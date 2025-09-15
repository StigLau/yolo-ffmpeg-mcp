
Repository Structure Changes

Current: yolo-ffmpeg-mcp/haiku-mcp-ts/
New: https://github.com/kompo-ai/haiku-mcp-server (or similar)

This means we'd need to:
1. Create new repository
2. Move all files from haiku-mcp-ts/
3. Update all internal references

CI/CD Changes

Current CI: .github/workflows/haiku-mcp-publish.yml in yolo-ffmpeg-mcp
New CI: Would be in the new repository's .github/workflows/

The CI would need changes:
- Remove the working-directory: ./haiku-mcp-ts since it would be root
- Update paths to not reference haiku-mcp-ts subdirectory
- GitHub Packages would still work the same way
- But the repository URL in package.json would change

Consumer Project Changes

YOLO-FFMPEG-MCP:
- Currently: Local import from ./haiku-mcp-ts/
- After: Package import from @kompo/haiku-mcp-server
- This change is already planned regardless of separate repo

KOMPO.AI:
- Would install from GitHub Packages same way
- No difference for them

Package Publishing

GitHub Packages:
- Would come from new repository
- Need to configure GitHub Packages for new repo
- Organization scope (@kompo) would remain the same

Development Workflow

Standalone Development:
- Developers could clone just the haiku-mcp-server repo
- Faster clones, focused development
- Independent versioning and releases

Cross-Project Coordination:
- Would need to coordinate changes between repos
- Testing integration would be more complex
- Shared learnings would need explicit communication

Documentation

CLAUDE.md:

I'll need to revise documentation to reflect the standalone nature of the project. The current documentation is tightly coupled with the parent project, so I'll strip out any contextual references to yolo-ffmpeg-mcp. The focus will be
on clear, project-specific guidelines and setup instructions.

README.md:
Comprehensive documentation overhaul is necessary. I'll remove all parent project context, update installation instructions, and clarify contribution guidelines to match the new independent repository structure.

Let me structure this analysis properly.

● Repository Migration Analysis: haiku-mcp-ts → Standalone GitHub Project

1. New Repository Structure

https://github.com/kompo-ai/haiku-mcp-server/
├── .github/workflows/          # Moved from yolo-ffmpeg-mcp
│   └── publish.yml            # Updated paths (no working-directory)
├── src/                       # Same structure
├── examples/                  # Same structure
├── package.json              # Updated repository URL
├── CLAUDE.md                 # Updated for standalone context
├── README.md                 # Remove parent project references
└── bun.lockb                 # Same

2. CI/CD Pipeline Changes

✻ Thinking…

Let me provide a comprehensive analysis of what needs to change.

● Current CI Issues to Fix:
# REMOVE these lines (no longer in subdirectory):
defaults:
run:
working-directory: ./haiku-mcp-ts

# REMOVE path filters:
paths:
- 'haiku-mcp-ts/**'

GitHub Packages Setup:
- Configure new repository for GitHub Packages publishing
- Update package.json repository URL
- Transfer organization permissions (@kompo scope)

3. Consumer Project Impact

✻ Thinking…

Now let me think about the consumer impacts and package strategy.

● YOLO-FFMPEG-MCP Changes:
// BEFORE (current local import):
import { HaikuMCPServer } from './haiku-mcp-ts/src/server.js';

// AFTER (package import - same whether separate repo or not):
import { HaikuMCPServer } from '@kompo/haiku-mcp-server';

KOMPO.AI Integration:
- No changes needed - still installs from GitHub Packages
- Same @kompo/haiku-mcp-server package name

4. Package Publishing Strategy

✻ Thinking…

Let me finish the package publishing strategy analysis.

● Advantages of Separate Repo:
- Faster Development: Clone only what you need
- Independent Releases: Version without coordinating with yolo-ffmpeg-mcp
- Focused Issues: Package-specific bug reports and feature requests
- Better Discovery: Easier to find and contribute to standalone package

Challenges:
- Integration Testing: Harder to test yolo-ffmpeg-mcp + haiku-mcp-server together
- Shared Learning: Need explicit process to share insights between projects
- Coordination Overhead: Breaking changes require coordination across repos

5. Migration Process

Step 1: Repository Setup
# Create new repo: kompo-ai/haiku-mcp-server
# Copy all files from yolo-ffmpeg-mcp/haiku-mcp-ts/
# Update package.json repository field

Step 2: CI Updates
# Remove working-directory references
# Remove haiku-mcp-ts path filters
# Configure GitHub Packages for new repo

Step 3: Documentation Updates
# CLAUDE.md: Remove yolo-ffmpeg-mcp parent references
# README.md: Focus on standalone usage
# Add CONTRIBUTING.md for new repo

Step 4: Consumer Updates
# yolo-ffmpeg-mcp: Switch to package import
# kompo.ai: No changes needed
# Update integration tests
