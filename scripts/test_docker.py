#!/usr/bin/env python3
"""
Docker-specific test runner

Wrapper for running tests in Docker environment with proper setup.
"""

import sys
import os
from pathlib import Path

# Add src to Python path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

# Set up environment for Docker
os.environ["PYTHONPATH"] = str(project_root / "src")

# Import and run the main CI test runner
from scripts.run_ci_tests import main

if __name__ == "__main__":
    sys.exit(main())
