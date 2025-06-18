#!/bin/bash

# Build Elm Editor Integration Script
# This script builds the Elm kompostedit application and integrates it with the React app

echo "🎬 Building Elm Editor Integration for kompo.st..."

# Check if elm-kompostedit symlink exists
if [[ ! -L "../elm-kompostedit" ]]; then
    echo "❌ elm-kompostedit symlink not found"
    echo "Expected: ../elm-kompostedit -> /Users/stiglau/utvikling/privat/ElmMoro/kompostedit"
    echo ""
    echo "To create the symlink:"
    echo "cd .."
    echo "ln -s /Users/stiglau/utvikling/privat/ElmMoro/kompostedit elm-kompostedit"
    exit 1
fi

# Resolve the symlink to the actual path
ELM_SOURCE_PATH=$(readlink "../elm-kompostedit")
echo "📁 Elm source path: $ELM_SOURCE_PATH"

# Check if Elm source exists
if [[ ! -d "$ELM_SOURCE_PATH" ]]; then
    echo "❌ Elm source directory not found: $ELM_SOURCE_PATH"
    exit 1
fi

# Check if elm is available
if ! command -v elm &> /dev/null; then
    echo "❌ Elm compiler not found. Please install Elm:"
    echo "npm install -g elm"
    exit 1
fi

# Create public/elm directory
mkdir -p public/elm

# Build the Elm application
echo "🔨 Building Elm application..."
cd "$ELM_SOURCE_PATH"

# Build main komposition editor
echo "Building Main.elm -> kompost.js..."
elm make src/Main.elm --output="$OLDPWD/public/elm/kompost.js"

if [[ $? -eq 0 ]]; then
    echo "✅ Elm kompost.js built successfully"
else
    echo "❌ Failed to build kompost.js"
    exit 1
fi

# Build file upload component if it exists
if [[ -f "src/CustomerMedia/FileUpload.elm" ]]; then
    echo "Building FileUpload.elm -> fileupload.js..."
    elm make src/CustomerMedia/FileUpload.elm --output="$OLDPWD/public/elm/fileupload.js"
    
    if [[ $? -eq 0 ]]; then
        echo "✅ Elm fileupload.js built successfully"
    else
        echo "⚠️  Failed to build fileupload.js (non-critical)"
    fi
fi

cd "$OLDPWD"

# Verify the built files
echo ""
echo "📋 Build Summary:"
echo "- Main editor: public/elm/kompost.js ($(du -h public/elm/kompost.js | cut -f1))"
if [[ -f "public/elm/fileupload.js" ]]; then
    echo "- File upload: public/elm/fileupload.js ($(du -h public/elm/fileupload.js | cut -f1))"
fi

echo ""
echo "🎯 Integration Ready!"
echo "The Elm editor is now integrated with the React application."
echo ""
echo "Next steps:"
echo "1. Start the React development server: npm start"
echo "2. Navigate to /edit/new to test the Elm editor"
echo "3. The editor will communicate with Firebase via React"

# Copy any additional assets if needed
if [[ -d "$ELM_SOURCE_PATH/release/content" ]]; then
    echo ""
    echo "📦 Copying additional Elm assets..."
    cp -r "$ELM_SOURCE_PATH/release/content/"* public/ 2>/dev/null || true
fi

echo ""
echo "✅ Elm Editor Integration Complete!"