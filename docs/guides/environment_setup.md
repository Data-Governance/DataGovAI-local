# Environment Setup Guide

This guide explains how to set up the development environment for the Knowledge Base Agent project. We provide two main methods: Conda (recommended for GPU users and managing complex dependencies) and standard Python `venv` (suitable for CPU-only development or users comfortable managing system dependencies).

## Method 1: Conda (Recommended)

This method uses Conda to manage both Python packages and potentially complex system dependencies like CUDA toolkits. It provides the best isolation and is recommended for leveraging GPU acceleration.

**Prerequisites:**
- [Miniconda](https://docs.conda.io/en/latest/miniconda.html) or [Anaconda](https://www.anaconda.com/products/distribution)

**Steps:**

1.  **Clone the repository (if you haven't already):**
    ```bash
    git clone https://github.com/yourusername/knowledge-base-agent.git
    cd knowledge-base-agent
    ```

2.  **Create the Conda environment from the provided file:**
    This command creates an environment named `chatbot` using the exact dependencies specified in `chatbot_environment.yml`.
    ```bash
    conda env create -f chatbot_environment.yml
    ```
    *(This step might take a few minutes)*

3.  **Activate the environment:**
    You need to activate the environment each time you work on the project in a new terminal session.
    ```bash
    conda activate chatbot
    ```
    Your terminal prompt should now start with `(chatbot)`.

4.  **Verify GPU Setup (Optional but Recommended):**
    If you intend to use GPU acceleration (highly recommended for performance), verify PyTorch can access your CUDA device:
    ```bash
    python -c "import torch; print(f'CUDA Available: {torch.cuda.is_available()}\nCUDA Version: {torch.version.cuda}')"
    ```
    If `CUDA Available` is `False`, consult the [GPU Configuration Guide](gpu_setup.md).

5.  **Set up `.env` file:**
    Copy the example environment file and configure it for your setup (especially database connection and model paths/settings):
    ```bash
    cp .env.example .env
    # Edit .env with your specific settings using a text editor
    # Example: nano .env
    ```

**Updating the Environment:**
If dependencies are added or updated, regenerate the `chatbot_environment.yml` file:
```bash
# Make sure the 'chatbot' environment is active
conda env export > chatbot_environment.yml
```
Commit the updated `chatbot_environment.yml` file.

## Method 2: venv + requirements.txt

This method uses Python's built-in `venv` module and `pip` with `requirements.txt`. It's generally faster for pure Python packages but requires manual management of non-Python dependencies like CUDA.

**Prerequisites:**
- Python 3.10+
- `pip` (usually included with Python)
- Git
- **Manual Installation:** You *must* manually ensure any required system libraries or drivers (like CUDA toolkit, cuDNN) are installed correctly on your system *before* installing Python packages that depend on them.

**Steps:**

1.  **Clone the repository (if you haven't already):**
    ```bash
    git clone https://github.com/yourusername/knowledge-base-agent.git
    cd knowledge-base-agent
    ```

2.  **Create a virtual environment:**
    ```bash
    python -m venv .venv
    ```
    This creates a `.venv` directory containing the Python interpreter and libraries.

3.  **Activate the virtual environment:**
    *   **Linux/macOS:**
        ```bash
        source .venv/bin/activate
        ```
    *   **Windows (Git Bash):**
        ```bash
        source .venv/Scripts/activate
        ```
    *   **Windows (Command Prompt):**
        ```bash
        .venv\Scripts\activate.bat
        ```
    *   **Windows (PowerShell):**
        ```bash
        .venv\Scripts\Activate.ps1
        ```
    Your terminal prompt should now start with `(.venv)`.

4.  **Install required Python packages:**
    ```bash
    pip install -r requirements.txt
    ```

5.  **Install PyTorch with CUDA (if using GPU):**
    *This step is CRITICAL if you need GPU support.* You must install the correct PyTorch version matching your **manually installed** CUDA toolkit version. Visit the [PyTorch installation page](https://pytorch.org/get-started/locally/) to get the correct `pip` command for your specific CUDA version.
    *Example (Check PyTorch website for the command matching YOUR system):*
    ```bash
    # Example for CUDA 11.8 - DO NOT run this without checking PyTorch website!
    pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
    ```

6.  **Install Development Dependencies (Optional):**
    If you plan to run tests or contribute code:
    ```bash
    pip install -r requirements-dev.txt
    ```

7.  **Set up `.env` file:**
    ```bash
    cp .env.example .env
    # Edit .env with your specific settings
    ```

**Updating the Environment:**
If core dependencies change, update `requirements.txt`:
```bash
# Make sure the '.venv' environment is active
pip freeze > requirements.txt
```
Commit the updated `requirements.txt` file.

## Choosing the Right Method

- **Use Conda if:** You have a GPU and want easier CUDA management, need strong environment isolation, or are dealing with complex non-Python dependencies.
- **Use venv if:** You are doing CPU-only development, are comfortable managing system dependencies like CUDA manually, or prefer standard Python tooling.

## Troubleshooting

- Refer to the [Troubleshooting Guide](../maintenance/troubleshooting.md) for common issues.
- Consult the [GPU Configuration Guide](gpu_setup.md) for specific GPU problems. 