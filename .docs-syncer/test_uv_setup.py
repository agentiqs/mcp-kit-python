#!/usr/bin/env python3
"""
Test script to verify the .docs-syncer uv migration is working correctly.
"""

import sys
import subprocess
from pathlib import Path

def test_uv_environment():
    """Test that uv environment is working correctly."""
    print("🧪 Testing uv environment...")
    
    # Test basic uv commands
    try:
        # Test uv version
        result = subprocess.run(['uv', '--version'], capture_output=True, text=True, check=True)
        print(f"✅ uv version: {result.stdout.strip()}")
        
        # Test uv run python
        result = subprocess.run(['uv', 'run', 'python', '--version'], capture_output=True, text=True, check=True)
        print(f"✅ Python via uv: {result.stdout.strip()}")
        
        # Test main dependencies
        test_imports = [
            "import pydoc_markdown",
            "import pytest", 
            "import mypy",
            "from generator import DocGenerator"
        ]
        
        for import_cmd in test_imports:
            result = subprocess.run(
                ['uv', 'run', 'python', '-c', import_cmd], 
                capture_output=True, text=True, check=True
            )
            print(f"✅ Import test passed: {import_cmd}")
        
        print("🎉 All uv environment tests passed!")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Test failed: {e}")
        print(f"stdout: {e.stdout}")
        print(f"stderr: {e.stderr}")
        return False

if __name__ == "__main__":
    success = test_uv_environment()
    sys.exit(0 if success else 1)
