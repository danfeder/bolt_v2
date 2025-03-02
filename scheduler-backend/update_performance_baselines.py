#!/usr/bin/env python
"""
Performance Baseline Management Tool

This script helps manage performance baselines for regression testing.
It can update existing baselines, create new ones, and list current baselines.

Usage:
    python update_performance_baselines.py [--update] [--list] [--create-standard]

Options:
    --update           Update all existing baselines with current performance
    --list             List all existing performance baselines
    --create-standard  Create standard test baseline (overwrites if exists)
"""
import argparse
import sys
import os
import json
from pathlib import Path

# Add scheduler-backend to path
script_dir = Path(__file__).parent
sys.path.insert(0, str(script_dir))

from tests.performance.regression_tests import update_baseline, load_baseline


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Performance Baseline Management Tool")
    parser.add_argument("--update", action="store_true", help="Update all existing baselines")
    parser.add_argument("--list", action="store_true", help="List all existing baselines")
    parser.add_argument("--create-standard", action="store_true", help="Create standard test baseline")
    return parser.parse_args()


def list_baselines():
    """List all existing performance baselines."""
    baseline_dir = Path("tests/performance/baselines")
    
    if not baseline_dir.exists():
        print("No baseline directory found.")
        return
        
    baselines = list(baseline_dir.glob("*.json"))
    
    if not baselines:
        print("No baselines found.")
        return
        
    print("\nExisting Performance Baselines:")
    print("===============================\n")
    
    for baseline_file in baselines:
        name = baseline_file.stem
        
        try:
            with open(baseline_file, 'r') as f:
                data = json.load(f)
                
            print(f"- {name}:")
            for key, value in data.items():
                if isinstance(value, float):
                    print(f"  {key}: {value:.4f}")
                else:
                    print(f"  {key}: {value}")
            print()
            
        except json.JSONDecodeError:
            print(f"- {name}: [Invalid JSON format]")
            
    print(f"Total: {len(baselines)} baseline(s)")


def main():
    """Main entry point."""
    args = parse_args()
    
    if args.list:
        list_baselines()
        return
        
    if args.create_standard or args.update:
        print("Updating standard test baseline...")
        update_baseline()
        
    if not any([args.update, args.list, args.create_standard]):
        print("No action specified. Use --help to see available options.")


if __name__ == "__main__":
    main()
