"""
Process Manager Service - Handles process termination with safety checks.
"""
import psutil
import os
import logging
from typing import Optional, Tuple
from datetime import datetime
from ..models.port import ProcessKillResponse, ActionLog
from ..config import settings


class ProcessManagerService:
    """
    Service for managing processes with safety guards.
    Handles process termination with proper error handling and logging.
    """
    
    def __init__(self):
        self._setup_logging()
        self.action_logs: list[ActionLog] = []
    
    def _setup_logging(self):
        """Setup file logging for action audit trail."""
        os.makedirs(os.path.dirname(settings.LOG_FILE), exist_ok=True)
        
        self.logger = logging.getLogger("portkiller")
        self.logger.setLevel(logging.INFO)
        
        if not self.logger.handlers:
            handler = logging.FileHandler(settings.LOG_FILE)
            handler.setFormatter(
                logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            )
            self.logger.addHandler(handler)
    
    def _is_critical_process(self, process: psutil.Process) -> bool:
        """Check if the process is critical and shouldn't be terminated."""
        try:
            name = process.name().lower()
            return name in {p.lower() for p in settings.CRITICAL_PROCESSES}
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return False
    
    def _get_current_user(self) -> Optional[str]:
        """Get current username for logging."""
        try:
            return os.getlogin()
        except OSError:
            return os.environ.get("USERNAME") or os.environ.get("USER")
    
    def _log_action(
        self, 
        action: str, 
        pid: Optional[int], 
        process_name: Optional[str],
        port: Optional[int],
        result: str
    ):
        """Log an action to file and memory."""
        log_entry = ActionLog(
            timestamp=datetime.now(),
            action=action,
            target_pid=pid,
            target_process=process_name,
            target_port=port,
            result=result,
            user=self._get_current_user()
        )
        
        self.action_logs.append(log_entry)
        
        # Keep only last 1000 entries in memory
        if len(self.action_logs) > 1000:
            self.action_logs = self.action_logs[-1000:]
        
        # Log to file
        self.logger.info(
            f"Action: {action} | PID: {pid} | Process: {process_name} | "
            f"Port: {port} | Result: {result} | User: {log_entry.user}"
        )
    
    def get_process_info(self, pid: int) -> Tuple[bool, Optional[str], Optional[str]]:
        """
        Get process information by PID.
        
        Returns:
            Tuple of (exists, process_name, error_message)
        """
        try:
            process = psutil.Process(pid)
            return True, process.name(), None
        except psutil.NoSuchProcess:
            return False, None, f"Process with PID {pid} does not exist"
        except psutil.AccessDenied:
            return True, None, f"Access denied to process {pid}"
    
    def kill_process(
        self, 
        pid: int, 
        force: bool = False,
        port: Optional[int] = None
    ) -> ProcessKillResponse:
        """
        Attempt to terminate a process by PID.
        
        Args:
            pid: Process ID to terminate.
            force: If True, use SIGKILL instead of SIGTERM.
            port: Optional port number for logging purposes.
        
        Returns:
            ProcessKillResponse with the result.
        """
        try:
            process = psutil.Process(pid)
            process_name = process.name()
            
            # Safety check: prevent killing critical processes
            if self._is_critical_process(process):
                error_msg = f"Cannot terminate critical system process: {process_name} (PID: {pid})"
                self._log_action("KILL_BLOCKED", pid, process_name, port, "CRITICAL_PROCESS")
                return ProcessKillResponse(
                    success=False,
                    message=error_msg,
                    pid=pid,
                    process_name=process_name
                )
            
            # Safety check: prevent killing self
            if pid == os.getpid():
                error_msg = "Cannot terminate the PortKiller process itself"
                self._log_action("KILL_BLOCKED", pid, process_name, port, "SELF_TERMINATION")
                return ProcessKillResponse(
                    success=False,
                    message=error_msg,
                    pid=pid,
                    process_name=process_name
                )
            
            # Attempt to terminate
            if force:
                process.kill()  # SIGKILL
                action = "FORCE_KILL"
            else:
                process.terminate()  # SIGTERM
                action = "TERMINATE"
            
            # Wait briefly to confirm termination
            try:
                process.wait(timeout=3)
            except psutil.TimeoutExpired:
                # Process didn't terminate in time
                if not force:
                    # Try force kill
                    process.kill()
                    try:
                        process.wait(timeout=2)
                    except psutil.TimeoutExpired:
                        error_msg = f"Process {process_name} (PID: {pid}) did not terminate"
                        self._log_action(action, pid, process_name, port, "TIMEOUT")
                        return ProcessKillResponse(
                            success=False,
                            message=error_msg,
                            pid=pid,
                            process_name=process_name
                        )
            
            success_msg = f"Successfully terminated {process_name} (PID: {pid})"
            self._log_action(action, pid, process_name, port, "SUCCESS")
            return ProcessKillResponse(
                success=True,
                message=success_msg,
                pid=pid,
                process_name=process_name
            )
            
        except psutil.NoSuchProcess:
            error_msg = f"Process with PID {pid} no longer exists (may have already terminated)"
            self._log_action("KILL_ATTEMPTED", pid, None, port, "NOT_FOUND")
            return ProcessKillResponse(
                success=False,
                message=error_msg,
                pid=pid,
                process_name=None
            )
            
        except psutil.AccessDenied:
            error_msg = f"Access denied. Insufficient permissions to terminate process {pid}. Try running as administrator."
            self._log_action("KILL_ATTEMPTED", pid, None, port, "ACCESS_DENIED")
            return ProcessKillResponse(
                success=False,
                message=error_msg,
                pid=pid,
                process_name=None
            )
            
        except Exception as e:
            error_msg = f"Unexpected error terminating process {pid}: {str(e)}"
            self._log_action("KILL_ATTEMPTED", pid, None, port, f"ERROR: {str(e)}")
            return ProcessKillResponse(
                success=False,
                message=error_msg,
                pid=pid,
                process_name=None
            )
    
    def get_action_logs(self, limit: int = 100) -> list[ActionLog]:
        """Get recent action logs."""
        return self.action_logs[-limit:][::-1]  # Most recent first


# Singleton instance
process_manager = ProcessManagerService()
