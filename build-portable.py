import os
import subprocess
import shutil
import sys
import platform

def build_portable():
    # Check for Mac flag
    target_mac = "--mac" in sys.argv
    
    # Platform detection
    host_os = platform.system()
    print(f"[-] Running on {host_os}...")

    if target_mac:
        print("[-] Target: macOS")
        if host_os == "Windows":
            print("[!] WARNING: PyInstaller cannot cross-compile from Windows to macOS.")
            print("    Please run this script on a Mac to generate a valid macOS binary.")
    
    # 1. Clean previous
    for folder in ["dist", "build"]:
        if os.path.exists(folder): shutil.rmtree(folder)
    
    # 2. Determine separator for path (Host OS dependent)
    sep = ';' if os.name == 'nt' else ':'
    
    # 3. Determine Output Name
    output_name = "pybash_portable_mac" if target_mac else "pybash_portable"

    # 4. Build command
    cmd = [
        "pyinstaller",
        "--onefile",
        f"--name={output_name}",
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
        
        # Determine extension for report
        ext = ""
        if os.name == 'nt' and not target_mac:
            ext = ".exe"
        
        print(f"\n[+] Portable build complete!")
        print(f"[+] File: {os.path.abspath(f'dist/{output_name}{ext}')}")
        
        if target_mac and host_os != "Windows":
            print("[+] Note: You may need to run 'chmod +x' on the generated binary.")

    except Exception as e:
        print(f"[!] Build failed: {e}")

if __name__ == "__main__":
    build_portable()
