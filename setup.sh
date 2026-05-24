#!/bin/bash

# Multi-Agent SDLC System - Unix/macOS Setup Script
# This script automates the installation process for Linux and macOS

set -e  # Exit on error

echo ""
echo "============================================================================"
echo "MULTI-AGENT SDLC SYSTEM - SETUP SCRIPT (Unix/macOS)"
echo "============================================================================"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed"
    echo "Please install Python 3.10+ from https://www.python.org/"
    echo ""
    echo "On macOS (with Homebrew):"
    echo "  brew install python@3.11"
    echo ""
    echo "On Ubuntu/Debian:"
    echo "  sudo apt-get install python3.11"
    exit 1
fi

echo "✓ Python detected"
python3 --version
echo ""

# Create virtual environment
echo "Creating virtual environment..."
if [ -d "venv" ]; then
    echo "Virtual environment already exists"
else
    python3 -m venv venv
    echo "✓ Virtual environment created"
fi
echo ""

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate
echo "✓ Virtual environment activated"
echo ""

# Upgrade pip
echo "Upgrading pip..."
python3 -m pip install --upgrade pip setuptools wheel > /dev/null 2>&1
echo "✓ pip upgraded"
echo ""

# Install requirements
echo "Installing dependencies from requirements.txt..."
if pip install -r requirements.txt; then
    echo "✓ Dependencies installed successfully"
else
    echo "ERROR: Failed to install dependencies"
    exit 1
fi
echo ""

# Create .env file
echo ""
echo "============================================================================"
echo "CONFIGURATION SETUP"
echo "============================================================================"
echo ""
echo "A .env file is required to store your API keys."
echo ""

if [ -f ".env" ]; then
    echo ".env file already exists"
else
    echo "Creating .env file from template..."
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo "✓ .env file created"
    else
        echo "ERROR: .env.example not found"
    fi
fi

echo ""
echo "============================================================================"
echo "IMPORTANT: API KEY CONFIGURATION"
echo "============================================================================"
echo ""
echo "You need to add your LLM API keys to the .env file."
echo ""
echo "OPTIONS:"
echo "  1. OpenAI (GPT-4): https://platform.openai.com/api-keys"
echo "  2. Anthropic Claude: https://console.anthropic.com/"
echo "  3. Google Gemini: https://ai.google.dev/"
echo ""
echo "Edit .env and add your API key:"
echo "  OPENAI_API_KEY=sk-your-key-here"
echo ""
echo "You can open the file with:"
echo "  nano .env          # or vim, code, etc."
echo ""

# Ask to open .env file
read -p "Would you like to open .env file now? (y/n): " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    if command -v nano &> /dev/null; then
        nano .env
    elif command -v vim &> /dev/null; then
        vim .env
    elif command -v code &> /dev/null; then
        code .env
    else
        echo "No text editor found. Please edit .env manually."
    fi
fi

echo ""
echo "============================================================================"
echo "SETUP COMPLETE"
echo "============================================================================"
echo ""
echo "Next steps:"
echo "  1. Make sure your API keys are set in .env file"
echo "  2. Activate virtual environment: source venv/bin/activate"
echo "  3. Run the system: python agents_sdlc.py"
echo "  4. Or explore examples: python examples.py"
echo ""
echo "For more information, see README.md"
echo ""
