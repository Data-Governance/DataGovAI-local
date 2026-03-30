# Conda-based setup for DataGovAI (Python 3.11)
# Usage: bash setup_conda.sh
set -e

ENV_NAME=datagovai311
PYTHON_VERSION=3.11

# Create conda env if it doesn't exist
echo "Creating conda environment: $ENV_NAME with Python $PYTHON_VERSION..."
conda create -y -n $ENV_NAME python=$PYTHON_VERSION

echo "Activating conda environment..."
source $(conda info --base)/etc/profile.d/conda.sh
conda activate $ENV_NAME

echo "Installing dependencies with pip..."
pip install --upgrade pip
pip install -r requirements.txt

echo "\n✅ Conda environment '$ENV_NAME' with Python $PYTHON_VERSION is ready. Activate with:"
echo "conda activate $ENV_NAME"
