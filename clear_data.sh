#!/bin/bash

# Clear processed data script for SAT/ACT Notes Organizer
# This script clears vector database and generated notes but preserves raw images

echo "==============================================="
echo "SAT/ACT Notes Organizer - Data Clearing Script"
echo "==============================================="
echo ""

# Navigate to project directory
cd "$(dirname "$0")"

echo "Current directory: $(pwd)"
echo ""

# Check if directories exist
if [ ! -d "data" ]; then
    echo "Error: data directory not found!"
    exit 1
fi

echo "Found data directory structure:"
echo "  - Raw images: data/raw/ ($(ls -1 data/raw/ 2>/dev/null | wc -l | tr -d ' ') files)"
echo "  - Vector database: data/vector_db/ ($(ls -1 data/vector_db/ 2>/dev/null | wc -l | tr -d ' ') files)"
echo "  - Generated notes: data/notes/ ($(ls -1 data/notes/ 2>/dev/null | wc -l | tr -d ' ') files)"
echo ""

# Confirm with user before proceeding
echo "This will clear:"
echo "  - Vector database (data/vector_db/)"
echo "  - Generated notes (data/notes/*)"
echo "  - BUT will preserve raw images (data/raw/)"
echo ""
read -p "Do you want to proceed? (y/N): " -n 1 -r
echo ""
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Operation cancelled."
    exit 0
fi

echo ""
echo "Clearing data..."

# Clear vector database
if [ -d "data/vector_db" ]; then
    rm -rf data/vector_db/
    echo "✓ Vector database cleared"
else
    echo "⚠ Vector database directory not found"
fi

# Clear generated notes
if [ -d "data/notes" ]; then
    rm -rf data/notes/*
    echo "✓ Generated notes cleared"
else
    echo "⚠ Notes directory not found"
fi

# Recreate necessary directories
mkdir -p data/vector_db
mkdir -p data/notes

echo ""
echo "Data clearing completed successfully!"
echo ""
echo "What was cleared:"
echo "  - Vector database: All processed text embeddings and metadata"
echo "  - Generated notes: All organized markdown files"
echo ""
echo "What was preserved:"
echo "  - Raw images: data/raw/ (untouched)"
echo ""
echo "The system is now reset and ready for a fresh start."
echo "Run 'python3 script/run_all.py' to process images again."
echo ""