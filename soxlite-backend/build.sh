#!/bin/bash

# Upgrade pip
pip install --upgrade pip

# Install setuptools and wheel first
pip install setuptools wheel

# Install numpy first (dependency for pandas)
pip install numpy==1.26.2

# Install pandas
pip install pandas==2.1.4

# Install the rest of the requirements
pip install -r requirements.txt 