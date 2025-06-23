#!/bin/bash
set -e

echo "Installing system dependencies..."
apt-get update -qq
apt-get install -y build-essential

echo "Upgrading pip..."
pip install --upgrade pip

echo "Installing numpy first (required for other packages)..."
pip install numpy>=1.24.0

echo "Installing tiktoken separately..."
pip install tiktoken>=0.5.0

echo "Installing remaining requirements..."
pip install -r requirements.txt

echo "Build completed successfully!" 