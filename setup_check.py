#!/usr/bin/env python3
"""
Setup check script for SAT/ACT Notes Organizer.
This script verifies dependencies and configuration before running the app.
"""

import sys
import os
import importlib
import subprocess
from pathlib import Path

def check_python_version():
    """Check if Python version is compatible."""
    print("🐍 Checking Python version...")
    version = sys.version_info
    if version.major == 3 and version.minor >= 8:
        print(f"   ✅ Python {version.major}.{version.minor}.{version.micro} (compatible)")
        return True
    else:
        print(f"   ❌ Python {version.major}.{version.minor}.{version.micro} (requires Python 3.8+)")
        return False

def check_dependencies():
    """Check if required packages are installed."""
    print("\n📦 Checking dependencies...")

    required_packages = [
        'streamlit',
        'pytesseract',
        'PIL',  # Pillow
        'cv2',  # opencv-python
        'numpy',
        'requests'
    ]

    missing_packages = []

    for package in required_packages:
        try:
            importlib.import_module(package)
            print(f"   ✅ {package}")
        except ImportError:
            print(f"   ❌ {package} (missing)")
            missing_packages.append(package)

    return len(missing_packages) == 0, missing_packages

def check_tesseract():
    """Check if Tesseract OCR is installed."""
    print("\n🔍 Checking Tesseract OCR...")

    try:
        result = subprocess.run(['tesseract', '--version'],
                              capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            version_line = result.stdout.split('\n')[0]
            print(f"   ✅ {version_line}")
            return True
        else:
            print("   ❌ Tesseract not responding properly")
            return False
    except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError):
        print("   ❌ Tesseract not found")
        print("   📋 Install with: brew install tesseract (macOS) or apt-get install tesseract-ocr (Ubuntu)")
        return False

def check_config():
    """Check configuration and API keys."""
    print("\n⚙️ Checking configuration...")

    config_path = Path('config.json')
    env_vars = ['AI_API_KEY', 'AI_BASE_URL', 'AI_MODEL']

    config_ok = False

    # Check config.json
    if config_path.exists():
        try:
            import json
            with open(config_path) as f:
                config = json.load(f)

            providers = config.get('providers', [])
            if providers and providers[0].get('api_key') not in ['', 'your_openai_api_key_here']:
                print("   ✅ config.json exists with API key")
                config_ok = True
            else:
                print("   ⚠️ config.json exists but API key needs to be set")
        except Exception as e:
            print(f"   ❌ config.json exists but has errors: {e}")
    else:
        print("   ℹ️ config.json not found (will use environment variables)")

    # Check environment variables
    env_config = {}
    for var in env_vars:
        value = os.getenv(var)
        if value:
            env_config[var] = "✅ set"
        else:
            env_config[var] = "❌ missing"

    if any("✅" in status for status in env_config.values()):
        print("   ✅ Environment variables configured:")
        for var, status in env_config.items():
            print(f"      {var}: {status}")
        config_ok = True
    elif not config_ok:
        print("   ❌ No valid configuration found")
        print("   📋 Set environment variables or configure config.json")

    return config_ok

def check_directories():
    """Check if required directories exist."""
    print("\n📁 Checking directories...")

    required_dirs = ['data', 'data/temp', 'data/notes', 'ui', 'src', 'services']
    all_exist = True

    for dir_path in required_dirs:
        if os.path.exists(dir_path):
            print(f"   ✅ {dir_path}")
        else:
            print(f"   ❌ {dir_path} (missing)")
            all_exist = False

            # Try to create missing directories
            try:
                os.makedirs(dir_path, exist_ok=True)
                print(f"      ✅ Created {dir_path}")
                all_exist = True
            except Exception as e:
                print(f"      ❌ Failed to create {dir_path}: {e}")

    return all_exist

def main():
    """Main setup check function."""
    print("🚀 SAT/ACT Notes Organizer - Setup Check")
    print("=" * 50)

    checks = [
        ("Python Version", check_python_version()),
        ("Dependencies", check_dependencies()[0]),
        ("Tesseract OCR", check_tesseract()),
        ("Configuration", check_config()),
        ("Directories", check_directories())
    ]

    print("\n" + "=" * 50)
    print("📋 SUMMARY")
    print("=" * 50)

    all_passed = True
    for check_name, passed in checks:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{check_name:.<30} {status}")
        if not passed:
            all_passed = False

    print()

    if all_passed:
        print("🎉 All checks passed! Ready to run the application.")
        print("\n🚀 To start the app:")
        print("   python3 app_launcher.py")
        print("\n📱 For mobile access:")
        print("   python3 mobile_proxy.py")
        return 0
    else:
        print("⚠️ Some checks failed. Please fix the issues above before running.")
        print("\n🔧 Quick fixes:")

        # Check dependencies again to get missing packages
        deps_ok, missing = check_dependencies()
        if not deps_ok:
            print("   Install missing packages:")
            if 'PIL' in missing:
                missing[missing.index('PIL')] = 'Pillow'
            if 'cv2' in missing:
                missing[missing.index('cv2')] = 'opencv-python'
            print(f"   pip3 install {' '.join(missing)}")

        return 1

if __name__ == "__main__":
    sys.exit(main())
