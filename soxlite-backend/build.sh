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
pip install "numpy>=2.0.0"

echo "Installing pandas with Python 3.13 compatibility..."
pip install "pandas>=2.3.0"

echo "Installing tiktoken separately..."
pip install "tiktoken>=0.5.0"

echo "Installing remaining requirements..."
pip install -r requirements.txt

echo "Build completed successfully!" 