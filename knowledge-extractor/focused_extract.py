#!/usr/bin/env python3
"""
Focused Knowledge Extractor - Quick analysis of specific files
"""

import asyncio
import sys
from pathlib import Path
import subprocess

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))
from knowledge_extractor import HaikuKnowledgeExtractor

async def analyze_main_functions(base_dir: str):
    """Find and analyze Java files with main functions"""
    
    print(f"🔍 Finding Java files with main functions in: {base_dir}")
    
    # Use grep to find files with main functions
    try:
        result = subprocess.run([
            'find', base_dir, '-name', '*.java', 
            '-exec', 'grep', '-l', 'public static void main', '{}', ';'
        ], capture_output=True, text=True)
        
        main_files = [Path(f.strip()) for f in result.stdout.split('\n') if f.strip()]
        
    except Exception as e:
        print(f"❌ Error finding files: {e}")
        return
    
    print(f"📊 Found {len(main_files)} Java files with main functions")
    
    if not main_files:
        return
    
    # Limit to first 5 for demo
    selected_files = main_files[:5]
    print(f"📄 Analyzing first {len(selected_files)} files:")
    
    # Initialize extractor
    output_dir = Path(base_dir) / 'docs' / 'main-analysis' 
    output_dir.mkdir(parents=True, exist_ok=True)
    
    extractor = HaikuKnowledgeExtractor(
        db_path=str(output_dir / 'main_functions.db'),
        output_dir=str(output_dir),
        cost_limit_daily=0.50
    )
    
    results = []
    total_cost = 0
    
    for i, file_path in enumerate(selected_files, 1):
        print(f"⚙️ Processing ({i}/{len(selected_files)}): {file_path.name}")
        try:
            result = await extractor.process_file(file_path)
            if result:
                results.append(result)
                total_cost += result.cost_estimate
                
                # Show main functions found
                main_functions = [e for e in result.entities if e['type'] == 'function' and 'main' in e['name'].lower()]
                if main_functions:
                    print(f"   ✅ Found main function: {main_functions[0]['name']}")
                else:
                    print(f"   ⚠️ No main function entity extracted")
                    
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    print(f"\n📊 Summary:")
    print(f"   Files analyzed: {len(results)}")
    print(f"   Total cost: ${total_cost:.4f}")
    print(f"   Main functions found: {sum(1 for r in results for e in r.entities if e['type'] == 'function' and 'main' in e['name'].lower())}")
    
    # Quick summary of entry points
    print(f"\n🚀 Entry Points Discovered:")
    for result in results:
        file_name = Path(result.file_path).name
        main_funcs = [e for e in result.entities if e['type'] == 'function' and 'main' in e['name'].lower()]
        if main_funcs:
            print(f"   • {file_name}: {main_funcs[0]['name']}")
            if main_funcs[0].get('description'):
                print(f"     Description: {main_funcs[0]['description']}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python focused_extract.py <directory>")
        sys.exit(1)
    
    asyncio.run(analyze_main_functions(sys.argv[1]))