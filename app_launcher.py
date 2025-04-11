import os
import sys
import subprocess

# Disable Streamlit's file watcher - this helps avoid Streamlit crashing issues
os.environ['STREAMLIT_FILE_WATCHER_TYPE'] = 'none'

# Fix for torch.classes with safer import pattern
try:
    import torch
    # Create torch.classes if it doesn't exist
    if not hasattr(torch, 'classes'):
        # Create a dummy module and attach it to torch
        import types
        torch.classes = types.ModuleType('torch.classes')
        torch.classes.__path__ = []
        sys.modules['torch.classes'] = torch.classes
    print("PyTorch configured successfully")
except ImportError as e:
    print(f"Warning: Could not import torch: {e}")
except Exception as e:
    print(f"Warning: Error during torch configuration: {e}")

# Set Streamlit server options as environment variables
os.environ['STREAMLIT_SERVER_PORT'] = '8505'
os.environ['STREAMLIT_SERVER_HEADLESS'] = 'true'
os.environ['STREAMLIT_BROWSER_GATHER_USAGE_STATS'] = 'false'

# Run Streamlit as a subprocess
if __name__ == "__main__":
    print("Starting Streamlit app via launcher with workarounds...")
    # Ensure the correct Python executable (from the active env) is used
    python_executable = sys.executable 
    
    # Pass environment variables to the subprocess
    env = os.environ.copy()
    
    # Use streamlit directly - this avoids the torch import in the child process
    cmd = [python_executable, "-m", "streamlit", "run", "app.py"]
    try:
        subprocess.run(cmd, check=True, env=env)
    except subprocess.CalledProcessError as e:
        print(f"Error running Streamlit: {e}")
    except FileNotFoundError:
        print(f"Error: Could not find Python executable or streamlit module.") 