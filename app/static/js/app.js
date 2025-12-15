/**
 * PortKiller - Main Application JavaScript
 * Handles API communication, UI updates, and user interactions
 */

// ===== Application State =====
const state = {
    ports: [],
    filteredPorts: [],
    stats: null,
    logs: [],
    sortColumn: 'port',
    sortDirection: 'asc',
    activeFilter: 'all',
    searchQuery: '',
    autoRefresh: true,
    refreshInterval: null,
    selectedProcess: null
};

// ===== API Service =====
const API = {
    baseUrl: '',

    async getPorts() {
        try {
            const response = await fetch(`${this.baseUrl}/api/ports`);
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            return await response.json();
        } catch (error) {
            console.error('Failed to fetch ports:', error);
            throw error;
        }
    },

    async getStats() {
        try {
            const response = await fetch(`${this.baseUrl}/api/stats`);
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            return await response.json();
        } catch (error) {
            console.error('Failed to fetch stats:', error);
            throw error;
        }
    },

    async killProcess(pid, force = false, port = null) {
        try {
            const params = new URLSearchParams({ force: force.toString() });
            if (port) params.append('port', port.toString());

            const response = await fetch(`${this.baseUrl}/api/kill/${pid}?${params}`, {
                method: 'POST'
            });
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            return await response.json();
        } catch (error) {
            console.error('Failed to kill process:', error);
            throw error;
        }
    },

    async getLogs(limit = 50) {
        try {
            const response = await fetch(`${this.baseUrl}/api/logs?limit=${limit}`);
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            return await response.json();
        } catch (error) {
            console.error('Failed to fetch logs:', error);
            throw error;
        }
    }
};

// ===== DOM Elements =====
const DOM = {
    // Stats
    tcpCount: document.getElementById('tcpCount'),
    udpCount: document.getElementById('udpCount'),
    listenCount: document.getElementById('listenCount'),
    establishedCount: document.getElementById('establishedCount'),
    processCount: document.getElementById('processCount'),

    // Table
    portsTableBody: document.getElementById('portsTableBody'),
    resultsCount: document.getElementById('resultsCount'),

    // Controls
    searchInput: document.getElementById('searchInput'),
    clearSearch: document.getElementById('clearSearch'),
    refreshBtn: document.getElementById('refreshBtn'),
    autoRefreshToggle: document.getElementById('autoRefresh'),
    updateTime: document.getElementById('updateTime'),

    // Modal
    confirmModal: document.getElementById('confirmModal'),
    modalProcessName: document.getElementById('modalProcessName'),
    modalPid: document.getElementById('modalPid'),
    modalPort: document.getElementById('modalPort'),
    forceKill: document.getElementById('forceKill'),
    cancelKill: document.getElementById('cancelKill'),
    confirmKill: document.getElementById('confirmKill'),

    // Logs
    logsToggle: document.getElementById('logsToggle'),
    logsDrawer: document.getElementById('logsDrawer'),
    closeDrawer: document.getElementById('closeDrawer'),
    logsContent: document.getElementById('logsContent'),
    logsBadge: document.getElementById('logsBadge'),

    // Toast
    toastContainer: document.getElementById('toastContainer')
};

// ===== UI Functions =====
const UI = {
    updateStats(stats) {
        if (!stats) return;

        DOM.tcpCount.textContent = stats.total_tcp_ports;
        DOM.udpCount.textContent = stats.total_udp_ports;
        DOM.listenCount.textContent = stats.listening_ports;
        DOM.establishedCount.textContent = stats.established_connections;
        DOM.processCount.textContent = stats.unique_processes;

        // Animate numbers
        document.querySelectorAll('.stat-value').forEach(el => {
            el.classList.add('updated');
            setTimeout(() => el.classList.remove('updated'), 300);
        });
    },

    updateTable(ports) {
        if (!ports.length) {
            DOM.portsTableBody.innerHTML = `
                <tr class="empty-row">
                    <td colspan="8">
                        <div style="padding: 2rem;">
                            <div style="font-size: 2rem; margin-bottom: 0.5rem;">🔍</div>
                            <div>No ports found matching your criteria</div>
                        </div>
                    </td>
                </tr>
            `;
            DOM.resultsCount.textContent = '0 results';
            return;
        }

        const html = ports.map(port => this.createTableRow(port)).join('');
        DOM.portsTableBody.innerHTML = html;
        DOM.resultsCount.textContent = `${ports.length} result${ports.length !== 1 ? 's' : ''}`;

        // Add event listeners to kill buttons
        document.querySelectorAll('.btn-kill').forEach(btn => {
            btn.addEventListener('click', () => {
                const pid = parseInt(btn.dataset.pid);
                const process = btn.dataset.process;
                const port = parseInt(btn.dataset.port);
                this.showKillModal(pid, process, port);
            });
        });
    },

    createTableRow(port) {
        const stateClass = port.state.toLowerCase().replace('_', '-');
        const isCritical = port.is_critical;

        return `
            <tr class="${isCritical ? 'row-critical' : ''}">
                <td><span class="port-number">${port.port}</span></td>
                <td><span class="protocol-badge ${port.protocol.toLowerCase()}">${port.protocol}</span></td>
                <td><span class="state-badge ${stateClass}">${port.state}</span></td>
                <td class="address-cell" title="${port.local_address}">${port.local_address}</td>
                <td class="address-cell" title="${port.remote_address || '-'}">${port.remote_address || '-'}</td>
                <td>${port.pid || '-'}</td>
                <td>
                    <span class="process-name">
                        ${isCritical ? '<span class="critical-icon" title="Critical Process">⚠️</span>' : ''}
                        ${port.process_name || '-'}
                    </span>
                </td>
                <td>
                    <button 
                        class="btn btn-kill" 
                        data-pid="${port.pid}"
                        data-process="${port.process_name || 'Unknown'}"
                        data-port="${port.port}"
                        ${!port.pid || isCritical ? 'disabled' : ''}
                        title="${isCritical ? 'Cannot terminate critical process' : 'Terminate process'}"
                    >
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <line x1="18" y1="6" x2="6" y2="18"/>
                            <line x1="6" y1="6" x2="18" y2="18"/>
                        </svg>
                    </button>
                </td>
            </tr>
        `;
    },

    showKillModal(pid, process, port) {
        state.selectedProcess = { pid, process, port };

        DOM.modalProcessName.textContent = process;
        DOM.modalPid.textContent = pid;
        DOM.modalPort.textContent = port;
        DOM.forceKill.checked = false;

        DOM.confirmModal.classList.add('show');
    },

    hideKillModal() {
        DOM.confirmModal.classList.remove('show');
        state.selectedProcess = null;
    },

    updateLastRefresh() {
        const now = new Date();
        const timeStr = now.toLocaleTimeString();
        DOM.updateTime.textContent = timeStr;
    },

    toggleLogsDrawer(show) {
        if (show) {
            DOM.logsDrawer.classList.add('open');
            this.loadLogs();
        } else {
            DOM.logsDrawer.classList.remove('open');
        }
    },

    async loadLogs() {
        try {
            state.logs = await API.getLogs(50);
            this.updateLogsContent();
        } catch (error) {
            DOM.logsContent.innerHTML = '<p class="no-logs">Failed to load logs</p>';
        }
    },

    updateLogsContent() {
        if (!state.logs.length) {
            DOM.logsContent.innerHTML = '<p class="no-logs">No actions logged yet</p>';
            DOM.logsBadge.textContent = '0';
            return;
        }

        DOM.logsBadge.textContent = state.logs.length > 99 ? '99+' : state.logs.length;

        const html = state.logs.map(log => {
            const isSuccess = log.result === 'SUCCESS';
            const isBlocked = log.result === 'CRITICAL_PROCESS' || log.result === 'SELF_TERMINATION';
            const statusClass = isSuccess ? 'success' : (isBlocked ? 'blocked' : 'error');

            const timestamp = new Date(log.timestamp).toLocaleString();

            return `
                <div class="log-entry ${statusClass}">
                    <div class="log-timestamp">${timestamp}</div>
                    <div class="log-action">${log.action}</div>
                    <div class="log-details">
                        ${log.target_process ? `Process: ${log.target_process}` : ''}
                        ${log.target_pid ? ` (PID: ${log.target_pid})` : ''}
                        ${log.target_port ? ` • Port: ${log.target_port}` : ''}
                        <br>Result: ${log.result}
                    </div>
                </div>
            `;
        }).join('');

        DOM.logsContent.innerHTML = html;
    },

    showToast(type, title, message) {
        const icons = {
            success: '✅',
            error: '❌',
            warning: '⚠️',
            info: 'ℹ️'
        };

        const toast = document.createElement('div');
        toast.className = `toast ${type}`;
        toast.innerHTML = `
            <span class="toast-icon">${icons[type]}</span>
            <div class="toast-content">
                <div class="toast-title">${title}</div>
                ${message ? `<div class="toast-message">${message}</div>` : ''}
            </div>
        `;

        DOM.toastContainer.appendChild(toast);

        // Auto-remove after 5 seconds
        setTimeout(() => {
            toast.style.opacity = '0';
            toast.style.transform = 'translateY(20px)';
            setTimeout(() => toast.remove(), 300);
        }, 5000);
    },

    showLoading() {
        DOM.portsTableBody.innerHTML = `
            <tr class="loading-row">
                <td colspan="8">
                    <div class="loading-spinner"></div>
                    <span>Loading ports...</span>
                </td>
            </tr>
        `;
    }
};

// ===== Data Functions =====
const Data = {
    filterPorts(ports) {
        let filtered = [...ports];

        // Apply active filter
        switch (state.activeFilter) {
            case 'tcp':
                filtered = filtered.filter(p => p.protocol === 'TCP');
                break;
            case 'udp':
                filtered = filtered.filter(p => p.protocol === 'UDP');
                break;
            case 'listen':
                filtered = filtered.filter(p => p.state === 'LISTEN');
                break;
            case 'established':
                filtered = filtered.filter(p => p.state === 'ESTABLISHED');
                break;
            case 'critical':
                filtered = filtered.filter(p => p.is_critical);
                break;
        }

        // Apply search query
        if (state.searchQuery) {
            const query = state.searchQuery.toLowerCase();
            filtered = filtered.filter(p =>
                p.port.toString().includes(query) ||
                p.protocol.toLowerCase().includes(query) ||
                p.state.toLowerCase().includes(query) ||
                (p.process_name && p.process_name.toLowerCase().includes(query)) ||
                (p.local_address && p.local_address.toLowerCase().includes(query)) ||
                (p.pid && p.pid.toString().includes(query))
            );
        }

        return filtered;
    },

    sortPorts(ports) {
        return [...ports].sort((a, b) => {
            let aVal = a[state.sortColumn];
            let bVal = b[state.sortColumn];

            // Handle null values
            if (aVal === null || aVal === undefined) aVal = '';
            if (bVal === null || bVal === undefined) bVal = '';

            // Compare
            if (typeof aVal === 'number' && typeof bVal === 'number') {
                return state.sortDirection === 'asc' ? aVal - bVal : bVal - aVal;
            }

            aVal = String(aVal).toLowerCase();
            bVal = String(bVal).toLowerCase();

            if (state.sortDirection === 'asc') {
                return aVal.localeCompare(bVal);
            } else {
                return bVal.localeCompare(aVal);
            }
        });
    },

    processAndDisplay(ports) {
        state.ports = ports;
        let processed = this.filterPorts(ports);
        processed = this.sortPorts(processed);
        state.filteredPorts = processed;
        UI.updateTable(processed);
    }
};

// ===== Main Functions =====
async function refreshData() {
    try {
        const [ports, stats] = await Promise.all([
            API.getPorts(),
            API.getStats()
        ]);

        state.stats = stats;
        UI.updateStats(stats);
        Data.processAndDisplay(ports);
        UI.updateLastRefresh();

    } catch (error) {
        UI.showToast('error', 'Refresh Failed', 'Could not fetch port data. Make sure the server is running.');
    }
}

async function killProcess() {
    if (!state.selectedProcess) return;

    const { pid, process, port } = state.selectedProcess;
    const force = DOM.forceKill.checked;

    UI.hideKillModal();

    try {
        const result = await API.killProcess(pid, force, port);

        if (result.success) {
            UI.showToast('success', 'Process Terminated', result.message);
        } else {
            UI.showToast('error', 'Termination Failed', result.message);
        }

        // Refresh data after kill attempt
        setTimeout(refreshData, 500);

        // Update logs if drawer is open
        if (DOM.logsDrawer.classList.contains('open')) {
            UI.loadLogs();
        }

    } catch (error) {
        UI.showToast('error', 'Error', 'Failed to terminate process. Check permissions.');
    }
}

function startAutoRefresh() {
    if (state.refreshInterval) clearInterval(state.refreshInterval);
    state.refreshInterval = setInterval(refreshData, 5000);
}

function stopAutoRefresh() {
    if (state.refreshInterval) {
        clearInterval(state.refreshInterval);
        state.refreshInterval = null;
    }
}

// ===== Event Listeners =====
function initEventListeners() {
    // Refresh button
    DOM.refreshBtn.addEventListener('click', () => {
        DOM.refreshBtn.classList.add('spinning');
        refreshData().finally(() => {
            setTimeout(() => DOM.refreshBtn.classList.remove('spinning'), 500);
        });
    });

    // Auto-refresh toggle
    DOM.autoRefreshToggle.addEventListener('change', (e) => {
        state.autoRefresh = e.target.checked;
        if (state.autoRefresh) {
            startAutoRefresh();
        } else {
            stopAutoRefresh();
        }
    });

    // Search input
    DOM.searchInput.addEventListener('input', (e) => {
        state.searchQuery = e.target.value;
        Data.processAndDisplay(state.ports);
    });

    // Clear search
    DOM.clearSearch.addEventListener('click', () => {
        DOM.searchInput.value = '';
        state.searchQuery = '';
        Data.processAndDisplay(state.ports);
    });

    // Filter chips
    document.querySelectorAll('.filter-chip').forEach(chip => {
        chip.addEventListener('click', () => {
            document.querySelectorAll('.filter-chip').forEach(c => c.classList.remove('active'));
            chip.classList.add('active');
            state.activeFilter = chip.dataset.filter;
            Data.processAndDisplay(state.ports);
        });
    });

    // Table sorting
    document.querySelectorAll('.sortable').forEach(th => {
        th.addEventListener('click', () => {
            const column = th.dataset.sort;

            if (state.sortColumn === column) {
                state.sortDirection = state.sortDirection === 'asc' ? 'desc' : 'asc';
            } else {
                state.sortColumn = column;
                state.sortDirection = 'asc';
            }

            // Update UI
            document.querySelectorAll('.sortable').forEach(t => {
                t.classList.remove('asc', 'desc');
            });
            th.classList.add(state.sortDirection);

            Data.processAndDisplay(state.ports);
        });
    });

    // Modal controls
    DOM.cancelKill.addEventListener('click', UI.hideKillModal);
    DOM.confirmKill.addEventListener('click', killProcess);
    DOM.confirmModal.addEventListener('click', (e) => {
        if (e.target === DOM.confirmModal) UI.hideKillModal();
    });

    // Logs drawer
    DOM.logsToggle.addEventListener('click', () => {
        UI.toggleLogsDrawer(true);
    });
    DOM.closeDrawer.addEventListener('click', () => {
        UI.toggleLogsDrawer(false);
    });

    // Keyboard shortcuts
    document.addEventListener('keydown', (e) => {
        // Escape to close modals/drawers
        if (e.key === 'Escape') {
            UI.hideKillModal();
            UI.toggleLogsDrawer(false);
        }

        // Ctrl+R or Cmd+R to refresh (prevent default and use custom refresh)
        if ((e.ctrlKey || e.metaKey) && e.key === 'r') {
            e.preventDefault();
            refreshData();
        }

        // Focus search with /
        if (e.key === '/' && document.activeElement !== DOM.searchInput) {
            e.preventDefault();
            DOM.searchInput.focus();
        }
    });
}

// ===== Initialization =====
document.addEventListener('DOMContentLoaded', () => {
    console.log('🔌 PortKiller initialized');

    // Initialize event listeners
    initEventListeners();

    // Show loading state
    UI.showLoading();

    // Initial data load
    refreshData();

    // Start auto-refresh
    if (state.autoRefresh) {
        startAutoRefresh();
    }
});

// Clean up on page unload
window.addEventListener('beforeunload', () => {
    stopAutoRefresh();
});
