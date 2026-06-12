#!/usr/bin/env python3
"""
Initialize Git repository and make initial commit.
"""

import subprocess
import sys
from pathlib import Path


def run_command(cmd: list[str], cwd: str | Path = ".") -> tuple[int, str, str]:
    """Run a command and return exit code, stdout, stderr."""
    result = subprocess.run(
        cmd,
        cwd=cwd,
        capture_output=True,
        text=True,
    )
    return result.returncode, result.stdout, result.stderr


def main():
    """Initialize Git repository."""
    project_dir = Path(__file__).parent
    
    print("Initializing Git repository...")
    print(f"Project directory: {project_dir}")
    print("=" * 50)
    
    # Check if git is installed
    returncode, stdout, stderr = run_command(["git", "--version"])
    if returncode != 0:
        print("Error: Git is not installed or not in PATH")
        sys.exit(1)
    
    print(f"Git version: {stdout.strip()}")
    
    # Initialize git repository
    print("\n1. Initializing git repository...")
    returncode, stdout, stderr = run_command(["git", "init"], cwd=project_dir)
    if returncode != 0:
        print(f"Error initializing git: {stderr}")
        sys.exit(1)
    print("   OK - Git repository initialized")
    
    # Add all files
    print("\n2. Adding files...")
    returncode, stdout, stderr = run_command(["git", "add", "."], cwd=project_dir)
    if returncode != 0:
        print(f"Error adding files: {stderr}")
        sys.exit(1)
    print("   OK - Files added")
    
    # Show status
    print("\n3. Git status:")
    returncode, stdout, stderr = run_command(["git", "status"], cwd=project_dir)
    print(stdout)
    
    # Make initial commit
    print("4. Making initial commit...")
    returncode, stdout, stderr = run_command(
        ["git", "commit", "-m", "Initial commit: iTab Migration Tool v1.0.0"],
        cwd=project_dir,
    )
    if returncode != 0:
        print(f"Error committing: {stderr}")
        sys.exit(1)
    print("   OK - Initial commit made")
    
    print("\n" + "=" * 50)
    print("Git repository initialized successfully!")
    print("=" * 50)
    print("\nNext steps:")
    print("1. Create a repository on GitHub")
    print("2. Add remote origin:")
    print(f"   git remote add origin https://github.com/YOUR_USERNAME/itab-migration.git")
    print("3. Push to GitHub:")
    print("   git push -u origin main")


if __name__ == "__main__":
    main()
