#!/bin/bash
# FABO Quick Setup Script
# This script helps you get started with FABO

set -e

echo "🎉 FABO Setup Script"
echo "===================="
echo

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "📦 Installing uv package manager..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.local/bin:$PATH"
fi

# Install dependencies
echo "📚 Installing dependencies..."
uv sync

# Create .env if it doesn't exist
if [ ! -f .env ]; then
    echo "⚙️  Creating .env file..."
    cp .env.example .env
    echo "✅ Created .env file - please edit with your API keys"
else
    echo "ℹ️  .env file already exists"
fi

# Create data directories
echo "📁 Creating data directories..."
mkdir -p data/runs
mkdir -p data/milestones
mkdir -p screenshots
mkdir -p temp_screenshots

# Create runs directory if needed
mkdir -p runs

echo
echo "✅ Setup complete!"
echo
echo "Next steps:"
echo "  1. Edit .env with your API keys:"
echo "     nano .env"
echo
echo "  2. Configure a tracking run:"
echo "     cp runs/example-github-stars.yaml runs/my-run.yaml"
echo "     nano runs/my-run.yaml"
echo
echo "  3. Test your configuration:"
echo "     fabo run --config runs/my-run.yaml --dry-run"
echo
echo "  4. Run your first check:"
echo "     fabo run --config runs/my-run.yaml"
echo
echo "  5. Check status:"
echo "     fabo status"
echo
echo "For GitHub Actions setup, see:"
echo "  .github/workflows/fabo-check.yml"
echo
echo "Documentation:"
echo "  - Quick Start: docs/quick-start.md"
echo "  - Architecture: ARCHITECTURE_V2.md"
echo "  - Operators: docs/operators.md"
echo
