"""
PortKiller - Executable Builder Script

Creates a standalone Windows executable with:
1. Administrator privileges (UAC) automatically requested
2. Native desktop window (pywebview)
3. All dependencies bundled
"""

import subprocess
import sys
from pathlib import Path


def build():
    """Build the executable using PyInstaller."""
    root_dir = Path(__file__).parent
    main_script = root_dir / "main.py"
    static_dir = root_dir / "app" / "static"
    icon_path = root_dir / "app" / "static" / "favicon.ico"

    # PyInstaller command with UAC admin flag
    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--name=PortKiller",
        "--onefile",
        "--windowed",
        "--noconfirm",
        # Request admin privileges via UAC
        "--uac-admin",
        # Add static files
        f"--add-data={static_dir};app/static",
        # Uvicorn hidden imports
        "--hidden-import=uvicorn.logging",
        "--hidden-import=uvicorn.loops",
        "--hidden-import=uvicorn.loops.auto",
        "--hidden-import=uvicorn.protocols",
        "--hidden-import=uvicorn.protocols.http",
        "--hidden-import=uvicorn.protocols.http.auto",
        "--hidden-import=uvicorn.protocols.websockets",
        "--hidden-import=uvicorn.protocols.websockets.auto",
        "--hidden-import=uvicorn.lifespan",
        "--hidden-import=uvicorn.lifespan.on",
        "--hidden-import=uvicorn.lifespan.off",
        # Webview hidden imports
        "--hidden-import=webview",
        "--hidden-import=webview.platforms.edgechromium",
        "--hidden-import=clr_loader",
        "--hidden-import=pythonnet",
        # Collect all submodules
        "--collect-submodules=uvicorn",
        "--collect-submodules=fastapi",
        "--collect-submodules=starlette",
        "--collect-submodules=webview",
        "--collect-submodules=clr_loader",
    ]

    # Add icon if exists
    if icon_path.exists():
        cmd.append(f"--icon={icon_path}")

    # Add main script
    cmd.append(str(main_script))

    print("🔨 Building PortKiller Desktop App...")
    print(f"   Command: {' '.join(cmd)}")
    print()

    try:
        subprocess.run(cmd, check=True, cwd=root_dir)
        print()
        print("=" * 60)
        print("✅ BUILD SUCCESSFUL!")
        print("=" * 60)
        print(f"   Executable: {root_dir / 'dist' / 'PortKiller.exe'}")
        print()
        print("📝 Features:")
        print("   • Native desktop window (no browser needed)")
        print("   • Automatically requests Administrator privileges")
        print("   • Can terminate any process")
        print()
    except subprocess.CalledProcessError as e:
        print(f"❌ Build failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    build()
