#!/usr/bin/env python
"""
Environment Verification Script

This script verifies that the current environment is correctly set up for the
Gym Rotation Scheduler backend. It checks Python version, package installation,
and other environment requirements.
"""

import importlib
import os
import platform
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Tuple

# Define required packages and versions
REQUIRED_PACKAGES = {
    "fastapi": "0.68.0",
    "pydantic": "1.8.0",
    "ortools": "9.3.10497",
    "httpx": "0.28.1",
    "pytest": "7.0.0",
}

# Define required Python version
REQUIRED_PYTHON = (3, 11)


def check_python_version() -> bool:
    """Check if Python version meets requirements."""
    current = sys.version_info[:2]
    required = REQUIRED_PYTHON
    
    is_valid = current[0] == required[0] and current[1] == required[1]
    
    print(f"Python Version: {sys.version}")
    print(f"Required: {required[0]}.{required[1]}.x")
    print(f"Status: {'✅ OK' if is_valid else '❌ FAILED'}")
    
    return is_valid


def check_packages() -> Tuple[bool, List[str]]:
    """Check if required packages are installed with correct versions."""
    all_ok = True
    missing_or_invalid = []
    
    print("\nChecking required packages:")
    for package, min_version in REQUIRED_PACKAGES.items():
        try:
            module = importlib.import_module(package)
            version = getattr(module, "__version__", "Unknown")
            
            # Simple version comparison - could be enhanced for more complex version strings
            version_ok = version >= min_version
            
            status = "✅ OK" if version_ok else "❌ VERSION TOO OLD"
            print(f"  {package}: found {version}, required >={min_version} - {status}")
            
            if not version_ok:
                all_ok = False
                missing_or_invalid.append(f"{package}>={min_version}")
                
        except ImportError:
            print(f"  {package}: ❌ NOT FOUND")
            all_ok = False
            missing_or_invalid.append(f"{package}>={min_version}")
    
    return all_ok, missing_or_invalid


def check_environment_variables() -> bool:
    """Check if necessary environment variables are set."""
    # Currently no required env vars, but we'll keep this for future use
    print("\nChecking environment variables:")
    print("  No required environment variables for development")
    return True


def check_or_tools() -> bool:
    """Perform a simple OR-Tools test to verify it's working correctly."""
    print("\nTesting OR-Tools functionality:")
    try:
        from ortools.sat.python import cp_model
        
        # Create simple model
        model = cp_model.CpModel()
        x = model.NewIntVar(0, 10, "x")
        y = model.NewIntVar(0, 10, "y")
        model.Add(x + y == 10)
        
        # Create solver and solve
        solver = cp_model.CpSolver()
        status = solver.Solve(model)
        
        if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
            print(f"  OR-Tools test: ✅ OK (Found solution: x={solver.Value(x)}, y={solver.Value(y)})")
            return True
        else:
            print("  OR-Tools test: ❌ FAILED (Could not solve simple model)")
            return False
            
    except Exception as e:
        print(f"  OR-Tools test: ❌ FAILED ({str(e)})")
        return False


def check_directory_structure() -> bool:
    """Check if the project directory structure is valid."""
    base_dir = Path(__file__).parent.parent
    required_dirs = ["app", "tests", "data"]
    required_files = ["requirements.txt", "pytest.ini"]
    
    print("\nChecking project structure:")
    
    all_ok = True
    for dir_name in required_dirs:
        dir_path = base_dir / dir_name
        if dir_path.is_dir():
            print(f"  Directory {dir_name}: ✅ Found")
        else:
            print(f"  Directory {dir_name}: ❌ Missing")
            all_ok = False
    
    for file_name in required_files:
        file_path = base_dir / file_name
        if file_path.is_file():
            print(f"  File {file_name}: ✅ Found")
        else:
            print(f"  File {file_name}: ❌ Missing")
            all_ok = False
    
    return all_ok


def check_virtual_env() -> bool:
    """Check if running in a virtual environment."""
    in_venv = hasattr(sys, 'real_prefix') or (
        hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix
    )
    
    print("\nChecking virtual environment:")
    if in_venv:
        print(f"  Virtual Environment: ✅ Active ({sys.prefix})")
        return True
    else:
        print("  Virtual Environment: ❌ Not active")
        print("  Recommendation: Activate virtual environment with 'source venv/bin/activate'")
        return False


def main():
    """Run all checks and display a summary."""
    print("=" * 80)
    print("ENVIRONMENT VERIFICATION REPORT")
    print("=" * 80)
    
    system_info = platform.uname()
    print(f"System: {system_info.system} {system_info.release}")
    print(f"Machine: {system_info.machine}")
    print("-" * 80)
    
    # Run all checks
    python_ok = check_python_version()
    venv_ok = check_virtual_env()
    packages_ok, missing_pkgs = check_packages()
    env_vars_ok = check_environment_variables()
    ortools_ok = check_or_tools()
    structure_ok = check_directory_structure()
    
    # Overall result
    all_checks_passed = python_ok and packages_ok and env_vars_ok and ortools_ok and structure_ok
    
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Python Version: {'✅ OK' if python_ok else '❌ FAILED'}")
    print(f"Virtual Environment: {'✅ OK' if venv_ok else '❌ NOT ACTIVE'}")
    print(f"Required Packages: {'✅ OK' if packages_ok else '❌ ISSUES FOUND'}")
    print(f"Environment Variables: {'✅ OK' if env_vars_ok else '❌ ISSUES FOUND'}")
    print(f"OR-Tools Functionality: {'✅ OK' if ortools_ok else '❌ FAILED'}")
    print(f"Project Structure: {'✅ OK' if structure_ok else '❌ ISSUES FOUND'}")
    
    print("\nOVERALL RESULT: " + ("✅ PASSED" if all_checks_passed else "❌ FAILED"))
    
    # Provide instructions for fixing issues
    if not all_checks_passed:
        print("\nRECOMMENDED ACTIONS:")
        
        if not python_ok:
            print("- Install Python 3.11.x (required for OR-Tools compatibility)")
            print("  macOS: brew install python@3.11")
            print("  Linux: sudo apt install python3.11 python3.11-venv")
        
        if not venv_ok:
            print("- Activate virtual environment: source venv/bin/activate")
        
        if not packages_ok:
            print(f"- Install missing or update outdated packages:")
            for pkg in missing_pkgs:
                print(f"  pip install {pkg}")
        
        if not ortools_ok:
            print("- Reinstall OR-Tools: pip install --force-reinstall ortools==9.3.10497")
        
        if not structure_ok:
            print("- Make sure you're running this script from the project root directory")
    
    # Set exit code based on overall result
    sys.exit(0 if all_checks_passed else 1)


if __name__ == "__main__":
    main() 