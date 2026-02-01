# 🔌 PortKiller

<div align="center">

**Professional Port Management & Process Control Tool**

*Visualize open ports, identify processes, and manage network connections with a beautiful native desktop application.*

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

</div>

---

## 🎯 Features

- **🖥️ Native Desktop App** - Standalone Windows executable with native window
- **🔐 Administrator Privileges** - Automatically requests UAC elevation to terminate any process
- **📊 Real-time Dashboard** - View TCP/UDP statistics at a glance
- **🔍 Advanced Filtering** - Filter by port, protocol, state, or process
- **⚡ Process Termination** - Safely terminate processes with confirmation
- **🛡️ Safety Guards** - Critical system processes are protected
- **📝 Action Logging** - All actions are logged for audit trails
- **🔄 Auto-refresh** - Automatic updates every 5 seconds
- **🌙 Modern Dark UI** - Beautiful glassmorphism design

---

## 💻 Desktop Executable (Windows)

### Download & Run

The easiest way to use PortKiller is the standalone executable:

1. **Download** `PortKiller.exe` from the `dist/` folder
2. **Double-click** to run
3. **Accept the UAC prompt** (required for process termination)
4. The app opens in a **native desktop window**

### Features of the Desktop App

| Feature | Description |
|---------|-------------|
| 🔐 **UAC Admin** | Automatically requests administrator privileges |
| 🖥️ **Native Window** | Runs in a native desktop window (not browser) |
| 📦 **Standalone** | No Python installation required |
| ⚡ **Kill Any Process** | Can terminate any process (including system services) |

### Build from Source

To build the executable yourself:

```bash
# Install dependencies
pip install -r requirements.txt

# Build the executable
python build_exe.py
```

The executable will be created at `dist/PortKiller.exe`

---

## 🚀 Quick Start (Development Mode)

### Prerequisites

- Python 3.8 or higher
- Windows / Linux / macOS

### Installation

1. **Clone or navigate to the project directory:**
   ```bash
   cd portkiller
   ```

2. **Create a virtual environment (recommended):**
   ```bash
   python -m venv venv
   
   # Windows
   .\venv\Scripts\activate
   
   # Linux/macOS
   source venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application:**
   ```bash
   python main.py
   ```

5. **Open your browser:**
   Navigate to [http://127.0.0.1:8787](http://127.0.0.1:8787)

---

## 🏗️ Architecture

```
portkiller/
├── app/
│   ├── __init__.py
│   ├── config.py              # Configuration settings
│   ├── models/
│   │   ├── __init__.py
│   │   └── port.py            # Pydantic data models
│   ├── services/
│   │   ├── __init__.py
│   │   ├── port_scanner.py    # Port scanning service
│   │   └── process_manager.py # Process management service
│   ├── routes/
│   │   ├── __init__.py
│   │   └── ports.py           # API endpoints
│   └── static/
│       ├── index.html         # Main HTML page
│       ├── css/
│       │   └── styles.css     # Styles (dark theme)
│       └── js/
│           └── app.js         # Frontend logic
├── dist/                       # Built executable output
│   └── PortKiller.exe         # Windows executable
├── logs/                       # Action logs directory
├── main.py                     # Application entry point
├── build_exe.py                # PyInstaller build script
├── portkiller.manifest         # Windows UAC manifest
├── requirements.txt            # Python dependencies
└── README.md                   # This file
```

---

## 📡 API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/ports` | List all open ports |
| `GET` | `/api/stats` | Get system statistics |
| `POST` | `/api/kill/{pid}` | Terminate a process |
| `GET` | `/api/logs` | Get action logs |
| `GET` | `/api/process/{pid}` | Get process details |
| `GET` | `/health` | Health check endpoint |
| `GET` | `/docs` | Swagger API documentation |

### Query Parameters

**GET /api/ports**
- `port` - Filter by specific port number
- `protocol` - Filter by TCP or UDP
- `process` - Filter by process name (partial match)
- `state` - Filter by connection state

### Rate Limiting

All API endpoints are protected by rate limiting to prevent abuse:

| Endpoint | Limit | Description |
|----------|-------|-------------|
| `GET /api/ports` | 60/min | Port listing |
| `GET /api/stats` | 60/min | Statistics |
| `GET /api/logs` | 30/min | Action logs |
| `GET /api/process/{pid}` | 60/min | Process details |
| `POST /api/kill/{pid}` | **10/min** | Process termination (strict) |
| `GET /health` | 120/min | Health check |

When rate limit is exceeded, the API returns:
```json
{
  "success": false,
  "error": "rate_limit_exceeded",
  "message": "Too many requests. Please try again in 60 seconds.",
  "retry_after": 60
}
```

---

## 🔐 Security Features

### Protected Processes

The following critical system processes cannot be terminated:
- Windows: `System`, `csrss.exe`, `lsass.exe`, `svchost.exe`, `explorer.exe`, etc.
- Linux: `init`, `systemd`, `kthreadd`, etc.
- macOS: `launchd`, `kernel_task`, `WindowServer`

### Protected Ports

Critical ports (22, 53, 135, 445, etc.) are flagged with warnings.

### Logging

All termination attempts are logged to `logs/portkiller.log` with:
- Timestamp
- Action type
- Target process and PID
- Result
- User who performed the action

---

## ⚙️ Configuration

Environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `PORTKILLER_HOST` | `127.0.0.1` | Server host address |
| `PORTKILLER_PORT` | `8787` | Server port |
| `PORTKILLER_DEBUG` | `false` | Enable debug mode |

---

## 🎨 UI Features

### Theme Toggle

Switch between **Dark** and **Light** themes:
- Click the sun/moon icon in the header
- Use `Ctrl+Shift+T` keyboard shortcut
- Theme preference is saved in localStorage

### Export Data

Export ports and logs data from the header dropdown:
- **Ports (JSON/CSV)** - Export all current port connections
- **Logs (JSON/CSV)** - Export action history

Or use the API directly:
```bash
# Export ports as CSV
curl http://localhost:8787/api/export/ports?format=csv

# Export logs as JSON
curl http://localhost:8787/api/export/logs?format=json
```

### Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `/` | Focus search input |
| `Ctrl+R` | Refresh data |
| `Ctrl+Shift+T` | Toggle theme |
| `Esc` | Close modals/drawers |

### Filter Chips

- **All** - Show all connections
- **TCP** - Show only TCP ports
- **UDP** - Show only UDP ports
- **LISTEN** - Show listening ports
- **ESTABLISHED** - Show established connections
- **⚠️ Critical** - Show critical processes

---

## � Monitoring & Metrics

### Prometheus Metrics

PortKiller exposes Prometheus metrics at `/metrics`:

```bash
curl http://localhost:8787/metrics
```

Available metrics include:
- Request count and latency
- Active requests in progress
- HTTP status code distribution

---

## 🔧 Development

### Running in development mode:

```bash
PORTKILLER_DEBUG=true python main.py
```

### Running with custom port:

```bash
PORTKILLER_PORT=9000 python main.py
```

### Building the executable:

```bash
python build_exe.py
```

---

## 📄 License

MIT License - feel free to use in your projects.

---

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

---
