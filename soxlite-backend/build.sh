#!/bin/bash
set -e

echo "Checking Python version..."
python --version

echo "Installing system dependencies..."
apt-get update -qq
apt-get install -y build-essential

echo "Upgrading pip..."
pip install --upgrade pip

echo "Installing numpy first (required for other packages)..."
pip install "numpy==1.26.2"

echo "Installing pandas..."
pip install "pandas==2.1.4"

echo "Installing tiktoken separately..."
pip install "tiktoken==0.5.2"

echo "Installing remaining requirements..."
pip install -r requirements.txt

echo "Build completed successfully!" 