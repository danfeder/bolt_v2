#!/usr/bin/env python
"""
Quality Gate

Enforces quality gates by checking test results, coverage, and other metrics.
"""

import argparse
import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Dict, List, Optional, Tuple


class QualityGate:
    """Class to enforce quality gates for the codebase."""
    
    def __init__(
        self,
        coverage_threshold: float = 80.0,
        test_failure_threshold: int = 0,
        complexity_threshold: float = 10.0,
        test_results: Optional[str] = None,
        coverage_file: Optional[str] = None,
        complexity_file: Optional[str] = None
    ):
        """
        Initialize the quality gate checker.
        
        Args:
            coverage_threshold: Minimum required code coverage percentage
            test_failure_threshold: Maximum allowed test failures
            complexity_threshold: Maximum allowed code complexity
            test_results: Path to the test results XML file
            coverage_file: Path to the coverage XML file
            complexity_file: Path to the complexity report file
        """
        self.coverage_threshold = coverage_threshold
        self.test_failure_threshold = test_failure_threshold
        self.complexity_threshold = complexity_threshold
        self.test_results = test_results
        self.coverage_file = coverage_file
        self.complexity_file = complexity_file
        
        # Initialize results containers
        self.test_failure_count = 0
        self.overall_coverage = 0.0
        self.max_complexity = 0.0
        self.failing_modules: List[str] = []
    
    def check_test_results(self) -> bool:
        """
        Check if the test results meet the quality gate criteria.
        
        Returns:
            True if test results pass, False otherwise
        """
        if not self.test_results or not Path(self.test_results).exists():
            print("Warning: Test results file not provided or does not exist")
            return True
        
        try:
            tree = ET.parse(self.test_results)
            root = tree.getroot()
            
            if root.tag == 'testsuites':
                # JUnit format with multiple testsuites
                failures = sum(int(testsuite.attrib.get('failures', '0')) for testsuite in root.findall('.//testsuite'))
                errors = sum(int(testsuite.attrib.get('errors', '0')) for testsuite in root.findall('.//testsuite'))
            else:
                # Single testsuite format
                failures = int(root.attrib.get('failures', '0'))
                errors = int(root.attrib.get('errors', '0'))
            
            self.test_failure_count = failures + errors
            
            if self.test_failure_count > self.test_failure_threshold:
                print(f"❌ Test quality gate failed: {self.test_failure_count} failures/errors "
                      f"(threshold: {self.test_failure_threshold})")
                
                # List failing tests
                for testsuite in root.findall('.//testsuite'):
                    for testcase in testsuite.findall('./testcase'):
                        if testcase.find('./failure') is not None or testcase.find('./error') is not None:
                            test_name = f"{testcase.attrib.get('classname', '')}.{testcase.attrib.get('name', '')}"
                            print(f"  - Failed test: {test_name}")
                
                return False
            else:
                print(f"✅ Test quality gate passed: {self.test_failure_count} failures/errors "
                      f"(threshold: {self.test_failure_threshold})")
                return True
                
        except Exception as e:
            print(f"Error parsing test results: {e}")
            return False
    
    def check_coverage(self) -> bool:
        """
        Check if the code coverage meets the quality gate criteria.
        
        Returns:
            True if coverage passes, False otherwise
        """
        if not self.coverage_file or not Path(self.coverage_file).exists():
            print("Warning: Coverage file not provided or does not exist")
            return True
        
        try:
            tree = ET.parse(self.coverage_file)
            root = tree.getroot()
            
            # Extract overall coverage
            self.overall_coverage = float(root.attrib['line-rate']) * 100
            
            # Check modules with low coverage
            for package in root.findall('.//package'):
                for module in package.findall('./classes/class'):
                    module_name = module.attrib['name']
                    module_line_rate = float(module.attrib['line-rate']) * 100
                    
                    if module_line_rate < self.coverage_threshold:
                        self.failing_modules.append(f"{module_name} ({module_line_rate:.2f}%)")
            
            if self.overall_coverage < self.coverage_threshold:
                print(f"❌ Coverage quality gate failed: {self.overall_coverage:.2f}% "
                      f"(threshold: {self.coverage_threshold}%)")
                
                # List modules with low coverage
                if self.failing_modules:
                    print("  Modules with low coverage:")
                    for module in self.failing_modules[:5]:  # Show top 5 failing modules
                        print(f"  - {module}")
                    
                    if len(self.failing_modules) > 5:
                        print(f"  - ... and {len(self.failing_modules) - 5} more")
                
                return False
            else:
                print(f"✅ Coverage quality gate passed: {self.overall_coverage:.2f}% "
                      f"(threshold: {self.coverage_threshold}%)")
                return True
                
        except Exception as e:
            print(f"Error parsing coverage file: {e}")
            return False
    
    def check_complexity(self) -> bool:
        """
        Check if the code complexity meets the quality gate criteria.
        
        Returns:
            True if complexity passes, False otherwise
        """
        if not self.complexity_file or not Path(self.complexity_file).exists():
            print("Warning: Complexity file not provided or does not exist")
            return True
        
        try:
            # Assuming the complexity file is a JSON with a specific format
            with open(self.complexity_file, 'r') as f:
                complexity_data = json.load(f)
            
            # Extract maximum complexity
            # This format would depend on your actual complexity analysis tool
            if 'max_complexity' in complexity_data:
                self.max_complexity = float(complexity_data['max_complexity'])
            else:
                # Try to find the maximum complexity in the data
                complexities = []
                for module in complexity_data.get('modules', []):
                    module_complexity = float(module.get('complexity', 0))
                    complexities.append(module_complexity)
                
                self.max_complexity = max(complexities) if complexities else 0
            
            if self.max_complexity > self.complexity_threshold:
                print(f"❌ Complexity quality gate failed: {self.max_complexity:.2f} "
                      f"(threshold: {self.complexity_threshold})")
                return False
            else:
                print(f"✅ Complexity quality gate passed: {self.max_complexity:.2f} "
                      f"(threshold: {self.complexity_threshold})")
                return True
                
        except Exception as e:
            print(f"Error parsing complexity file: {e}")
            return False
    
    def run_all_checks(self) -> bool:
        """
        Run all quality gate checks.
        
        Returns:
            True if all checks pass, False otherwise
        """
        test_result = self.check_test_results()
        coverage_result = self.check_coverage()
        complexity_result = self.check_complexity()
        
        all_passed = test_result and coverage_result and complexity_result
        
        if all_passed:
            print("\n✅ All quality gates passed!")
        else:
            print("\n❌ One or more quality gates failed!")
        
        return all_passed
    
    def generate_report(self, output_file: str) -> None:
        """
        Generate a quality gate report.
        
        Args:
            output_file: Path to save the report
        """
        report = {
            "quality_gate_status": "passed" if self.run_all_checks() else "failed",
            "metrics": {
                "test_failures": self.test_failure_count,
                "coverage": self.overall_coverage,
                "max_complexity": self.max_complexity
            },
            "thresholds": {
                "test_failures": self.test_failure_threshold,
                "coverage": self.coverage_threshold,
                "complexity": self.complexity_threshold
            },
            "failing_modules": self.failing_modules
        }
        
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"Quality gate report saved to {output_file}")


def main():
    parser = argparse.ArgumentParser(description="Enforce quality gates for the codebase")
    parser.add_argument("--coverage-threshold", type=float, default=80.0,
                        help="Minimum required code coverage percentage")
    parser.add_argument("--test-failure-threshold", type=int, default=0,
                        help="Maximum allowed test failures")
    parser.add_argument("--complexity-threshold", type=float, default=10.0,
                        help="Maximum allowed code complexity")
    parser.add_argument("--test-results", help="Path to the test results XML file")
    parser.add_argument("--coverage-file", help="Path to the coverage XML file")
    parser.add_argument("--complexity-file", help="Path to the complexity report file")
    parser.add_argument("--report", help="Path to save the quality gate report")
    parser.add_argument("--exit-code", action="store_true",
                        help="Exit with non-zero code if quality gates fail")
    
    args = parser.parse_args()
    
    quality_gate = QualityGate(
        coverage_threshold=args.coverage_threshold,
        test_failure_threshold=args.test_failure_threshold,
        complexity_threshold=args.complexity_threshold,
        test_results=args.test_results,
        coverage_file=args.coverage_file,
        complexity_file=args.complexity_file
    )
    
    if args.report:
        quality_gate.generate_report(args.report)
        passed = quality_gate.run_all_checks()
    else:
        passed = quality_gate.run_all_checks()
    
    if args.exit_code and not passed:
        sys.exit(1)


if __name__ == "__main__":
    main()
