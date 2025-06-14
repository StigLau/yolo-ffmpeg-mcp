#!/usr/bin/env python3
"""
Test script for the resource management system
"""

import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from deterministic_id_generator import DeterministicIDGenerator
from resource_manager import ResourceRegistry, CacheManager, ResourceRecovery


def test_resource_system():
    """Test the complete resource management system"""
    print("Testing Resource Management System")
    print("=" * 50)
    
    # Initialize system
    registry = ResourceRegistry("/tmp/music/metadata/test_file_registry.json")
    cache_manager = CacheManager(registry)
    recovery = ResourceRecovery(registry)
    
    # Test 1: Scan and rebuild registry
    print("\n1. Scanning filesystem to rebuild registry...")
    recovery.scan_and_rebuild_registry()
    
    # Test 2: Validate deterministic ID generation
    print("\n2. Testing deterministic ID generation...")
    test_files = [
        "lookin.mp4",
        "Subnautic Measures.flac", 
        "PXL_20250306_132546255.mp4"
    ]
    
    for filename in test_files:
        file_id = DeterministicIDGenerator.source_file_id(filename)
        print(f"  {filename} -> {file_id}")
    
    # Test 3: Test effect ID generation
    print("\n3. Testing effect ID generation...")
    effect_id = DeterministicIDGenerator.effect_file_id(
        ["src_lookin_mp4"], 
        "trim", 
        {"start": 0, "duration": 4}
    )
    print(f"  trim effect ID: {effect_id}")
    
    # Test 4: Check cache functionality
    print("\n4. Testing cache functionality...")
    cached_result = registry.check_effect_cache(
        ["src_lookin_mp4"], 
        "trim", 
        {"start": 0, "duration": 4}
    )
    print(f"  Cache result for trim operation: {cached_result}")
    
    # Test 5: Validate resource integrity
    print("\n5. Validating resource integrity...")
    missing = recovery.validate_resource_integrity()
    
    for category, files in missing.items():
        if files:
            print(f"  Missing {category}: {files}")
        else:
            print(f"  ✅ All {category} are valid")
    
    # Test 6: Check for source file changes
    print("\n6. Checking for source file changes...")
    cache_manager.check_source_file_changes()
    
    # Test 7: Display registry statistics
    print("\n7. Registry Statistics:")
    print(f"  Source files: {len(registry.source_files)}")
    print(f"  Generated files: {len(registry.generated_files)}")
    print(f"  Metadata files: {len(registry.metadata_files)}")
    print(f"  Operations recorded: {len(registry.operations)}")
    print(f"  Dependencies tracked: {len(registry.dependencies)}")
    
    # Test 8: Show actual files found
    print("\n8. Actual files in registry:")
    for file_id, resource in registry.source_files.items():
        print(f"  📁 {file_id}: {Path(resource.path).name} ({resource.size} bytes)")
    
    # Test 9: Demonstrate temp file path generation
    print("\n9. Example temp file paths:")
    examples = [
        ("src_lookin_mp4", "trim", {"start": 0, "duration": 4}),
        ("effect_trim_12345678", "concatenate_simple", {"second_video": "effect_trim_87654321"}),
    ]
    
    for file_id, operation, params in examples:
        temp_path = DeterministicIDGenerator.temp_file_path(file_id, operation, params)
        print(f"  {operation}: {temp_path}")
    
    print("\n✅ Resource system test completed!")
    return True


if __name__ == "__main__":
    try:
        test_resource_system()
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)