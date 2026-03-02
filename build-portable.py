import os
import subprocess
import shutil
import sys
import platform

def build_portable():
    # Check for Mac flag
    target_mac = "--mac" in sys.argv
    host_os = platform.system()
    
    print(f"[-] Host OS: {host_os}")

    if target_mac:
        if host_os == "Windows":
            print("\n[!] CRITICAL ERROR: Cannot build macOS binary on Windows.")
            print("    PyInstaller does not support cross-compilation.")
            print("    -> Please copy this project to a Mac and run 'python build-portable.py --mac' there.")
            return # Stop execution
        print("[-] Target: macOS")
    
    # 1. Clean previous
    for folder in ["dist", "build"]:
        if os.path.exists(folder): shutil.rmtree(folder)
    
    # 2. Determine separator for path
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
        if os.name == 'nt':
            ext = ".exe"
        
        final_path = os.path.abspath(f'dist/{output_name}{ext}')
        
        print(f"\n[+] Portable build complete!")
        print(f"[+] File: {final_path}")
        
        if host_os != "Windows":
            print("[*] Tip: You may need to run 'chmod +x' on the generated file.")

    except Exception as e:
        print(f"[!] Build failed: {e}")

if __name__ == "__main__":
    build_portable()
