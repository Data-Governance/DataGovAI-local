import os
import torch
import sys
import subprocess

# Disable Streamlit's file watcher - this helps avoid the torch.classes issue
os.environ['STREAMLIT_FILE_WATCHER_TYPE'] = 'none'

# Monkeypatch torch.classes before Streamlit is imported by the subprocess
import torch.classes
if not hasattr(torch.classes, '__path__'):
    class PathFix:
        _path = []
    torch.classes.__path__ = PathFix()

# Set Streamlit server options as environment variables
os.environ['STREAMLIT_SERVER_PORT'] = '8505'
os.environ['STREAMLIT_SERVER_HEADLESS'] = 'true'
os.environ['STREAMLIT_BROWSER_GATHER_USAGE_STATS'] = 'false'

# Run Streamlit as a subprocess
if __name__ == "__main__":
    print("Starting Streamlit app via launcher with workarounds...")
    # Ensure the correct Python executable (from the active env) is used
    python_executable = sys.executable 
    cmd = [python_executable, "-m", "streamlit", "run", "app.py"]
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error running Streamlit: {e}")
    except FileNotFoundError:
        print(f"Error: Could not find Python executable or streamlit module.") 