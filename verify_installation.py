#!/usr/bin/env python3
"""
Installation Verification Script for Multi-Agent SDLC System

This script verifies that all dependencies are properly installed
and the system is ready to run.

Usage:
    python verify_installation.py
"""

import sys
import os
import importlib
from typing import Tuple, List
from pathlib import Path


class Colors:
    """ANSI color codes for terminal output."""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


def check_python_version() -> Tuple[bool, str]:
    """Check if Python version is 3.10+."""
    version_info = sys.version_info
    version_str = f"{version_info.major}.{version_info.minor}.{version_info.micro}"
    
    if version_info >= (3, 10):
        return True, version_str
    else:
        return False, version_str


def check_package(package_name: str, import_name: str = None) -> Tuple[bool, str]:
    """Check if a package is installed."""
    if import_name is None:
        import_name = package_name.replace("-", "_")
    
    try:
        module = importlib.import_module(import_name)
        # Try to get version
        version = "unknown"
        for attr in ['__version__', 'VERSION', 'version']:
            if hasattr(module, attr):
                version = getattr(module, attr)
                break
        return True, str(version)
    except ImportError:
        return False, "not installed"


def check_file(filepath: str) -> bool:
    """Check if a file exists."""
    return Path(filepath).exists()


def check_env_file() -> Tuple[bool, str]:
    """Check if .env file exists and has API keys."""
    if not Path('.env').exists():
        return False, "File not found"
    
    try:
        with open('.env', 'r') as f:
            content = f.read()
            
        has_openai = 'OPENAI_API_KEY' in content and not 'OPENAI_API_KEY=' in content or 'sk-' in content
        has_anthropic = 'ANTHROPIC_API_KEY' in content and 'sk-ant-' in content
        has_gemini = 'GOOGLE_API_KEY' in content and 'GOOGLE_API_KEY=' in content
        
        if has_openai or has_anthropic or has_gemini:
            return True, "API keys configured"
        else:
            return False, "No valid API keys found"
    except Exception as e:
        return False, f"Error reading file: {e}"


def print_section(title: str):
    """Print a section header."""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{title:^70}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.RESET}\n")


def print_check(name: str, status: bool, detail: str = ""):
    """Print a check result."""
    status_text = f"{Colors.GREEN}✓ PASS{Colors.RESET}" if status else f"{Colors.RED}✗ FAIL{Colors.RESET}"
    detail_text = f" ({detail})" if detail else ""
    print(f"  {status_text} {name}{detail_text}")


def main():
    """Run all verification checks."""
    
    print("\n" + Colors.BOLD + "="*70)
    print("MULTI-AGENT SDLC SYSTEM - INSTALLATION VERIFICATION")
    print("="*70 + Colors.RESET)
    
    all_passed = True
    
    # Check Python
    print_section("PYTHON ENVIRONMENT")
    py_ok, py_version = check_python_version()
    print_check("Python Version", py_ok, f"{py_version} (required: 3.10+)")
    all_passed = all_passed and py_ok
    
    print_check("Python Executable", True, sys.executable)
    
    # Check Core Packages
    print_section("CORE DEPENDENCIES")
    
    core_packages = [
        ("crewai", "crewai"),
        ("crewai-tools", "crewai_tools"),
        ("openai", "openai"),
        ("anthropic", "anthropic"),
        ("pydantic", "pydantic"),
        ("python-dotenv", "dotenv"),
    ]
    
    for package, import_name in core_packages:
        pkg_ok, pkg_version = check_package(package, import_name)
        print_check(f"{package}", pkg_ok, pkg_version)
        all_passed = all_passed and pkg_ok
    
    # Check Optional Packages
    print_section("OPTIONAL DEPENDENCIES")
    
    optional_packages = [
        ("google-generativeai", "google.generativeai"),
        ("pytest", "pytest"),
        ("requests", "requests"),
    ]
    
    for package, import_name in optional_packages:
        pkg_ok, pkg_version = check_package(package, import_name)
        status = f"{Colors.GREEN}✓ INSTALLED{Colors.RESET}" if pkg_ok else f"{Colors.YELLOW}⚠ NOT INSTALLED (optional){Colors.RESET}"
        detail_text = f" ({pkg_version})" if pkg_ok else " (recommended)"
        print(f"  {status} {package}{detail_text}")
    
    # Check Project Files
    print_section("PROJECT FILES")
    
    required_files = {
        "agents_sdlc.py": "Main system file",
        "requirements.txt": "Dependency list",
        "README.md": "Documentation",
        ".env.example": "Configuration template",
    }
    
    for filename, description in required_files.items():
        file_ok = check_file(filename)
        print_check(description, file_ok, filename)
        all_passed = all_passed and file_ok
    
    # Check Configuration
    print_section("CONFIGURATION")
    
    env_ok, env_detail = check_env_file()
    print_check(".env Configuration", env_ok, env_detail)
    
    if not env_ok:
        print(f"\n    {Colors.YELLOW}ℹ Tip: Copy .env.example to .env and add your API key{Colors.RESET}")
    
    # Check API Key in Environment
    api_keys = {
        "OPENAI_API_KEY": "OpenAI",
        "ANTHROPIC_API_KEY": "Anthropic",
        "GOOGLE_API_KEY": "Google Gemini",
    }
    
    api_found = False
    for env_var, provider in api_keys.items():
        has_key = os.getenv(env_var) is not None
        if has_key:
            api_found = True
        print_check(f"{provider} API Key", has_key, "(environment variable)")
    
    # Summary
    print_section("VERIFICATION SUMMARY")
    
    if py_ok and all_passed and (env_ok or api_found):
        print(f"{Colors.GREEN}{Colors.BOLD}✓ ALL CHECKS PASSED!{Colors.RESET}\n")
        print("Your system is ready to use. Next steps:")
        print("  1. Run: python agents_sdlc.py")
        print("  2. Or explore examples: python examples.py")
        print(f"\n{Colors.GREEN}Happy coding!{Colors.RESET}\n")
        return 0
    else:
        print(f"{Colors.RED}{Colors.BOLD}✗ SOME CHECKS FAILED{Colors.RESET}\n")
        print("Issues to fix:")
        
        if not py_ok:
            print(f"  • Python version must be 3.10 or higher (you have {py_version})")
        
        if not all_passed:
            print("  • Some dependencies are missing. Run: pip install -r requirements.txt")
        
        if not (env_ok or api_found):
            print("  • No API key found. Add to .env file or set environment variable")
        
        print()
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
