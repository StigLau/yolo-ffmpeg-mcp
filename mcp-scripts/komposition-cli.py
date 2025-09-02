#!/usr/bin/env python3
"""
Komposition CLI Tool
Command-line interface for komposition processing
"""

import argparse
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from komposition.converter import KompositionConverter
from komposition.processor import KompositionProcessor


def main():
    parser = argparse.ArgumentParser(description='Komposition Processing CLI')
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Convert command
    convert_parser = subparsers.add_parser('convert', help='Convert between MD and JSON formats')
    convert_parser.add_argument('input', help='Input file (.md or .json)')
    convert_parser.add_argument('-o', '--output', help='Output file (auto-detected if not specified)')
    
    # Process command  
    process_parser = subparsers.add_parser('process', help='Generate FFMPEG command from komposition')
    process_parser.add_argument('komposition', help='Komposition file (.md)')
    process_parser.add_argument('-o', '--output', required=True, help='Output video file')
    process_parser.add_argument('--execute', action='store_true', help='Execute FFMPEG command')
    
    # Validate command
    validate_parser = subparsers.add_parser('validate', help='Validate komposition file')
    validate_parser.add_argument('komposition', help='Komposition file (.md)')
    
    # Test command
    test_parser = subparsers.add_parser('test', help='Test conversion with example')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
        
    try:
        if args.command == 'convert':
            converter = KompositionConverter()
            result = converter.convert_file(args.input, args.output)
            print(f"✅ {result}")
            
        elif args.command == 'process':
            processor = KompositionProcessor()
            command = processor.process_komposition_file(args.komposition, args.output)
            print(f"📋 Generated FFMPEG command:")
            print(command)
            
            if args.execute:
                import subprocess
                print(f"⚡ Executing FFMPEG...")
                result = subprocess.run(command, shell=True, capture_output=True, text=True)
                if result.returncode == 0:
                    print(f"✅ Video generated: {args.output}")
                else:
                    print(f"❌ FFMPEG failed: {result.stderr}")
                    
        elif args.command == 'validate':
            processor = KompositionProcessor()
            result = processor.validate_komposition(args.komposition)
            
            if result['valid']:
                print("✅ Komposition is valid")
                print(f"   Segments: {result['segments']}")
                print(f"   Duration: {result['total_duration']:.1f}s")
                print(f"   Resolution: {result['config']['resolution']}")
                print(f"   BPM: {result['config']['bpm']}")
            else:
                print("❌ Komposition has issues:")
                for issue in result.get('issues', []):
                    print(f"   • {issue}")
                    
            if result.get('warnings'):
                print("⚠️  Warnings:")
                for warning in result['warnings']:
                    print(f"   • {warning}")
                    
        elif args.command == 'test':
            # Test with example file
            example_file = Path(__file__).parent.parent / "komposition-example.md"
            if example_file.exists():
                print("🧪 Testing komposition processing...")
                
                # Test validation
                processor = KompositionProcessor()
                result = processor.validate_komposition(str(example_file))
                print(f"Validation: {'✅ Valid' if result['valid'] else '❌ Invalid'}")
                
                # Test conversion
                converter = KompositionConverter()
                json_file = "test-output.json"
                converter.convert_file(str(example_file), json_file)
                print(f"✅ Converted to JSON: {json_file}")
                
                # Test processing
                command = processor.process_komposition_file(str(example_file), "test-output.mp4")
                print(f"✅ Generated FFMPEG command ({len(command)} chars)")
                print(f"Command preview: {command[:100]}...")
                
            else:
                print("❌ Example file not found")
                
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()