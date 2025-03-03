#!/usr/bin/env python
"""
Coverage Report Generator

This script generates a formatted coverage report from coverage data,
with highlighting of areas that need improvement.
"""

import argparse
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Tuple


def parse_coverage_xml(xml_path: str) -> Tuple[float, Dict[str, float], List[Dict]]:
    """
    Parse the coverage XML file and extract relevant information.
    
    Args:
        xml_path: Path to the coverage XML file
        
    Returns:
        Tuple containing overall coverage, module coverage, and untested functions
    """
    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()
    except Exception as e:
        print(f"Error parsing coverage file: {e}")
        sys.exit(1)
    
    # Extract overall coverage
    overall_coverage = float(root.attrib['line-rate']) * 100
    
    # Extract module coverage
    module_coverage = {}
    untested_functions = []
    
    for package in root.findall('.//package'):
        package_name = package.attrib['name']
        
        for module in package.findall('./classes/class'):
            module_name = module.attrib['name']
            module_line_rate = float(module.attrib['line-rate']) * 100
            module_coverage[f"{package_name}.{module_name}"] = module_line_rate
            
            # Find untested functions (methods with line-rate = 0)
            for method in module.findall('./methods/method'):
                method_line_rate = float(method.attrib.get('line-rate', '0'))
                if method_line_rate == 0:
                    untested_functions.append({
                        'module': f"{package_name}.{module_name}",
                        'function': method.attrib['name'],
                        'line': method.attrib.get('line', 'N/A')
                    })
    
    return overall_coverage, module_coverage, untested_functions


def generate_markdown_report(
    overall_coverage: float,
    module_coverage: Dict[str, float],
    untested_functions: List[Dict],
    output_path: str
) -> None:
    """
    Generate a markdown report with the coverage information.
    
    Args:
        overall_coverage: Overall line coverage percentage
        module_coverage: Dictionary mapping module names to coverage percentages
        untested_functions: List of untested functions
        output_path: Path to save the generated report
    """
    with open(output_path, 'w') as f:
        # Header
        f.write("# Coverage Report\n\n")
        
        # Overall coverage
        coverage_status = "✅ Good" if overall_coverage >= 80 else "⚠️ Needs improvement" if overall_coverage >= 60 else "❌ Critical"
        f.write(f"## Overall Coverage: {overall_coverage:.2f}% {coverage_status}\n\n")
        
        # Module coverage table
        f.write("## Module Coverage\n\n")
        f.write("| Module | Coverage | Status |\n")
        f.write("|--------|----------|--------|\n")
        
        # Sort modules by coverage (ascending)
        sorted_modules = sorted(module_coverage.items(), key=lambda x: x[1])
        
        for module, coverage in sorted_modules:
            status = "✅" if coverage >= 80 else "⚠️" if coverage >= 60 else "❌"
            f.write(f"| {module} | {coverage:.2f}% | {status} |\n")
        
        # Untested functions
        if untested_functions:
            f.write("\n## Untested Functions\n\n")
            f.write("| Module | Function | Line |\n")
            f.write("|--------|----------|------|\n")
            
            for func in untested_functions:
                f.write(f"| {func['module']} | {func['function']} | {func['line']} |\n")
        
        # Recommendations
        f.write("\n## Recommendations\n\n")
        
        # Get modules with low coverage
        low_coverage_modules = [m for m, c in sorted_modules if c < 60]
        
        if low_coverage_modules:
            f.write("### Critical: Improve coverage for these modules\n\n")
            for module in low_coverage_modules[:5]:  # Show top 5 critical modules
                f.write(f"- {module}\n")
        
        if overall_coverage < 80:
            f.write("\n### General Recommendations\n\n")
            f.write("- Add tests for untested functions\n")
            f.write("- Focus on modules with coverage below 60%\n")
            f.write("- Consider adding integration tests for complex functionality\n")


def main():
    parser = argparse.ArgumentParser(description="Generate a formatted coverage report")
    parser.add_argument("--input", required=True, help="Path to coverage XML file")
    parser.add_argument("--output", required=True, help="Path to output markdown report")
    
    args = parser.parse_args()
    
    # Check if input file exists
    if not Path(args.input).exists():
        print(f"Error: Input file {args.input} does not exist")
        sys.exit(1)
    
    # Parse coverage data
    overall_coverage, module_coverage, untested_functions = parse_coverage_xml(args.input)
    
    # Generate report
    generate_markdown_report(overall_coverage, module_coverage, untested_functions, args.output)
    
    print(f"Coverage report generated at {args.output}")


if __name__ == "__main__":
    main()
