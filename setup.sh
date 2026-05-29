#!/bin/bash
# Setup script for Local Adversarial Arena

set -e

echo "🎯 Local Adversarial Arena - Setup Script"
echo "=========================================="
echo ""

# Check Python version
echo "Checking Python version..."
python_version=$(python3 --version 2>&1 | awk '{print $2}' | cut -d. -f1,2)
required_version="3.11"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "❌ Python 3.11+ required. Found: $python_version"
    exit 1
fi
echo "✓ Python $python_version found"
echo ""

# Check if Ollama is installed
echo "Checking for Ollama..."
if command -v ollama &> /dev/null; then
    echo "✓ Ollama found"
    ollama --version
else
    echo "⚠️  Ollama not found"
    echo "   Install from: https://ollama.ai/download"
    echo "   Or run: curl -fsSL https://ollama.ai/install.sh | sh"
fi
echo ""

# Create virtual environment
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    echo "✓ Virtual environment created"
else
    echo "✓ Virtual environment already exists"
fi
echo ""

# Activate and install dependencies
echo "Installing dependencies..."
source venv/bin/activate
pip install --upgrade pip > /dev/null 2>&1
pip install -r requirements.txt
echo "✓ Dependencies installed"
echo ""

# Check Ollama models
echo "Checking Ollama models..."
if command -v ollama &> /dev/null; then
    if ollama list 2>/dev/null | grep -q "llama3.2"; then
        echo "✓ llama3.2 models found"
    else
        echo "⚠️  llama3.2 not found. Pulling models (this may take a while)..."
        ollama pull llama3.2:latest &
        PULL_PID=$!
        echo "   Pull in progress (PID: $PULL_PID)"
        echo "   You can continue setup and models will download in background"
    fi
else
    echo "⚠️  Skipping model check (Ollama not installed)"
fi
echo ""

# Create directories
echo "Creating directories..."
mkdir -p logs exports data
echo "✓ Directories created"
echo ""

# Run tests
echo "Running basic tests..."
python -m pytest tests/test_env.py -v --tb=short 2>&1 | tail -20
echo ""

echo "=========================================="
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "  1. Activate venv: source venv/bin/activate"
echo "  2. Start Ollama: ollama serve (in another terminal)"
echo "  3. Run CLI: python -m src.main --check"
echo "  4. Run simulation: python -m src.main --rounds 5"
echo "  5. Or launch UI: streamlit run src/ui/streamlit_app.py"
echo ""
echo "For help: python -m src.main --help"
echo "=========================================="
