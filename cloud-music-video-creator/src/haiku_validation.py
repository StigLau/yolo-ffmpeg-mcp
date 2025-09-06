#!/usr/bin/env python3
"""
Haiku Processing Validation and Error Analysis
Pre-validates komposition data and analyzes Haiku failures for improvement.
"""

import json
import logging
import os
import re
from typing import Dict, List, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class HaikuValidationError(Exception):
    """Raised when komposition validation fails."""
    pass


class HaikuValidator:
    """
    Validates komposition data before sending to Haiku and analyzes failures.
    Prevents Haiku from defaulting to synthetic content when real content should be used.
    """
    
    def __init__(self):
        self.required_media_dirs = [
            "/tmp/music/source",
            "/tmp/music",
            "/tmp/kompo"
        ]
    
    def validate_komposition_pre_processing(self, komposition_md: str) -> Dict[str, Any]:
        """
        Pre-validate komposition before sending to Haiku.
        
        Args:
            komposition_md: Markdown komposition content
            
        Returns:
            Validation result with success status and details
            
        Raises:
            HaikuValidationError: If validation fails and processing should stop
        """
        validation = {
            "success": True,
            "warnings": [],
            "errors": [],
            "media_files": [],
            "validation_details": {}
        }
        
        # Add komposition quality validation (EXPERIMENTAL - may be rolled back)
        quality_validation = self.validate_komposition_quality(komposition_md)
        if quality_validation["needs_improvement"]:
            validation["warnings"].extend([f"Quality issue: {issue}" for issue in quality_validation["issues"]])
            validation["validation_details"]["quality_issues"] = quality_validation["issues"]
        
        try:
            # 1. Extract media file references
            media_files = self._extract_media_references(komposition_md)
            validation["media_files"] = media_files
            validation["validation_details"]["media_count"] = len(media_files)
            
            if not media_files:
                validation["errors"].append("No media files found in komposition")
                validation["success"] = False
                return validation
            
            # 2. Validate media file availability
            missing_files = []
            available_files = []
            
            for media_file in media_files:
                file_path = media_file["full_path"]
                if os.path.exists(file_path):
                    file_size = os.path.getsize(file_path)
                    media_file["file_size"] = file_size
                    available_files.append(media_file)
                    
                    # Check for suspicious file sizes
                    if file_size < 1024:  # Less than 1KB
                        validation["warnings"].append(f"Media file {media_file['filename']} is very small ({file_size} bytes)")
                else:
                    missing_files.append(media_file)
            
            validation["validation_details"]["available_files"] = available_files
            validation["validation_details"]["missing_files"] = missing_files
            
            # 3. Check for critical validation failures
            if missing_files:
                error_msg = f"Missing media files: {[f['filename'] for f in missing_files]}"
                validation["errors"].append(error_msg)
                validation["success"] = False
                
                # Suggest available alternatives
                alternatives = self._find_alternative_media_files()
                if alternatives:
                    validation["validation_details"]["suggested_alternatives"] = alternatives
                    validation["warnings"].append(f"Available alternatives: {[f['name'] for f in alternatives]}")
            
            # 4. Validate komposition structure
            structure_issues = self._validate_komposition_structure(komposition_md)
            if structure_issues:
                validation["warnings"].extend(structure_issues)
            
            # 5. Check for Haiku processing requirements
            haiku_issues = self._validate_haiku_requirements(komposition_md)
            if haiku_issues:
                validation["errors"].extend(haiku_issues)
                validation["success"] = False
            
            # 6. Final validation decision
            if not validation["success"]:
                error_summary = "; ".join(validation["errors"])
                raise HaikuValidationError(f"Komposition validation failed: {error_summary}")
            
            logger.info(f"✅ Komposition validation passed: {len(available_files)} media files available")
            return validation
            
        except Exception as e:
            logger.error(f"Validation error: {e}")
            validation["success"] = False
            validation["errors"].append(str(e))
            return validation
    
    def _extract_media_references(self, komposition_md: str) -> List[Dict[str, str]]:
        """Extract media file references from komposition markdown."""
        media_files = []
        
        # Pattern to match media references like "media_001 (filename.mp4)"
        media_pattern = r'media_(\w+)\s*\(([^)]+\.(mp4|avi|mov|mkv|mp3|wav|flac|m4a))\)'
        
        matches = re.findall(media_pattern, komposition_md, re.IGNORECASE)
        
        for media_id, filename, ext in matches:
            # Try multiple potential paths
            potential_paths = [
                f"/tmp/music/source/{filename}",
                f"/tmp/music/{filename}",
                f"/tmp/kompo/{filename}",
                f"/tmp/{filename}"
            ]
            
            for path in potential_paths:
                if os.path.exists(path):
                    media_files.append({
                        "media_id": f"media_{media_id}",
                        "filename": filename,
                        "extension": ext,
                        "full_path": path,
                        "path_found": True
                    })
                    break
            else:
                # No path found
                media_files.append({
                    "media_id": f"media_{media_id}",
                    "filename": filename,
                    "extension": ext,
                    "full_path": f"/tmp/music/source/{filename}",  # Default expected path
                    "path_found": False
                })
        
        # Remove duplicates while preserving order
        seen = set()
        unique_media = []
        for media in media_files:
            key = (media["filename"], media["full_path"])
            if key not in seen:
                seen.add(key)
                unique_media.append(media)
        
        return unique_media
    
    def validate_komposition_quality(self, komposition_md: str) -> Dict[str, Any]:
        """
        EXPERIMENTAL: Validate komposition creative quality and structure.
        This validation may be rolled back if it's too restrictive.
        
        Args:
            komposition_md: Markdown komposition content
            
        Returns:
            Quality validation result with issues and improvement flag
        """
        issues = []
        
        try:
            # Extract segment sources
            segment_pattern = r'### Segment \d+:.*?\n- \*\*Source\*\*: (.*?)\n'
            segments = re.findall(segment_pattern, komposition_md, re.DOTALL)
            
            if len(segments) > 1:
                # Check for visual variety - all segments using same source
                unique_sources = set(seg.strip() for seg in segments)
                if len(unique_sources) == 1:
                    issues.append("All segments use same media source - lacks visual variety")
            
            # Check crossfade timing math
            duration_match = re.search(r'\*\*Duration\*\*:\s*(\d+)\s*seconds?', komposition_md)
            crossfade_matches = re.findall(r'Crossfade.*?(\d+)-second', komposition_md)
            
            if duration_match and crossfade_matches and segments:
                total_duration = int(duration_match.group(1))
                segment_count = len(segments)
                crossfade_time = int(crossfade_matches[0]) if crossfade_matches else 0
                
                if segment_count > 1:
                    segment_duration = total_duration / segment_count
                    if crossfade_time >= segment_duration * 0.4:  # More than 40% of segment
                        issues.append(f"Crossfade time ({crossfade_time}s) too long for {segment_duration:.1f}s segments")
            
            # Check for effect variety
            effect_pattern = r'- \*\*Effects\*\*: (.*?)\n'
            effects = re.findall(effect_pattern, komposition_md)
            if len(effects) > 2:
                unique_effects = set(eff.strip() for eff in effects)
                if len(unique_effects) == 1:
                    issues.append("All segments use identical effects - consider progression or variety")
            
        except Exception as e:
            logger.warning(f"Quality validation failed: {e}")
            # Don't fail validation due to parsing issues
        
        return {
            "issues": issues,
            "needs_improvement": len(issues) > 0,
            "experimental": True
        }
    
    def _find_alternative_media_files(self) -> List[Dict[str, str]]:
        """Find available media files that could be used as alternatives."""
        alternatives = []
        
        for media_dir in self.required_media_dirs:
            if not os.path.exists(media_dir):
                continue
                
            try:
                for file_path in Path(media_dir).rglob("*"):
                    if file_path.is_file() and file_path.suffix.lower() in ['.mp4', '.avi', '.mov', '.mkv', '.mp3', '.wav', '.flac', '.m4a']:
                        alternatives.append({
                            "name": file_path.name,
                            "path": str(file_path),
                            "size": file_path.stat().st_size,
                            "type": "video" if file_path.suffix.lower() in ['.mp4', '.avi', '.mov', '.mkv'] else "audio"
                        })
            except Exception as e:
                logger.warning(f"Error scanning {media_dir}: {e}")
        
        # Sort by size (larger files first, more likely to be real content)
        alternatives.sort(key=lambda x: x["size"], reverse=True)
        return alternatives[:5]  # Return top 5 alternatives
    
    def _validate_komposition_structure(self, komposition_md: str) -> List[str]:
        """Validate komposition markdown structure."""
        issues = []
        
        # Check for required sections
        required_sections = ["Basic Parameters", "Segments"]
        for section in required_sections:
            if section not in komposition_md:
                issues.append(f"Missing required section: {section}")
        
        # Check for BPM specification
        if not re.search(r'\d+\s*BPM', komposition_md, re.IGNORECASE):
            issues.append("BPM not specified - timing may be incorrect")
        
        # Check for duration
        if not re.search(r'\d+\s*seconds?', komposition_md, re.IGNORECASE):
            issues.append("Duration not specified")
        
        return issues
    
    def _validate_haiku_requirements(self, komposition_md: str) -> List[str]:
        """Validate requirements specific to Haiku processing."""
        issues = []
        
        # Check for synthetic content indicators (these suggest Haiku will fall back)
        synthetic_indicators = ["testsrc", "sine=", "generate", "synthetic"]
        for indicator in synthetic_indicators:
            if indicator in komposition_md.lower():
                issues.append(f"Komposition contains synthetic content indicator: {indicator}")
        
        # Validate segment count
        segment_count = len(re.findall(r'### Segment \d+:', komposition_md))
        if segment_count == 0:
            issues.append("No segments found in komposition")
        elif segment_count > 20:
            issues.append(f"Too many segments ({segment_count}) - may overwhelm Haiku processing")
        
        return issues
    
    def analyze_haiku_failure(self, komposition_md: str, haiku_result: Dict[str, Any], 
                            validation_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze Haiku processing failure and provide improvement suggestions.
        
        Args:
            komposition_md: Original komposition markdown
            haiku_result: Result from failed Haiku processing
            validation_result: Pre-validation result
            
        Returns:
            Analysis with failure reasons and improvement suggestions
        """
        analysis = {
            "failure_type": "unknown",
            "root_causes": [],
            "improvement_suggestions": [],
            "gemini_evaluation_prompt": "",
            "severity": "medium"
        }
        
        try:
            # 1. Analyze failure type
            if haiku_result.get("error"):
                if "testsrc" in str(haiku_result.get("error", "")):
                    analysis["failure_type"] = "synthetic_fallback"
                    analysis["severity"] = "high"
                elif "file not found" in str(haiku_result.get("error", "")).lower():
                    analysis["failure_type"] = "missing_media"
                    analysis["severity"] = "high"
                elif "timeout" in str(haiku_result.get("error", "")).lower():
                    analysis["failure_type"] = "processing_timeout"
                    analysis["severity"] = "medium"
                else:
                    analysis["failure_type"] = "processing_error"
                    analysis["severity"] = "medium"
            
            # 2. Check if synthetic content was generated
            commands = haiku_result.get("ffmpeg_commands", [])
            if any("testsrc" in cmd or "sine=" in cmd for cmd in commands):
                analysis["failure_type"] = "synthetic_fallback"
                analysis["severity"] = "high"
                analysis["root_causes"].append("Haiku generated synthetic content instead of using real media files")
            
            # 3. Analyze root causes based on validation
            if not validation_result.get("success"):
                for error in validation_result.get("errors", []):
                    analysis["root_causes"].append(f"Validation error: {error}")
            
            # 4. Generate improvement suggestions
            if analysis["failure_type"] == "synthetic_fallback":
                analysis["improvement_suggestions"].extend([
                    "Ensure media file paths are correct and accessible",
                    "Add explicit file validation before sending to Haiku",
                    "Include full file paths in komposition instead of references",
                    "Verify Haiku MCP server has access to media directories"
                ])
            
            if analysis["failure_type"] == "missing_media":
                available_files = validation_result.get("validation_details", {}).get("available_files", [])
                if available_files:
                    analysis["improvement_suggestions"].append(
                        f"Use available files instead: {[f['filename'] for f in available_files[:3]]}"
                    )
                else:
                    analysis["improvement_suggestions"].append("Upload or provide the required media files")
            
            # 5. Create Gemini evaluation prompt
            analysis["gemini_evaluation_prompt"] = self._create_gemini_evaluation_prompt(
                komposition_md, haiku_result, analysis
            )
            
            return analysis
            
        except Exception as e:
            logger.error(f"Failed to analyze Haiku failure: {e}")
            analysis["root_causes"].append(f"Analysis error: {e}")
            return analysis
    
    def _create_gemini_evaluation_prompt(self, komposition_md: str, haiku_result: Dict[str, Any], 
                                       analysis: Dict[str, Any]) -> str:
        """Create a prompt for Gemini to evaluate and improve the failed processing."""
        
        prompt = f"""## Haiku Processing Failure Analysis

**Failure Type**: {analysis['failure_type']}
**Severity**: {analysis['severity']}

**Original Komposition**:
```markdown
{komposition_md[:1000]}{'...' if len(komposition_md) > 1000 else ''}
```

**Haiku Result**:
```json
{json.dumps(haiku_result, indent=2)[:1000]}{'...' if len(str(haiku_result)) > 1000 else ''}
```

**Root Causes**:
{chr(10).join(f"- {cause}" for cause in analysis['root_causes'])}

**Improvement Suggestions**:
{chr(10).join(f"- {suggestion}" for suggestion in analysis['improvement_suggestions'])}

**Please analyze this failure and provide**:
1. **Corrected Komposition**: A revised komposition that should work better
2. **Processing Strategy**: How to prevent this failure in the future  
3. **User Communication**: How to explain this issue to the user in creative terms (no technical details)

Focus on ensuring real media files are used instead of synthetic content.
"""
        
        return prompt


def validate_before_haiku_processing(komposition_md: str) -> Dict[str, Any]:
    """
    Validate komposition before sending to Haiku processing.
    
    Args:
        komposition_md: Komposition markdown content
        
    Returns:
        Validation result
        
    Raises:
        HaikuValidationError: If validation fails critically
    """
    validator = HaikuValidator()
    return validator.validate_komposition_pre_processing(komposition_md)


def analyze_haiku_processing_failure(komposition_md: str, haiku_result: Dict[str, Any], 
                                   validation_result: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Analyze failed Haiku processing and provide improvement suggestions.
    
    Args:
        komposition_md: Original komposition markdown
        haiku_result: Result from failed Haiku processing
        validation_result: Optional pre-validation result
        
    Returns:
        Analysis with improvement suggestions
    """
    validator = HaikuValidator()
    
    if validation_result is None:
        try:
            validation_result = validator.validate_komposition_pre_processing(komposition_md)
        except HaikuValidationError:
            validation_result = {"success": False, "errors": ["Validation failed"]}
    
    return validator.analyze_haiku_failure(komposition_md, haiku_result, validation_result)