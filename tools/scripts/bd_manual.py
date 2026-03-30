#!/usr/bin/env python3
"""
Build Detective: Manual Analysis and CI Integration

Comprehensive build and repository analysis tool for CI/PR validation.
"""

import argparse
import subprocess
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent))
from bd_lost_files import LostFilesDetector

class BuildDetective:
    def __init__(self, repo=None, pr_number=None):
        self.repo = repo
        self.pr_number = pr_number

    def run_ci_analysis(self):
        """Comprehensive CI analysis including lost files detection."""
        print("🕵️ Build Detective: Comprehensive CI Analysis")
        
        # Lost Files Detection
        lost_files_detector = LostFilesDetector(pr_number=self.pr_number)
        lost_files = lost_files_detector.detect_lost_files()
        
        if lost_files:
            print("\n🚨 Lost Files Detected:")
            lost_files_detector.print_report()
        
        # Additional CI checks can be added here

def main():
    parser = argparse.ArgumentParser(description='Build Detective: Manual CI Analysis')
    parser.add_argument('--repo', help='GitHub repository to analyze')
    parser.add_argument('--pr', help='Pull Request number to analyze')
    
    args = parser.parse_args()

    detective = BuildDetective(repo=args.repo, pr_number=args.pr)
    detective.run_ci_analysis()

if __name__ == '__main__':
    main()
