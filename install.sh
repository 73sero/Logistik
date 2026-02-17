#!/bin/bash
# 🚚 Logistics System - One-Command Setup
# Run this ONCE on your laptop where you have GitHub access

set -e

REPO="https://github.com/73sero/Logistik.git"
INSTALL_DIR="./Logistik"

echo "🚀 Logistics Backoffice Setup"
echo "Repository: $REPO"
echo ""

# Step 1: Clone repo
if [ -d "$INSTALL_DIR" ]; then
    echo "📂 Using existing repo at $INSTALL_DIR"
    cd "$INSTALL_DIR"
    git pull origin main
else
    echo "📥 Cloning repository..."
    git clone "$REPO" "$INSTALL_DIR"
    cd "$INSTALL_DIR"
fi

# Step 2: Check Python & Flask
echo "🔍 Checking Python..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python3 not found. Install it first:"
    echo "   macOS: brew install python3"
    echo "   Ubuntu: sudo apt install python3"
    exit 1
fi

echo "✅ Python3: $(python3 --version)"

# Step 3: Install dependencies
echo "📦 Installing Flask..."
pip install flask

# Step 4: Start server
echo ""
echo "✅ Setup complete!"
echo ""
echo "🎯 To start the server:"
echo "   cd $INSTALL_DIR"
echo "   python3 logistik_api.py"
echo ""
echo "🌐 Then open: http://localhost:5000"
