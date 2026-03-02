import os
import subprocess
import shutil
import sys
import platform

def build_portable():
    print(f"[-] Building Portable PyBash for {platform.system()}...")
    
    # 1. Clean previous
    for folder in ["dist", "build"]:
        if os.path.exists(folder): shutil.rmtree(folder)
    
    # 2. Determine separator for path
    sep = ';' if os.name == 'nt' else ':'
    
    # 3. Build command
    # We include 'core' and 'plugins' as data folders so they are inside the EXE
    cmd = [
        "pyinstaller",
        "--onefile",
        "--name=pybash_portable",
        "--add-data", f"core{sep}core",
        "--add-data", f"plugins{sep}plugins",
        "--clean",
        "--hidden-import=prompt_toolkit.key_binding.bindings.basic",
        "--hidden-import=prompt_toolkit.key_binding.bindings.emacs",
        "--hidden-import=pygments.lexers.shell",
        "pybash.py"
    ]

    try:
        subprocess.check_call(cmd)
        ext = ".exe" if os.name == 'nt' else ""
        print(f"[+] Portable build complete!")
        print(f"[+] File: {os.path.abspath('dist/pybash_portable' + ext)}")
    except Exception as e:
        print(f"[!] Build failed: {e}")

if __name__ == "__main__":
    build_portable()
