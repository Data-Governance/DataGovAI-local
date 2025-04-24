# Use micromamba base image for lightweight conda support
FROM mambaorg/micromamba:1.5.0

# Set working directory
WORKDIR /app

# Copy environment definition and install packages
COPY environment.yml ./
RUN micromamba create -n rag -f environment.yml -y \
    && micromamba clean --all --yes

# Copy application code
COPY . ./

# Expose Streamlit port
EXPOSE 8505

# Launch the application using the launcher script
CMD ["micromamba", "run", "-n", "rag", "--no-capture-output", "python", "app_launcher.py"] 