"""
Deterministic ID Generator for FFMPEG MCP Server

This module provides deterministic file ID generation to enable cache persistence
across server restarts and predictable file naming for effect operations.
"""

import hashlib
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
import re


class DeterministicIDGenerator:
    """Generate deterministic, content-based file IDs for cache persistence"""
    
    @staticmethod
    def source_file_id(filename: str) -> str:
        """
        Generate deterministic ID for source files based on filename
        
        Args:
            filename: Original filename (e.g., "lookin.mp4", "Subnautic Measures.flac")
            
        Returns:
            Deterministic ID (e.g., "src_lookin_mp4", "src_subnautic_measures_flac")
        """
        # Normalize filename: lowercase, replace special chars with underscores
        normalized = re.sub(r'[^a-zA-Z0-9]', '_', filename.lower())
        # Remove consecutive underscores and trailing/leading ones
        normalized = re.sub(r'_+', '_', normalized).strip('_')
        
        return f"src_{normalized}"
    
    @staticmethod
    def effect_file_id(input_ids: List[str], operation: str, params: Dict[str, Any]) -> str:
        """
        Generate deterministic ID for effect operations
        
        Args:
            input_ids: List of input file IDs
            operation: Operation name (e.g., "trim", "concatenate_simple")
            params: Operation parameters
            
        Returns:
            Deterministic effect ID (e.g., "effect_trim_1a2b3c4d")
        """
        # Sort inputs and params for consistency
        sorted_inputs = sorted(input_ids)
        sorted_params = sorted(params.items()) if params else []
        
        # Create content string for hashing
        content = {
            "inputs": sorted_inputs,
            "operation": operation,
            "params": sorted_params
        }
        content_str = json.dumps(content, sort_keys=True, separators=(',', ':'))
        
        # Generate hash
        hash_hex = hashlib.sha256(content_str.encode('utf-8')).hexdigest()[:8]
        
        return f"effect_{operation}_{hash_hex}"
    
    @staticmethod
    def temp_file_path(file_id: str, operation: str, params: Dict[str, Any], 
                      extension: str = "mp4") -> str:
        """
        Generate predictable temp file paths for better organization
        
        Args:
            file_id: Deterministic file ID
            operation: Operation name
            params: Operation parameters
            extension: File extension
            
        Returns:
            Predictable file path
        """
        # Create readable parameter string
        param_parts = []
        for key, value in sorted(params.items()):
            # Sanitize parameter values for filename
            safe_value = str(value).replace('.', 'p').replace(' ', '')
            param_parts.append(f"{key}{safe_value}")
        
        param_str = "_".join(param_parts) if param_parts else "default"
        
        # Limit filename length while keeping readability
        if len(param_str) > 50:
            param_hash = hashlib.md5(param_str.encode()).hexdigest()[:6]
            param_str = f"params_{param_hash}"
        
        return f"/tmp/music/temp/{operation}_{file_id}_{param_str}.{extension}"
    
    @staticmethod
    def metadata_file_path(file_id: str, metadata_type: str) -> str:
        """
        Generate metadata file paths
        
        Args:
            file_id: Source or effect file ID
            metadata_type: Type of metadata (e.g., "analysis", "speech", "properties")
            
        Returns:
            Metadata file path
        """
        return f"/tmp/music/metadata/{file_id}_{metadata_type}.json"
    
    @staticmethod
    def validate_deterministic_naming():
        """
        Validate that deterministic naming produces consistent results
        
        Returns:
            Dict with validation results and examples
        """
        # Test cases for validation
        test_cases = [
            {
                "filename": "lookin.mp4",
                "expected_id": "src_lookin_mp4"
            },
            {
                "filename": "Subnautic Measures.flac", 
                "expected_id": "src_subnautic_measures_flac"
            },
            {
                "filename": "What+The+FSCK+do+Developers+do+-+JavaZone.mp3",
                "expected_id": "src_what_the_fsck_do_developers_do_javazone_mp3"
            }
        ]
        
        effect_test_cases = [
            {
                "inputs": ["src_lookin_mp4"],
                "operation": "trim",
                "params": {"start": 0, "duration": 4},
                "expected_pattern": "effect_trim_"
            },
            {
                "inputs": ["effect_trim_1a2b3c4d", "effect_trim_5e6f7g8h"],
                "operation": "concatenate_simple",
                "params": {"second_video": "effect_trim_5e6f7g8h"},
                "expected_pattern": "effect_concatenate_simple_"
            }
        ]
        
        results = {
            "source_file_tests": [],
            "effect_tests": [],
            "deterministic_check": True
        }
        
        # Test source file naming
        for test in test_cases:
            result_id = DeterministicIDGenerator.source_file_id(test["filename"])
            results["source_file_tests"].append({
                "filename": test["filename"],
                "generated_id": result_id,
                "expected_id": test["expected_id"],
                "matches": result_id == test["expected_id"]
            })
            
            if result_id != test["expected_id"]:
                results["deterministic_check"] = False
        
        # Test effect naming consistency (run twice to ensure determinism)
        for test in effect_test_cases:
            id1 = DeterministicIDGenerator.effect_file_id(
                test["inputs"], test["operation"], test["params"]
            )
            id2 = DeterministicIDGenerator.effect_file_id(
                test["inputs"], test["operation"], test["params"]
            )
            
            results["effect_tests"].append({
                "inputs": test["inputs"],
                "operation": test["operation"],
                "params": test["params"],
                "generated_id": id1,
                "consistent": id1 == id2,
                "matches_pattern": id1.startswith(test["expected_pattern"])
            })
            
            if id1 != id2:
                results["deterministic_check"] = False
        
        return results


class CacheKeyGenerator:
    """Generate cache keys for different types of cached data"""
    
    @staticmethod
    def content_analysis_key(file_id: str) -> str:
        """Generate cache key for video content analysis"""
        return f"analysis_{file_id}"
    
    @staticmethod
    def speech_detection_key(file_id: str, params: Dict[str, Any]) -> str:
        """Generate cache key for speech detection results"""
        param_hash = hashlib.md5(
            json.dumps(params, sort_keys=True).encode()
        ).hexdigest()[:8]
        return f"speech_{file_id}_{param_hash}"
    
    @staticmethod
    def properties_cache_key(file_id: str) -> str:
        """Generate cache key for file properties"""
        return f"props_{file_id}"
    
    @staticmethod
    def komposition_key(title: str, params: Dict[str, Any]) -> str:
        """Generate cache key for komposition files"""
        title_clean = re.sub(r'[^a-zA-Z0-9]', '_', title.lower())
        param_hash = hashlib.md5(
            json.dumps(params, sort_keys=True).encode()
        ).hexdigest()[:8]
        return f"komp_{title_clean}_{param_hash}"


# Example usage and validation
if __name__ == "__main__":
    # Validate deterministic naming
    validation = DeterministicIDGenerator.validate_deterministic_naming()
    
    print("Deterministic ID Generator Validation")
    print("=" * 40)
    print(f"Overall deterministic check: {validation['deterministic_check']}")
    
    print("\nSource file tests:")
    for test in validation["source_file_tests"]:
        status = "✅" if test["matches"] else "❌"
        print(f"{status} {test['filename']} -> {test['generated_id']}")
    
    print("\nEffect tests:")
    for test in validation["effect_tests"]:
        status = "✅" if test["consistent"] and test["matches_pattern"] else "❌"
        print(f"{status} {test['operation']} -> {test['generated_id']}")
    
    print("\nExample temp file paths:")
    examples = [
        ("src_lookin_mp4", "trim", {"start": 0, "duration": 4}),
        ("effect_trim_1a2b3c4d", "concatenate_simple", {"second_video": "effect_trim_5e6f7g8h"}),
    ]
    
    for file_id, operation, params in examples:
        path = DeterministicIDGenerator.temp_file_path(file_id, operation, params)
        print(f"  {operation}: {path}")