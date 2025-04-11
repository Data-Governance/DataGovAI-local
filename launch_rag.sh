#!/bin/bash
# DataGovAI Knowledge Base Agent - Launch Script
# Handles environment setup, dependency checks, and app launching 
# with PyTorch/Streamlit compatibility fixes

set -e  # Exit on errors

# Get the directory of this script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" >/dev/null 2>&1 && pwd)"
cd "$SCRIPT_DIR"

# Default Streamlit port
STREAMLIT_PORT=8505

# Output styling
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to check if port is in use
check_port() {
    if command -v lsof >/dev/null 2>&1; then
        lsof -i :$STREAMLIT_PORT >/dev/null 2>&1
    else
        netstat -an | grep $STREAMLIT_PORT >/dev/null 2>&1
    fi
}

# Function to kill existing Streamlit processes
cleanup_streamlit() {
    echo -e "${YELLOW}Checking for existing Streamlit processes...${NC}"
    # Find and kill any existing streamlit processes
    pkill -f "streamlit run" || true
    
    # Wait for port to be freed (max 5 seconds)
    local max_attempts=5
    local attempt=1
    while check_port && [ $attempt -le $max_attempts ]; do
        echo "Waiting for port $STREAMLIT_PORT to be freed... (attempt $attempt/$max_attempts)"
        sleep 1
        attempt=$((attempt + 1))
    done

    if check_port; then
        echo -e "${RED}Error: Port $STREAMLIT_PORT is still in use. Please free it manually.${NC}"
        return 1
    fi
    
    return 0
}

# Check if mamba is available, fallback to conda
if command -v mamba &> /dev/null; then
    CONDA_CMD="mamba"
    echo -e "${GREEN}Using mamba for faster environment setup${NC}"
else
    CONDA_CMD="conda"
    echo -e "${YELLOW}Mamba not found, using conda instead${NC}"
fi

# Source the conda script to enable conda/mamba command
if [ -f "$HOME/anaconda3/etc/profile.d/conda.sh" ]; then
    . "$HOME/anaconda3/etc/profile.d/conda.sh"
elif [ -f "$HOME/miniconda3/etc/profile.d/conda.sh" ]; then
    . "$HOME/miniconda3/etc/profile.d/conda.sh"
else
    echo -e "${RED}Error: Could not find conda.sh${NC}"
    exit 1
fi

# Check for existing environment and remove if needed
if conda env list | grep -q "^rag_env "; then
    echo -e "${YELLOW}Found existing rag_env environment. Removing for clean install...${NC}"
    conda deactivate
    conda env remove -n rag_env --yes
fi

# Create fresh environment
echo -e "${GREEN}Creating fresh rag_env environment...${NC}"
$CONDA_CMD env create -f environment.yml

# Activate the environment
echo -e "${GREEN}Activating rag_env environment...${NC}"
conda activate rag_env

# Check if activation was successful
if [ "$CONDA_DEFAULT_ENV" != "rag_env" ]; then
    echo -e "${RED}Error: Failed to activate environment${NC}"
    exit 1
fi

# Verify NumPy version
NUMPY_VERSION=$(python -c "import numpy; print(numpy.__version__)" 2>/dev/null)
echo -e "${GREEN}NumPy version: $NUMPY_VERSION${NC}"
if [[ $NUMPY_VERSION != 1.* ]]; then
    echo -e "${RED}Error: NumPy version must be 1.x.x but got $NUMPY_VERSION${NC}"
    echo -e "${YELLOW}Fixing NumPy version...${NC}"
    python -m pip install numpy==1.24.3 --force-reinstall
fi

# Install spaCy model if needed
python -c "import spacy; spacy.load('en_core_web_sm')" 2>/dev/null || {
    echo -e "${YELLOW}Installing spaCy English model...${NC}"
    python -m spacy download en_core_web_sm
}

# Clean up any existing Streamlit processes
cleanup_streamlit || exit 1

echo -e "${GREEN}Starting Knowledge Base Agent...${NC}"
# Run the actual app launcher
python app_launcher.py

# Return exit code from the Python script
exit $? 