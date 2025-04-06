# Python Dependency Management Best Practices

This document outlines best practices for managing Python dependencies in ML/AI projects with complex requirements.

## Key Principles

1. **Use Conda for Environment Management**
   - Conda handles both Python packages and system-level dependencies
   - Better compatibility management for scientific packages
   - Native support for CUDA/cuDNN dependencies

2. **Define Environment in Version Control**
   - Store `environment.yml` in version control
   - Include explicit version pins for critical packages
   - Document the purpose of each dependency

3. **Channel Priority**
   - Use specific channels for specific packages
   - Order channels from most specific to most general
   - Example sequence: pytorch → nvidia → conda-forge → defaults

4. **Separate Core vs. Dev Dependencies**
   - Mark development, testing, and optional dependencies clearly

## Dependency Resolution Approach

When dependency conflicts arise:

1. **Analyze the Dependency Chain**
   - Use `conda list --explicit` to see installed packages
   - Check if CUDA, Python version or PyTorch versions are incompatible
   - Identify transitive dependencies causing conflicts

2. **Clean Environment Creation**
   - Remove existing environment completely
   - Create fresh environment using the YAML definition
   - Install core packages first, then add others

3. **Use Explicit Version Pinning**
   - For packages with compatibility issues, pin exact versions
   - Example: `pytorch=2.0.1=py3.10_cuda11.8_cudnn8.7.0_0`

4. **Staged Installation**
   - Install system packages via conda first
   - Then install Python-only packages via pip
   - Use pip only inside the conda environment

## CUDA Compatibility Matrix

When working with GPU libraries, ensure version compatibility:

| Python | CUDA | PyTorch | torchvision | torchaudio |
|--------|------|---------|-------------|------------|
| 3.10   | 12.1 | 2.5.1+  | 0.20.0+     | 2.5.1+     |
| 3.10   | 11.8 | 2.0.1+  | 0.15.2+     | 2.0.1+     |
| 3.9    | 12.1 | 2.5.1+  | 0.20.0+     | 2.5.1+     |
| 3.9    | 11.8 | 2.0.1+  | 0.15.2+     | 2.0.1+     |

## Managing Library-Specific Issues

### PyTorch and CUDA
- Install PyTorch with compatible CUDA version: `pytorch-cuda=12.1`
- Use PyTorch's official channel: `-c pytorch -c nvidia`
- Check compatibility at pytorch.org/get-started

### Transformers and Dependencies
- Ensure transformers and sentence-transformers versions align
- Install huggingface_hub with proper version
- Consider installing transformers without dependencies first

### Database Connectors
- Use `psycopg2-binary` for simplified PostgreSQL setup
- Install database extensions after core DB connectors

## Reproducibility

- Use `conda list --explicit > spec-file.txt` to save exact package list
- Create environment from spec file: `conda create --name myenv --file spec-file.txt`
- Include exact pip dependencies in requirements.txt

## Conclusion

Following these best practices significantly reduces dependency issues and creates reproducible environments. Always test environment creation from scratch on a clean system to verify reproducibility. 