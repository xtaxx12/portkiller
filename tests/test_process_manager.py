"""
Unit tests for the ProcessManagerService.
"""

import os
from unittest.mock import Mock, patch

import psutil

from app.services.process_manager import ProcessManagerService, process_manager


class TestProcessManagerService:
    """Tests for ProcessManagerService class."""

    def test_init_creates_empty_logs(self, process_manager):
        """Test that initialization creates empty action logs."""
        assert process_manager.action_logs == []

    def test_get_current_user_returns_username(self, process_manager):
        """Test getting the current username."""
        with patch("os.getlogin", return_value="testuser"):
            result = process_manager._get_current_user()
            assert result == "testuser"

    def test_get_current_user_fallback_to_env(self, process_manager):
        """Test fallback to environment variable when getlogin fails."""
        with patch("os.getlogin", side_effect=OSError("No terminal")):
            with patch.dict(os.environ, {"USERNAME": "envuser"}):
                result = process_manager._get_current_user()
                assert result == "envuser"


class TestCriticalProcessDetection:
    """Tests for critical process detection in ProcessManager."""

    def test_is_critical_process_detects_svchost(self, process_manager, mock_critical_process):
        """Test detection of svchost as critical."""
        result = process_manager._is_critical_process(mock_critical_process)
        assert result is True

    def test_is_critical_process_normal_process(self, process_manager, mock_process):
        """Test that normal processes are not critical."""
        result = process_manager._is_critical_process(mock_process)
        assert result is False

    def test_is_critical_process_handles_no_such_process(self, process_manager):
        """Test handling when process no longer exists."""
        process = Mock()
        process.name.side_effect = psutil.NoSuchProcess(1234)

        result = process_manager._is_critical_process(process)
        assert result is False

    def test_is_critical_process_handles_access_denied(self, process_manager):
        """Test handling when access to process is denied."""
        process = Mock()
        process.name.side_effect = psutil.AccessDenied(1234)

        result = process_manager._is_critical_process(process)
        assert result is False


class TestActionLogging:
    """Tests for action logging functionality."""

    def test_log_action_adds_to_list(self, process_manager):
        """Test that logging an action adds it to the list."""
        with patch.object(process_manager, "_get_current_user", return_value="testuser"):
            process_manager._log_action("TEST", 1234, "test.exe", 8080, "SUCCESS")

            assert len(process_manager.action_logs) == 1
            log = process_manager.action_logs[0]
            assert log.action == "TEST"
            assert log.target_pid == 1234
            assert log.target_process == "test.exe"
            assert log.target_port == 8080
            assert log.result == "SUCCESS"
            assert log.user == "testuser"

    def test_log_action_limits_to_1000_entries(self, process_manager):
        """Test that logs are limited to 1000 entries."""
        with patch.object(process_manager, "_get_current_user", return_value="testuser"):
            # Add 1005 entries
            for i in range(1005):
                process_manager._log_action("TEST", i, f"process_{i}", None, "SUCCESS")

            assert len(process_manager.action_logs) == 1000

    def test_log_action_logs_to_file(self, process_manager):
        """Test that actions are logged to file."""
        with patch.object(process_manager, "_get_current_user", return_value="testuser"):
            process_manager._log_action("KILL", 1234, "test.exe", 8080, "SUCCESS")

            process_manager.logger.info.assert_called()


class TestGetProcessInfo:
    """Tests for the get_process_info method."""

    def test_get_process_info_existing_process(self, process_manager):
        """Test getting info for an existing process."""
        with patch("psutil.Process") as mock_process_class:
            mock_process = Mock()
            mock_process.name.return_value = "test.exe"
            mock_process_class.return_value = mock_process

            exists, name, error = process_manager.get_process_info(1234)

            assert exists is True
            assert name == "test.exe"
            assert error is None

    def test_get_process_info_nonexistent_process(self, process_manager):
        """Test getting info for a non-existent process."""
        with patch("psutil.Process") as mock_process_class:
            mock_process_class.side_effect = psutil.NoSuchProcess(9999)

            exists, name, error = process_manager.get_process_info(9999)

            assert exists is False
            assert name is None
            assert "does not exist" in error

    def test_get_process_info_access_denied(self, process_manager):
        """Test getting info when access is denied."""
        with patch("psutil.Process") as mock_process_class:
            mock_process_class.side_effect = psutil.AccessDenied(1234)

            exists, name, error = process_manager.get_process_info(1234)

            assert exists is True
            assert name is None
            assert "Access denied" in error


class TestKillProcess:
    """Tests for the kill_process method."""

    def test_kill_process_success(self, process_manager):
        """Test successfully killing a process."""
        with patch("psutil.Process") as mock_process_class:
            mock_process = Mock()
            mock_process.name.return_value = "test.exe"
            mock_process.wait.return_value = None
            mock_process_class.return_value = mock_process

            with patch.object(process_manager, "_is_critical_process", return_value=False):
                with patch("os.getpid", return_value=9999):
                    result = process_manager.kill_process(1234, force=False)

                    assert result.success is True
                    assert "Successfully terminated" in result.message
                    assert result.pid == 1234
                    assert result.process_name == "test.exe"
                    mock_process.terminate.assert_called_once()

    def test_kill_process_force_uses_sigkill(self, process_manager):
        """Test that force=True uses SIGKILL."""
        with patch("psutil.Process") as mock_process_class:
            mock_process = Mock()
            mock_process.name.return_value = "test.exe"
            mock_process.wait.return_value = None
            mock_process_class.return_value = mock_process

            with patch.object(process_manager, "_is_critical_process", return_value=False):
                with patch("os.getpid", return_value=9999):
                    result = process_manager.kill_process(1234, force=True)

                    assert result.success is True
                    mock_process.kill.assert_called()

    def test_kill_process_blocks_critical_process(self, process_manager):
        """Test that critical processes cannot be killed."""
        with patch("psutil.Process") as mock_process_class:
            mock_process = Mock()
            mock_process.name.return_value = "svchost.exe"
            mock_process_class.return_value = mock_process

            with patch.object(process_manager, "_is_critical_process", return_value=True):
                result = process_manager.kill_process(100, force=False)

                assert result.success is False
                assert "critical system process" in result.message.lower()
                mock_process.terminate.assert_not_called()
                mock_process.kill.assert_not_called()

    def test_kill_process_blocks_self_termination(self, process_manager):
        """Test that the app cannot terminate itself."""
        current_pid = os.getpid()

        with patch("psutil.Process") as mock_process_class:
            mock_process = Mock()
            mock_process.name.return_value = "python.exe"
            mock_process_class.return_value = mock_process

            with patch.object(process_manager, "_is_critical_process", return_value=False):
                result = process_manager.kill_process(current_pid, force=False)

                assert result.success is False
                assert "PortKiller process itself" in result.message
                mock_process.terminate.assert_not_called()

    def test_kill_process_handles_no_such_process(self, process_manager):
        """Test handling when process doesn't exist."""
        with patch("psutil.Process") as mock_process_class:
            mock_process_class.side_effect = psutil.NoSuchProcess(9999)

            result = process_manager.kill_process(9999, force=False)

            assert result.success is False
            assert "no longer exists" in result.message

    def test_kill_process_handles_access_denied(self, process_manager):
        """Test handling when access to kill is denied."""
        with patch("psutil.Process") as mock_process_class:
            mock_process_class.side_effect = psutil.AccessDenied(1234)

            result = process_manager.kill_process(1234, force=False)

            assert result.success is False
            assert "Access denied" in result.message
            assert "administrator" in result.message.lower()

    def test_kill_process_timeout_then_force_kill(self, process_manager):
        """Test that timeout triggers force kill."""
        with patch("psutil.Process") as mock_process_class:
            mock_process = Mock()
            mock_process.name.return_value = "stubborn.exe"
            mock_process.wait.side_effect = [
                psutil.TimeoutExpired(3),  # First wait times out
                None,  # Second wait succeeds
            ]
            mock_process_class.return_value = mock_process

            with patch.object(process_manager, "_is_critical_process", return_value=False):
                with patch("os.getpid", return_value=9999):
                    result = process_manager.kill_process(1234, force=False)

                    assert result.success is True
                    # Should have called terminate first, then kill
                    mock_process.terminate.assert_called_once()
                    mock_process.kill.assert_called_once()

    def test_kill_process_timeout_even_with_force_kill(self, process_manager):
        """Test handling when process doesn't terminate even with force."""
        with patch("psutil.Process") as mock_process_class:
            mock_process = Mock()
            mock_process.name.return_value = "immortal.exe"
            mock_process.wait.side_effect = psutil.TimeoutExpired(3)
            mock_process_class.return_value = mock_process

            with patch.object(process_manager, "_is_critical_process", return_value=False):
                with patch("os.getpid", return_value=9999):
                    result = process_manager.kill_process(1234, force=False)

                    assert result.success is False
                    assert "did not terminate" in result.message

    def test_kill_process_handles_unexpected_exception(self, process_manager):
        """Test handling of unexpected exceptions."""
        with patch("psutil.Process") as mock_process_class:
            mock_process_class.side_effect = Exception("Unexpected error")

            result = process_manager.kill_process(1234, force=False)

            assert result.success is False
            assert "Unexpected error" in result.message

    def test_kill_process_logs_action(self, process_manager):
        """Test that kill actions are logged."""
        with patch("psutil.Process") as mock_process_class:
            mock_process = Mock()
            mock_process.name.return_value = "test.exe"
            mock_process.wait.return_value = None
            mock_process_class.return_value = mock_process

            with patch.object(process_manager, "_is_critical_process", return_value=False):
                with patch("os.getpid", return_value=9999):
                    process_manager.kill_process(1234, force=False, port=8080)

                    assert len(process_manager.action_logs) >= 1
                    log = process_manager.action_logs[-1]
                    assert log.target_pid == 1234
                    assert log.target_port == 8080


class TestGetActionLogs:
    """Tests for the get_action_logs method."""

    def test_get_action_logs_returns_recent_first(self, process_manager):
        """Test that logs are returned with most recent first."""
        with patch.object(process_manager, "_get_current_user", return_value="testuser"):
            for i in range(5):
                process_manager._log_action("TEST", i, f"process_{i}", None, "SUCCESS")

            logs = process_manager.get_action_logs(limit=5)

            # Most recent (i=4) should be first
            assert logs[0].target_pid == 4
            assert logs[-1].target_pid == 0

    def test_get_action_logs_respects_limit(self, process_manager):
        """Test that the limit parameter is respected."""
        with patch.object(process_manager, "_get_current_user", return_value="testuser"):
            for i in range(10):
                process_manager._log_action("TEST", i, f"process_{i}", None, "SUCCESS")

            logs = process_manager.get_action_logs(limit=3)

            assert len(logs) == 3

    def test_get_action_logs_empty(self, process_manager):
        """Test getting logs when there are none."""
        logs = process_manager.get_action_logs(limit=10)

        assert logs == []


class TestSingletonInstance:
    """Tests for the singleton instance."""

    def test_singleton_instance_exists(self):
        """Test that the singleton instance is created."""
        assert process_manager is not None
        assert isinstance(process_manager, ProcessManagerService)
