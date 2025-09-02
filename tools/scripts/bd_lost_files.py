#!/usr/bin/env python3
"""
Build Detective: Lost Files Detection Module

Detects and reports files that existed in previous commits/PRs but are now missing.
Helps identify potential build/test failures due to missing files.
"""

import os
import sys
import argparse
import subprocess
from typing import List, Dict, Optional

class LostFilesDetector:
    def __init__(self, pr_number: Optional[str] = None, since_commit: Optional[str] = None):
        self.pr_number = pr_number
        self.since_commit = since_commit
        self.lost_files: Dict[str, Dict] = {}

    def run_git_command(self, command: List[str]) -> str:
        """Execute a git command and return its output."""
        try:
            result = subprocess.run(command, capture_output=True, text=True, check=True)
            return result.stdout.strip()
        except subprocess.CalledProcessError as e:
            print(f"Error running git command: {e}", file=sys.stderr)
            return ""

    def get_file_history(self, commit_range: str) -> Dict[str, List[str]]:
        """Get files and their commit history."""
        files_history = {}
        cmd = ['git', 'log', commit_range, '--name-only', '--pretty=format:%H']
        log_output = self.run_git_command(cmd)
        
        current_commit = None
        for line in log_output.split('\n'):
            if line.strip():
                if len(line.strip()) == 40 and all(c in '0123456789abcdef' for c in line.strip()):
                    # This is a commit hash
                    current_commit = line.strip()
                elif current_commit and line.strip():
                    # This is a file path
                    files_history.setdefault(line.strip(), []).append(current_commit)
        
        return files_history

    def detect_lost_files(self) -> Dict[str, Dict]:
        """Detect files that existed in previous commits but are now missing."""
        # Determine commit range
        if self.pr_number:
            commit_range = f'origin/main..HEAD'
        elif self.since_commit:
            commit_range = f'{self.since_commit}..HEAD'
        else:
            commit_range = 'HEAD~10..HEAD'  # Last 10 commits by default

        files_history = self.get_file_history(commit_range)

        for filepath, commits in files_history.items():
            if not os.path.exists(filepath):
                self.lost_files[filepath] = {
                    'last_seen_commits': commits[:3],  # Last 3 commits for context
                    'last_seen_commit': commits[0],
                    'restoration_command': f'git show {commits[0]}:{filepath} > {filepath}'
                }

        return self.lost_files

    def print_report(self):
        """Print a detailed report of lost files."""
        if not self.lost_files:
            print("✅ No lost files detected.")
            return

        print(f"🚨 Lost Files Detected (Total: {len(self.lost_files)}):\n")
        for filepath, details in self.lost_files.items():
            print(f"📄 File: {filepath}")
            print(f"   Last Seen Commits: {', '.join(details['last_seen_commits'])}")
            print(f"   Restoration Command: {details['restoration_command']}\n")

def main():
    parser = argparse.ArgumentParser(description='Build Detective: Lost Files Detection')
    group = parser.add_mutually_exclusive_group()
    group.add_argument('--pr', help='Check for lost files since a specific PR')
    group.add_argument('--since', help='Check for lost files since a specific commit')
    
    args = parser.parse_args()

    detector = LostFilesDetector(
        pr_number=args.pr,
        since_commit=args.since
    )
    
    detector.detect_lost_files()
    detector.print_report()

if __name__ == '__main__':
    main()
