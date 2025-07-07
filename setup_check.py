#!/usr/bin/env python3
"""
Setup Verification Script for Litematic Converter
Run this script to verify that all dependencies are installed correctly.
"""

import sys
import importlib

def check_python_version():
    """Check if Python version is compatible."""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 7):
        print("❌ Python 3.7 or newer is required!")
        print(f"   Current version: {sys.version}")
        return False
    else:
        print(f"✅ Python version: {sys.version}")
        return True

def check_dependency(name, import_name=None):
    """Check if a dependency is available."""
    if import_name is None:
        import_name = name
    
    try:
        module = importlib.import_module(import_name)
        if hasattr(module, '__version__'):
            version = module.__version__
        else:
            version = "unknown"
        print(f"✅ {name}: {version}")
        return True
    except ImportError:
        print(f"❌ {name}: Not installed")
        return False

def main():
    """Run all checks."""
    print("🔍 Checking Litematic Converter Setup...\n")
    
    all_ok = True
    
    # Check Python version
    all_ok &= check_python_version()
    print()
    
    # Check required dependencies
    dependencies = [
        ("litemapy", "litemapy"),
        ("nbtlib", "nbtlib"), 
        ("Pillow", "PIL"),
        ("tkinter", "tkinter")
    ]
    
    print("📦 Checking Dependencies:")
    for name, import_name in dependencies:
        all_ok &= check_dependency(name, import_name)
    
    print()
    
    if all_ok:
        print("🎉 All checks passed! You're ready to use the Litematic Converter.")
        print("\nTo start the GUI, run:")
        print("   python litematic_converter_gui.py")
    else:
        print("❗ Some dependencies are missing.")
        print("\nTo install missing dependencies, run:")
        print("   pip install -r requirements.txt")
        
    return 0 if all_ok else 1

if __name__ == "__main__":
    sys.exit(main()) 