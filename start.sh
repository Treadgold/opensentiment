#!/bin/bash

VENV_NAME=".venv"
PYTHON_VERSION="3.10.12"

# Check if virtual environment exists
if [ ! -d "$VENV_NAME" ]; then
    echo "Virtual environment not found. Creating new venv..."
    
    # Check if python3.10 is installed
    if ! command -v python3.10 &> /dev/null; then
        echo "Python 3.10 not found. Please install Python 3.10.12 first."
        exit 1
    fi
    
    # Create virtual environment
    python3.10 -m venv $VENV_NAME
    
    # Activate virtual environment and install dependencies
    source $VENV_NAME/bin/activate
    pip install --upgrade pip
    pip install -r requirements.txt
    
    # Add any other dependencies your project needs
    
    echo "Virtual environment created and dependencies installed."
else
    echo "Using existing virtual environment."
    source $VENV_NAME/bin/activate
fi

# Run the FastAPI application
python main.py 