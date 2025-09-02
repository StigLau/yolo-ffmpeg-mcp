# Build Detective: Lost Files Detection

## Overview
The `bd_lost_files.py` script helps identify files that existed in previous commits but are now missing from the current working directory. This helps prevent build and test failures caused by silently disappeared files.

## Usage Patterns

### Check Lost Files Since Last PR
```bash
python3 tools/scripts/bd_lost_files.py --pr CURRENT_PR_NUMBER
```

### Check Lost Files Since Specific Commit
```bash
python3 tools/scripts/bd_lost_files.py --since COMMIT_HASH
```

### Features
- 🕵️ Detect files missing from current working directory
- 🔍 Trace last commits where files were present
- 🔧 Provide restoration commands for lost files

## Example Output
```
🚨 Lost Files Detected (Total: 2):

📄 File: tests/integration/test_music_video_workflow_ci.py
   Last Seen Commits: 7b3af44, 9c2de11
   Restoration Command: git show 7b3af44:tests/integration/test_music_video_workflow_ci.py > tests/integration/test_music_video_workflow_ci.py

📄 File: scripts/bd_local_ci.py
   Last Seen Commits: a1b2c3d, e4f5g6h
   Restoration Command: git show a1b2c3d:scripts/bd_local_ci.py > scripts/bd_local_ci.py
```

## Integration
- Automatically run during `bd_manual.py` PR analysis
- Part of standard Build Detective validation workflows
- Helps prevent silent file loss during development

## Best Practices
1. Always review lost files before restoration
2. Understand why files disappeared
3. Consider if files are genuinely no longer needed
4. Use restoration commands with caution
