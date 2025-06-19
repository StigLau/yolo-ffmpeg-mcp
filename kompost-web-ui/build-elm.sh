#!/bin/bash

# Build Elm Editor Integration Script
# This script builds the Elm kompostedit application and integrates it with the React app

set -e  # Exit on any error

echo "🎬 Building Elm Editor Integration for kompo.st..."

# Function to find Elm source directory
find_elm_source() {
    # Possible locations for the Elm source
    local possible_paths=(
        "../elm-kompostedit"                                    # Symlink in parent
        "/Users/stiglau/utvikling/privat/ElmMoro/kompostedit"  # Direct path
        "./elm-kompostedit"                                     # Local symlink
        "../../ElmMoro/kompostedit"                            # Relative path up
    )
    
    for path in "${possible_paths[@]}"; do
        if [[ -d "$path" && -f "$path/elm.json" ]]; then
            echo "$path"
            return 0
        fi
    done
    
    return 1
}

# Find Elm source directory
ELM_SOURCE_PATH=$(find_elm_source)
if [[ $? -ne 0 ]]; then
    echo "❌ Elm kompostedit source not found!"
    echo ""
    echo "Searched these locations:"
    echo "  - ../elm-kompostedit"
    echo "  - /Users/stiglau/utvikling/privat/ElmMoro/kompostedit"
    echo "  - ./elm-kompostedit"
    echo "  - ../../ElmMoro/kompostedit"
    echo ""
    echo "To create a symlink:"
    echo "  cd .."
    echo "  ln -s /Users/stiglau/utvikling/privat/ElmMoro/kompostedit elm-kompostedit"
    echo ""
    echo "Or specify path manually:"
    echo "  ELM_SOURCE=/path/to/kompostedit ./build-elm.sh"
    exit 1
fi

# Allow override via environment variable
if [[ -n "$ELM_SOURCE" && -d "$ELM_SOURCE" ]]; then
    ELM_SOURCE_PATH="$ELM_SOURCE"
fi

# Resolve to absolute path
ELM_SOURCE_PATH=$(cd "$ELM_SOURCE_PATH" && pwd)
echo "📁 Elm source path: $ELM_SOURCE_PATH"

# Check if elm is available
if ! command -v elm &> /dev/null; then
    echo "❌ Elm compiler not found. Installing via npm..."
    npm install -g elm || {
        echo "❌ Failed to install Elm. Please install manually:"
        echo "  npm install -g elm"
        echo "  or visit: https://guide.elm-lang.org/install/"
        exit 1
    }
fi

# Create public/elm directory
mkdir -p public/elm

# Backup existing files
if [[ -f "public/elm/kompost.js" ]]; then
    echo "📦 Backing up existing kompost.js..."
    cp "public/elm/kompost.js" "public/elm/kompost.js.backup.$(date +%s)"
fi

# Build the Elm application
echo "🔨 Building Elm application..."
cd "$ELM_SOURCE_PATH"

# Check elm.json exists
if [[ ! -f "elm.json" ]]; then
    echo "❌ No elm.json found in $ELM_SOURCE_PATH"
    echo "This doesn't appear to be a valid Elm project directory."
    exit 1
fi

# Install Elm dependencies if needed
if [[ ! -d "elm-stuff" ]]; then
    echo "📥 Installing Elm dependencies..."
    elm install --yes
fi

# Build main komposition editor
echo "🛠️  Building Main.elm -> kompost.js..."
OUTPUT_PATH="$OLDPWD/public/elm/kompost.js"

# Try optimized build first, fall back to debug build if needed
echo "🛠️  Attempting optimized build..."
if elm make src/Main.elm --output="$OUTPUT_PATH" --optimize 2>/dev/null; then
    echo "✅ Optimized build successful"
else
    echo "⚠️  Optimized build failed (Debug statements found), building debug version..."
    elm make src/Main.elm --output="$OUTPUT_PATH"
    if [[ $? -ne 0 ]]; then
        echo "❌ Debug build also failed"
        exit 1
    fi
    echo "✅ Debug build successful"
fi

if [[ $? -eq 0 && -f "$OUTPUT_PATH" ]]; then
    echo "✅ Elm kompost.js built successfully"
    
    # Optimize the JS file size
    if command -v uglifyjs &> /dev/null; then
        echo "🗜️  Optimizing JS file size..."
        TEMP_FILE=$(mktemp)
        uglifyjs "$OUTPUT_PATH" --compress 'pure_funcs=[F2,F3,F4,F5,F6,F7,F8,F9,A2,A3,A4,A5,A6,A7,A8,A9],pure_getters,keep_fargs=false,unsafe_comps,unsafe' | uglifyjs --mangle --output="$TEMP_FILE"
        mv "$TEMP_FILE" "$OUTPUT_PATH"
        echo "✅ JS optimization complete"
    fi
else
    echo "❌ Failed to build kompost.js"
    exit 1
fi

# Build file upload component if it exists
if [[ -f "src/CustomerMedia/FileUpload.elm" ]]; then
    echo "🛠️  Building FileUpload.elm -> fileupload.js..."
    UPLOAD_OUTPUT="$OLDPWD/public/elm/fileupload.js"
    
    # Try optimized build for file upload component
    if elm make src/CustomerMedia/FileUpload.elm --output="$UPLOAD_OUTPUT" --optimize 2>/dev/null; then
        echo "✅ FileUpload optimized build successful"
    else
        echo "⚠️  FileUpload optimization failed, building debug version..."
        elm make src/CustomerMedia/FileUpload.elm --output="$UPLOAD_OUTPUT"
    fi
    
    if [[ $? -eq 0 ]]; then
        echo "✅ Elm fileupload.js built successfully"
        
        # Optimize file upload JS too
        if command -v uglifyjs &> /dev/null; then
            TEMP_FILE=$(mktemp)
            uglifyjs "$UPLOAD_OUTPUT" --compress 'pure_funcs=[F2,F3,F4,F5,F6,F7,F8,F9,A2,A3,A4,A5,A6,A7,A8,A9],pure_getters,keep_fargs=false,unsafe_comps,unsafe' | uglifyjs --mangle --output="$TEMP_FILE"
            mv "$TEMP_FILE" "$UPLOAD_OUTPUT"
        fi
    else
        echo "⚠️  Failed to build fileupload.js (non-critical)"
    fi
fi

cd "$OLDPWD"

# Copy any additional assets from Elm project
if [[ -d "$ELM_SOURCE_PATH/release/content" ]]; then
    echo "📦 Copying additional Elm assets..."
    # Copy JS interop files
    find "$ELM_SOURCE_PATH/release/content" -name "*.js" -exec cp {} public/elm/ \; 2>/dev/null || true
    # Copy any CSS files
    find "$ELM_SOURCE_PATH/release/content" -name "*.css" -exec cp {} public/ \; 2>/dev/null || true
fi

# Update the demo to indicate real Elm is now available
cat > public/elm/elm-status.json << EOF
{
  "status": "compiled",
  "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
  "source": "$ELM_SOURCE_PATH",
  "version": "$(cd "$ELM_SOURCE_PATH" && elm --version 2>/dev/null || echo 'unknown')"
}
EOF

# Verify the built files
echo ""
echo "📋 Build Summary:"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
if [[ -f "public/elm/kompost.js" ]]; then
    SIZE=$(du -h public/elm/kompost.js | cut -f1)
    echo "✅ Main editor: public/elm/kompost.js ($SIZE)"
else
    echo "❌ Main editor: NOT BUILT"
fi

if [[ -f "public/elm/fileupload.js" ]]; then
    SIZE=$(du -h public/elm/fileupload.js | cut -f1)
    echo "✅ File upload: public/elm/fileupload.js ($SIZE)"
fi

if [[ -f "public/elm/elm-status.json" ]]; then
    echo "✅ Status file: public/elm/elm-status.json"
fi

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "🎯 Elm Integration Complete!"
echo ""
echo "🚀 Next Steps:"
echo "1. Start React development server:"
echo "   npm start"
echo ""
echo "2. Test the integration:"
echo "   • Visit http://localhost:3000"
echo "   • Sign in with Google (Firebase)"
echo "   • Navigate to /edit/new"
echo "   • Elm editor should load with Firebase auth context"
echo ""
echo "3. Build for production:"
echo "   npm run build"
echo "   firebase deploy --only hosting"
echo ""
echo "🔧 Integration Features:"
echo "• Elm runs inside Firebase authenticated React shell"
echo "• User context passed via flags (no Elm auth needed)"
echo "• React-Elm communication via ports"
echo "• CouchDB-compatible API configuration"
echo ""
echo "✅ Ready for komposition editing!"