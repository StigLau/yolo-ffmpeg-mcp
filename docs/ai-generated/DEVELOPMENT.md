# Kompost Mixer Development Guide

## Quick Start

```bash
# See all available commands
make help

# Start development
make dev

# Quick deploy workflow
make commit MSG="your changes" && make push && make deploy
```

## Common Development Tasks

### 🚀 **Development Server**
```bash
make dev          # Start dev server
make dev-clean    # Kill existing and restart
make restart      # Alias for dev-clean
```

### 🏗️ **Building & Deployment**
```bash
make build        # Build for production
make deploy       # Deploy to Firebase
make deploy-force # Re-auth and deploy
```

### 📝 **Git Operations**
```bash
make status                        # Show git status
make commit MSG="your message"     # Quick commit
make push                          # Push current branch
make backup NAME="backup-name"     # Create backup branch
make branch NAME="feature-name"    # Create new feature branch
```

### 🧹 **Utilities**
```bash
make clean        # Clean and reinstall dependencies
make logs         # Show Firebase logs
make elm-build    # Build ELM application
make version      # Bump version number
```

## Environment Setup

1. **Copy environment template:**
   ```bash
   cp env.example .env.local
   ```

2. **Update with your Firebase config:**
   - Edit `.env.local` with your project settings
   - Use kompost-mixer or kompostedit project settings

3. **Restart server to pick up changes:**
   ```bash
   make dev-clean
   ```

## Workflow Examples

### 🔄 **Feature Development**
```bash
make branch NAME="feature/new-feature"  # Create feature branch
make dev                                # Start development
# ... make changes ...
make commit MSG="Add new feature"       # Commit changes
make push                               # Push to remote
make deploy                             # Deploy to Firebase
```

### 💾 **Create Backup Before Major Changes**
```bash
make backup NAME="working-elm-v2"       # Create backup
make branch NAME="feature/major-change" # Start new feature
```

### 🚀 **Quick Deploy**
```bash
make status                             # Check current state
make commit MSG="Fix UI issue"          # Commit changes
make push                               # Push to remote
make deploy                             # Deploy to Firebase
```

## ELM Integration

If you have the ELM source available:

```bash
make elm-build    # Compiles ELM to public/elm/kompost.js
```

The Makefile expects ELM source in `elm-kompostedit/` directory.

## Firebase Projects

The app can work with two Firebase projects:

- **kompost-mixer**: Main production project
- **kompostedit**: Development/testing project

Switch by updating `.env.local` and restarting with `make dev-clean`.

## Build Information

The app automatically includes build information:
- Timestamp (auto-generated)
- Version (from package.json)
- Git commit hash
- Branch name

Visible in console logs and footer.

## Troubleshooting

### Port Issues
```bash
make dev-clean    # Kills existing server and restarts
```

### Clean Install
```bash
make clean        # Removes node_modules and reinstalls
```

### Firebase Auth Issues
```bash
make deploy-force # Re-authenticates and deploys
```

### Build Version Confusion
Check the console logs and footer for build timestamp to verify you're running the latest code.