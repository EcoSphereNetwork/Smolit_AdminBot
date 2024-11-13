FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    wget \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requiements.txt .
RUN pip install --no-cache-dir -r requiements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p /usr/local/bin models logs memory

# Download Llama model
RUN wget -O models/Llama-3.2-1B-Instruct.Q6_K.llamafile "https://huggingface.co/Mozilla/Llama-3.2-1B-Instruct-llamafile/resolve/main/Llama-3.2-1B-Instruct.Q6_K.llamafile?download=true" \
    && chmod +x models/Llama-3.2-1B-Instruct.Q6_K.llamafile \
    && ln -sf /app/models/Llama-3.2-1B-Instruct.Q6_K.llamafile /usr/local/bin/llamafile

# Set up permissions
RUN chmod +x setup_permissions.sh && ./setup_permissions.sh

# Expose port for LlamaFile server
EXPOSE 8080

# Command to run tests
CMD ["python", "-m", "unittest", "test_bot.py", "-v"]
