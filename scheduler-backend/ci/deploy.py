#!/usr/bin/env python
"""
Deployment Script

Handles deployment to different environments with proper configuration.
"""

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, Optional


class Deployer:
    """Class to handle deployment to different environments."""
    
    def __init__(self, env: str, package: str, config_file: Optional[str] = None):
        """
        Initialize the deployer.
        
        Args:
            env: Target environment (staging or production)
            package: Path to the package file to deploy
            config_file: Optional path to the deployment configuration file
        """
        self.env = env
        self.package = package
        self.config = self._load_config(config_file)
        self.deploy_timestamp = int(time.time())
    
    def _load_config(self, config_file: Optional[str]) -> Dict:
        """
        Load the deployment configuration file.
        
        Args:
            config_file: Path to the configuration file
            
        Returns:
            Dictionary containing configuration parameters
        """
        # Default configuration
        default_config = {
            "staging": {
                "service_name": "scheduler-api-staging",
                "region": "us-east-1",
                "memory": 512,
                "timeout": 30,
                "environment_variables": {
                    "DEBUG": "True",
                    "LOG_LEVEL": "INFO"
                }
            },
            "production": {
                "service_name": "scheduler-api-production",
                "region": "us-east-1",
                "memory": 1024,
                "timeout": 30,
                "environment_variables": {
                    "DEBUG": "False",
                    "LOG_LEVEL": "WARNING"
                }
            }
        }
        
        # Load custom configuration if provided
        if config_file and Path(config_file).exists():
            try:
                with open(config_file, 'r') as f:
                    custom_config = json.load(f)
                    # Merge with default config
                    for env in custom_config:
                        if env in default_config:
                            default_config[env].update(custom_config[env])
                        else:
                            default_config[env] = custom_config[env]
            except Exception as e:
                print(f"Error loading config file: {e}")
                sys.exit(1)
        
        return default_config
    
    def validate(self) -> bool:
        """
        Validate deployment parameters.
        
        Returns:
            True if validation passes, False otherwise
        """
        # Check if environment is valid
        if self.env not in self.config:
            print(f"Error: Unknown environment '{self.env}'")
            return False
        
        # Check if package file exists
        if not Path(self.package).exists():
            print(f"Error: Package file '{self.package}' does not exist")
            return False
        
        # Check if AWS credentials are available
        if not os.environ.get('AWS_ACCESS_KEY_ID') or not os.environ.get('AWS_SECRET_ACCESS_KEY'):
            print("Error: AWS credentials not found in environment variables")
            return False
        
        return True
    
    def deploy(self) -> bool:
        """
        Deploy the package to the specified environment.
        
        Returns:
            True if deployment was successful, False otherwise
        """
        if not self.validate():
            return False
        
        env_config = self.config[self.env]
        
        print(f"Deploying to {self.env} environment...")
        
        try:
            # Upload package to S3
            s3_bucket = f"scheduler-deployment-{self.env}"
            s3_key = f"packages/{Path(self.package).name}"
            
            print(f"Uploading package to S3 bucket {s3_bucket}...")
            subprocess.run([
                "aws", "s3", "cp",
                self.package,
                f"s3://{s3_bucket}/{s3_key}"
            ], check=True)
            
            # Update Lambda function (if using Lambda)
            if env_config.get('deployment_type', 'lambda') == 'lambda':
                print(f"Updating Lambda function {env_config['service_name']}...")
                
                # Prepare environment variables
                env_vars = {
                    "Variables": {
                        **env_config['environment_variables'],
                        "DEPLOY_TIMESTAMP": str(self.deploy_timestamp)
                    }
                }
                
                # Update function code
                subprocess.run([
                    "aws", "lambda", "update-function-code",
                    "--function-name", env_config['service_name'],
                    "--s3-bucket", s3_bucket,
                    "--s3-key", s3_key,
                    "--region", env_config['region']
                ], check=True)
                
                # Update function configuration
                subprocess.run([
                    "aws", "lambda", "update-function-configuration",
                    "--function-name", env_config['service_name'],
                    "--timeout", str(env_config['timeout']),
                    "--memory-size", str(env_config['memory']),
                    "--environment", json.dumps(env_vars),
                    "--region", env_config['region']
                ], check=True)
            
            # For ECS deployment
            elif env_config.get('deployment_type') == 'ecs':
                print(f"Deploying to ECS cluster {env_config['cluster']}...")
                # ECS deployment steps would go here
                pass
            
            print(f"Deployment to {self.env} completed successfully!")
            return True
            
        except subprocess.CalledProcessError as e:
            print(f"Deployment failed: {e}")
            return False
        except Exception as e:
            print(f"Unexpected error during deployment: {e}")
            return False
    
    def run_smoke_tests(self) -> bool:
        """
        Run smoke tests against the deployed service.
        
        Returns:
            True if tests pass, False otherwise
        """
        print(f"Running smoke tests against {self.env} environment...")
        
        # Placeholder for actual smoke tests
        # In a real implementation, this would run tests against the deployed API
        time.sleep(5)  # Wait for deployment to stabilize
        
        try:
            # Example: Use pytest to run smoke tests
            subprocess.run([
                "python", "-m", "pytest",
                f"../tests/smoke_tests/{self.env}",
                "-v"
            ], check=True)
            
            print("Smoke tests passed!")
            return True
        except subprocess.CalledProcessError:
            print("Smoke tests failed!")
            return False
        except Exception as e:
            print(f"Error running smoke tests: {e}")
            return False


def main():
    parser = argparse.ArgumentParser(description="Deploy the application to a specified environment")
    parser.add_argument("--env", required=True, choices=['staging', 'production'],
                        help="Target environment")
    parser.add_argument("--package", required=True,
                        help="Path to the package file to deploy")
    parser.add_argument("--config", help="Path to the deployment configuration file")
    parser.add_argument("--skip-smoke-tests", action="store_true",
                        help="Skip running smoke tests after deployment")
    
    args = parser.parse_args()
    
    deployer = Deployer(args.env, args.package, args.config)
    
    if not deployer.deploy():
        sys.exit(1)
    
    if not args.skip_smoke_tests and not deployer.run_smoke_tests():
        print("Deployment failed smoke tests!")
        sys.exit(1)
    
    print(f"Deployment to {args.env} successful!")


if __name__ == "__main__":
    main()
