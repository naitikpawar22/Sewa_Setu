import os
import subprocess
import sys
import pytest

def test_deemed_approval_config_and_execution():
    """
    Test that deemed_approval.py locates its configuration file and runs
    without raising FileNotFoundError for missing settings.ini.
    """
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    script_path = os.path.join(base_dir, "app", "scripts", "deemed_approval.py")
    
    # Run the script via python process with a dry-run / import check
    # Before the fix, module-level execution fails immediately on line 24 with FileNotFoundError
    res = subprocess.run(
        [sys.executable, script_path],
        capture_output=True,
        text=True,
        cwd=os.path.join(base_dir, "app")
    )
    
    # Assert that it does NOT fail with FileNotFoundError for settings.ini
    assert "FileNotFoundError" not in res.stderr, f"Job failed with missing config: {res.stderr}"
    assert "settings.ini" not in res.stderr, f"Job failed looking for settings.ini: {res.stderr}"
