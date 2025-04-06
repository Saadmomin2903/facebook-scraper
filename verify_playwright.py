#!/usr/bin/env python3
"""
Verification script for Playwright installation in Vercel environment.
This script checks if Playwright and its browsers are correctly installed.
"""

import os
import sys
import subprocess
import glob

def run_command(command):
    """Run a shell command and return its output."""
    try:
        result = subprocess.run(
            command, 
            shell=True, 
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            universal_newlines=True
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        return f"Error: {e.stderr}"

def check_installation():
    """Check Playwright installation and related components."""
    print("\n--- System Information ---")
    print(f"Python version: {sys.version}")
    print(f"Platform: {sys.platform}")
    print(f"Current directory: {os.getcwd()}")
    
    print("\n--- Environment Variables ---")
    for key in ['VERCEL', 'HOME', 'PATH', 'PYTHONPATH']:
        print(f"{key}: {os.environ.get(key, 'Not set')}")
    
    try:
        print("\n--- Playwright Installation ---")
        import playwright
        print(f"Playwright installed: {playwright.__file__}")
        print(f"Playwright version: {playwright.__version__}")
        
        from playwright.sync_api import sync_playwright
        
        try:
            print("\n--- Checking Browser Binary Paths ---")
            with sync_playwright() as p:
                executable_path = p.chromium._impl_obj._channel.executable
                print(f"Chromium executable path: {executable_path}")
                print(f"Exists: {os.path.exists(executable_path)}")
        except Exception as e:
            print(f"Failed to get browser executable path: {e}")
    
        print("\n--- Browser Paths ---")
        # Common paths for Playwright browsers
        home = os.environ.get('HOME', '')
        cache_paths = [
            f"{home}/.cache/ms-playwright",
            "/home/sbx_user1051/.cache/ms-playwright",
            "/tmp/.playwright"
        ]
        
        for path in cache_paths:
            print(f"Checking path: {path}")
            if os.path.exists(path):
                print(f"  Directory exists: {path}")
                print(f"  Contents: {os.listdir(path)}")
                
                # Check for chromium installation
                chromium_paths = glob.glob(f"{path}/chromium-*/chrome-linux/chrome")
                if chromium_paths:
                    for chromium_path in chromium_paths:
                        print(f"  Chromium binary found: {chromium_path}")
                        print(f"  Executable: {os.access(chromium_path, os.X_OK)}")
                else:
                    print(f"  No chromium binary found in {path}")
            else:
                print(f"  Directory does not exist: {path}")
    
    except ImportError:
        print("Playwright is not installed")
    
    print("\n--- Dependencies ---")
    print(run_command("pip list"))
    
    print("\n--- File System ---")
    print(run_command("ls -la /tmp"))
    print(run_command("ls -la ~/.cache || echo 'No cache directory'"))
    
    print("\n--- Verification Complete ---")

if __name__ == "__main__":
    check_installation() 