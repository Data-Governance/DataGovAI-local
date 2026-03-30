#!/bin/bash
# Usage: bash setup_venv.sh
# Creates Python 3.11 venv and installs dependencies
set -e

# Detect OS
OS="$(uname -s)"

# Install Python 3.11 if not present
if ! command -v python3.11 &> /dev/null; then
  echo "Python 3.11 is not installed. Attempting to install..."
  if [ "$OS" = "Linux" ]; then
    if [ -f /etc/debian_version ]; then
      # Ubuntu/Debian
      sudo apt update
      sudo apt install -y software-properties-common
      sudo add-apt-repository -y ppa:deadsnakes/ppa
      sudo apt update
      sudo apt install -y python3.11 python3.11-venv python3.11-distutils
    else
      echo "Please install Python 3.11 manually for your Linux distribution."
      exit 1
    fi
  elif [ "$OS" = "Darwin" ]; then
    # macOS
    echo "Please install Python 3.11 using Homebrew: brew install python@3.11"
    exit 1
  else
    echo "Unsupported OS. Please install Python 3.11 manually."
    exit 1
  fi
fi

python3.11 -m venv rag_env_311
source rag_env_311/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

echo "\n✅ Environment ready. Activate with: source rag_env_311/bin/activate"
