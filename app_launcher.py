import os
import torch
import sys
import subprocess
import asyncio
import nest_asyncio # Import nest_asyncio

# Disable Streamlit's file watcher
os.environ['STREAMLIT_FILE_WATCHER_TYPE'] = 'none'

# Apply nest_asyncio patch early
nest_asyncio.apply()

# Define PathFix class outside conditionals
class PathFix:
    _path = []

# More comprehensive monkeypatch for torch.classes
try:
    import torch.classes
    if not hasattr(torch.classes, '__path__'):
        torch.classes.__path__ = PathFix()
except ImportError:
    print("Torch.classes not found, skipping patch.")
except Exception as e:
     print(f"Error patching torch.classes: {e}")

# Fix for torch._classes as well if needed
try:
    import torch._classes
    if not hasattr(torch._classes, '__path__'):
        torch._classes.__path__ = PathFix()
except ImportError:
    print("Torch._classes not found, skipping patch.")
except Exception as e:
     print(f"Error patching torch._classes: {e}")

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
    except KeyboardInterrupt:
        print("\nStreamlit process interrupted by user.") 