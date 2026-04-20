FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    wget \
    ca-certificates \
    && wget http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz \
    && tar -xzf ta-lib-0.4.0-src.tar.gz \
    && cd ta-lib/ \
    && curl -o config.guess 'https://raw.githubusercontent.com/gcc-mirror/gcc/master/config.guess' \
    && curl -o config.sub 'https://raw.githubusercontent.com/gcc-mirror/gcc/master/config.sub' \
    && chmod +x config.guess config.sub \
    && ./configure --prefix=/usr \
    && make \
    && make install \
    && cd .. \
    && rm -rf ta-lib* \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements (we will create this soon)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Create a non-root user for security
RUN adduser --disabled-password --gecos '' appuser

# Copy the rest of the application
COPY . .

# Switch to non-root user
RUN chown -R appuser:appuser /app
USER appuser

EXPOSE 8501

HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health

ENTRYPOINT ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
