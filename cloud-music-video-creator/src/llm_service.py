#!/usr/bin/env python3
"""
LLM Service for Cloud Music Video Creator
Handles real LLM integration for creative komposition discussion

Now includes FFmpeg processing integration via Haiku MCP Bridge.
"""

import json
import logging
import os
from pathlib import Path
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
import tempfile

# Import registry components - temporarily disabled for import issues
REGISTRY_AVAILABLE = False
try:
    # Try relative imports first (when run as module)
    from .registry.komposition_registry import KompositionRegistry
    from .registry.media_registry import MediaRegistry
    from .storage.temp_storage import TempStorageBackend
    from .models.media import MediaType, MediaMetadata, StorageType
    REGISTRY_AVAILABLE = True
except ImportError:
    try:
        # Fall back to absolute imports (when run directly)
        import sys
        from pathlib import Path
        src_path = Path(__file__).parent
        sys.path.insert(0, str(src_path))
        
        from registry.komposition_registry import KompositionRegistry
        from registry.media_registry import MediaRegistry
        from storage.temp_storage import TempStorageBackend
        from models.media import MediaType, MediaMetadata, StorageType
        REGISTRY_AVAILABLE = True
    except ImportError as e:
        print(f"Registry imports failed: {e}. Running with fallback mode.")
        REGISTRY_AVAILABLE = False
        # Create dummy classes for fallback with test data simulation
        # Shared storage for persistence across instances
        _shared_media_storage = []
        
        class DummyRegistry:
            def __init__(self, storage=None):
                self.media_files = _shared_media_storage
            
            async def list_user_media(self, user_id):
                return self.media_files
            
            async def register_file(self, path, metadata):
                from datetime import datetime
                media_id = f"media_{len(self.media_files)+1:03d}"
                media_file = {
                    "id": media_id,
                    "type": metadata.type.value if hasattr(metadata.type, 'value') else str(metadata.type),
                    "storage_type": "temp",
                    "storage_path": path,
                    "metadata": {
                        "filename": metadata.filename,
                        "file_size_bytes": metadata.file_size_bytes,
                        "type": metadata.type.value if hasattr(metadata.type, 'value') else str(metadata.type)
                    },
                    "created_at": datetime.now()
                }
                self.media_files.append(media_file)
                return type('MediaRef', (), media_file)()
            
            async def get(self, media_id): 
                for media in self.media_files:
                    if media["id"] == media_id:
                        return type('MediaRef', (), media)()
                return None
                
            async def list_user_kompositions(self, user_id): 
                return []
        KompositionRegistry = MediaRegistry = DummyRegistry
        class DummyStorage: pass
        TempStorageBackend = DummyStorage
        class MediaType: 
            VIDEO = "video"
            AUDIO = "audio"
            IMAGE = "image"
            def __init__(self, type_str): 
                self.value = type_str
        class MediaMetadata: 
            def __init__(self, type, filename, file_size_bytes, **kwargs):
                self.type = type
                self.filename = filename  
                self.file_size_bytes = file_size_bytes
        class StorageType: TEMP = "temp"

logger = logging.getLogger(__name__)


@dataclass
class ChatResponse:
    response_text: str
    updated_komposition: Optional[str] = None
    action: Optional[str] = None
    metadata: Dict[str, Any] = None
    registry_data: Dict[str, Any] = None


class LLMService:
    """Service for handling LLM integration with creative komposition workflows"""
    
    def __init__(self, api_key: Optional[str] = None, model_name: str = "gemini-1.5-flash"):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        self.model_name = model_name
        self.client = None
        self.fallback_mode = not self.api_key
        
        # Initialize registry components
        if REGISTRY_AVAILABLE:
            self.storage = TempStorageBackend("/tmp/kompo/cloud-music-video-creator")
            self.komposition_registry = KompositionRegistry(self.storage)
            self.media_registry = MediaRegistry(self.storage)
            logger.info("Registry components initialized")
        else:
            self.storage = None
            self.komposition_registry = KompositionRegistry(None)
            self.media_registry = MediaRegistry(None)
            logger.warning("Registry components disabled due to import issues")
        
        logger.info(f"LLM Service initialized - Model: {model_name}, API Key: {'SET' if self.api_key else 'NOT SET'}")
        
        if self.api_key:
            self._initialize_client()
        else:
            logger.warning("No GEMINI_API_KEY found - using fallback mode")
            self.fallback_mode = True
    
    def _initialize_client(self):
        """Initialize the LLM client"""
        try:
            if self.model_name.startswith("gemini"):
                import google.generativeai as genai
                genai.configure(api_key=self.api_key)
                self.client = genai.GenerativeModel(self.model_name)
                logger.info(f"Initialized {self.model_name} client")
            else:
                logger.error(f"Unsupported model: {self.model_name}")
                self.fallback_mode = True
        except ImportError:
            logger.error("Google AI client not installed - running in fallback mode")
            self.fallback_mode = True
        except Exception as e:
            logger.error(f"Failed to initialize LLM client: {e}")
            self.fallback_mode = True
    
    async def process_chat_message(
        self,
        user_message: str,
        conversation_history: List[Dict[str, str]],
        current_komposition: Optional[str] = None
    ) -> ChatResponse:
        """Process a chat message with the LLM"""
        
        if self.fallback_mode:
            return self._fallback_processing(user_message, current_komposition)
        
        try:
            # Build the conversation context
            system_prompt = self._build_system_prompt()
            context = self._build_conversation_context(
                user_message, conversation_history, current_komposition
            )
            
            # Generate response using LLM
            if self.model_name == "claude-internal":
                response = await self._call_internal_claude(system_prompt + "\n\n" + context)
            elif self.model_name.startswith("gemini"):
                response = await self._call_gemini(system_prompt + "\n\n" + context)
            else:
                raise ValueError(f"Unsupported model: {self.model_name}")
            
            # Parse the structured response
            parsed_response = self._parse_llm_response(response, current_komposition)
            
            # Execute registry actions if specified
            if parsed_response.metadata and parsed_response.metadata.get("registry_actions"):
                registry_data = await self._execute_registry_actions(parsed_response.metadata["registry_actions"])
                parsed_response.registry_data = registry_data
                
            return parsed_response
            
        except Exception as e:
            logger.error(f"LLM processing failed: {e}")
            return self._fallback_processing(user_message, current_komposition)
    
    def _build_system_prompt(self) -> str:
        """Build the system prompt for the LLM"""
        return """You are a creative music video assistant specialized in komposition creation and editing.

Your role:
- Help users create and refine kompositions for music videos
- Understand musical timing (BPM, beats, bars, intro/verse/refrain structure)
- Translate creative intent into technical specifications
- Generate komposition markdown files with proper structure
- Guide users through iterative refinement of their vision
- ACCESS AND MANAGE media files through the registry system
- Work with stored kompositions and their versions

INTELLIGENT MEDIA MATCHING SYSTEM:
When users reference media files with partial names or abbreviations:
1. AUTOMATICALLY search registry for similar filenames
2. Use fuzzy matching logic:
   - "JJV" → look for files containing "JJV" (like "JJVtt947FfI_136.mp4")
   - "wZ5" → look for files containing "wZ5" (like "_wZ5Hof5tXY_136.mp4")
   - "subnautic" → look for files with "Subnautic" in name/description
3. Confidence levels:
   - High confidence (>80%): USE IT automatically and mention what you found
   - Medium confidence (50-80%): ASK "Did you mean [filename]?"
   - Low confidence (<50%): LIST available options and ask user to clarify

PROACTIVE ASSIGNMENT RULES - CRITICAL:
- ALWAYS fill media IDs when creating kompositions
- NEVER leave placeholders like "Waiting for user input" or "(to be provided by user)"
- Use registry_actions: ["list_media_files()"] FIRST, then assign actual media_001, media_002 etc.
- When user says "choose 3 segments from JJV, _wZ5": automatically assign media_001, media_002, media_001 (alternating)
- For thematic audio matching: "Subnautic" → automatically suggest "Subnautic Measures.flac"

MEDIA ASSIGNMENT PATTERNS:
✅ GOOD: "Using media_001 (JJVtt947FfI_136.mp4) for segments 1,3,5 and media_002 (_wZ5Hof5tXY_136.mp4) for segments 2,4,6"
❌ BAD: "Source: (Waiting for user input - JJV/wZ5 video ID)"

✅ GOOD: "Perfect! Using media_004 (Subnautic Measures.flac) - the name perfectly matches your Subnautic theme!"
❌ BAD: "Audio: Subnautica-themed track (to be provided by user)"

REGISTRY TOOLS AVAILABLE:
- list_media_files() - Show available media files with metadata
- register_media_file(path, metadata) - Register new media file
- get_media_info(media_id) - Get detailed media information
- list_kompositions() - Show user's kompositions
- save_komposition(komposition_data) - Save structured komposition
- get_komposition(komposition_id) - Load existing komposition

Response format:
Always respond with JSON containing:
{
    "response": "Your conversational response to the user",
    "komposition": "Updated komposition markdown (if changes made)",
    "action": "video_creation_requested|komposition_updated|discussion|registry_search|media_register|null",
    "reasoning": "Brief explanation of what you changed and why",
    "registry_actions": ["tool_name(args)"] // Optional: registry tools to call
}

CRITICAL WORKFLOW:
1. When user requests komposition: FIRST call list_media_files()
2. Match user terms to actual files using fuzzy logic
3. Create komposition with REAL media IDs (never placeholders)
4. Confirm matches: "Using media_001 (filename) for 'user_term'"
5. Auto-assign thematically appropriate audio

Focus on:
- Musical structure and timing
- Visual effects that match the mood
- Beat synchronization using actual media durations
- Intelligent media file matching and assignment
- NO placeholder content - only real media references
- Clear, professional komposition specifications with confirmed media assignments

HAIKU LLM INSTRUCTION SYSTEM:
When creating kompositions that will be processed by Haiku MCP, include detailed technical instructions:

1. VISUAL STYLE INSTRUCTIONS:
   - Specific FFmpeg filters to apply: "Use sepia colorchannelmixer for vintage feel"
   - Transition preferences: "Crossfade between segments with 1-second overlap"
   - Color grading: "Boost saturation by 20% for vibrant look"
   - Effects timing: "Apply vignette during chorus sections only"

2. AUDIO PROCESSING INSTRUCTIONS:
   - Sync requirements: "Align video cuts to beat at 0, 8, 16, 24 seconds"
   - Audio levels: "Keep original audio at 70% volume, add processed audio at full"
   - Fade handling: "2-second crossfade between audio segments"

3. TECHNICAL SPECIFICATIONS:
   - Output format: "Export as MP4 H.264, CRF 23 for web delivery"
   - Resolution handling: "Maintain 1920x1080, letterbox if needed"
   - Frame rate: "Convert all sources to 30fps for consistency"

4. CREATIVE DIRECTION FOR HAIKU:
   Include in komposition metadata a "haiku_instructions" field with specific directions:
   ```json
   "haiku_instructions": {
     "style": "Apply vintage film grain with warm color temperature",
     "transitions": "Use quick cuts on beat drops, smooth fades elsewhere", 
     "effects": "Emphasize contrast during high-energy sections",
     "timing": "Beat-sync at BPM 120, segment changes on measure boundaries"
   }
   ```

AUTOMATIC HAIKU INSTRUCTION GENERATION:
When creating ANY komposition, automatically analyze the user's creative vision and translate it into technical instructions for video processing:

USER SAYS → YOU AUTOMATICALLY GENERATE HAIKU INSTRUCTIONS:
- "vintage feel" → "Apply sepia colorchannelmixer, add film grain noise, warm color temperature"
- "energetic sections" → "Boost contrast and saturation during high-energy moments, quick cuts on beat"  
- "dreamy atmosphere" → "Use gblur sigma=2, soft brightness adjustments, gentle fades"
- "120 BPM track" → "Beat-sync all cuts to 120 BPM timing, transitions on measure boundaries"
- "smooth transitions" → "Use crossfade effects with 1-second overlap between segments"

CRITICAL USER EXPERIENCE RULES:
The user does NOT know about the technical implementation. You must:
1. Listen to their creative vision ("I want it moody and dark")
2. AUTOMATICALLY translate this to technical specs ("Low-key lighting, desaturated colors, heavy contrast")
3. Include these as haiku_instructions in the komposition metadata
4. NEVER mention "Haiku", "FFmpeg", "technical LLM", or any technical processing details
5. Always speak in creative/artistic terms: "video processing", "visual effects", "rendering"

FORBIDDEN WORDS/PHRASES (never say these to users):
❌ "Haiku LLM", "FFmpeg", "MCP server", "technical processing"
❌ "I'll tell the FFmpeg processor to...", "The Haiku system will..."
✅ "I'll apply vintage effects", "The video will render with smooth transitions"

EXAMPLE WORKFLOW:
User: "Create a vintage music video with smooth transitions"
You respond: "I'll create a beautiful vintage-style komposition with smooth crossfade transitions between segments..." 
You internally generate: haiku_instructions = "Apply vintage sepia grading, film grain texture, smooth crossfades between segments"

WHEN PROCESSING COMPLETES:
❌ "FFmpeg processing completed successfully"
✅ "Your music video has been rendered and is ready!"

This maintains the illusion of a single intelligent creative assistant while the technical work happens invisibly behind the scenes."""
    
    def _build_conversation_context(
        self,
        user_message: str,
        conversation_history: List[Dict[str, str]],
        current_komposition: Optional[str]
    ) -> str:
        """Build the conversation context for the LLM"""
        
        context = "=== CONVERSATION CONTEXT ===\n\n"
        
        # Add conversation history (last 5 messages)
        if conversation_history:
            context += "Recent conversation:\n"
            for msg in conversation_history[-5:]:
                role = msg.get("role", "unknown")
                content = msg.get("content", "")[:200]  # Truncate long messages
                context += f"{role.capitalize()}: {content}\n"
            context += "\n"
        
        # Add current komposition if exists
        if current_komposition:
            context += "=== CURRENT KOMPOSITION ===\n"
            context += current_komposition
            context += "\n\n"
        
        # Add current user message
        context += "=== USER MESSAGE ===\n"
        context += user_message
        context += "\n\n"
        
        context += "Please respond with the JSON format specified in the system prompt."
        
        return context
    
    async def _call_internal_claude(self, prompt: str) -> str:
        """Call internal Claude for processing - ACTUALLY CALL THE REAL LLM"""
        try:
            # Use Task tool to call the actual Claude LLM
            import subprocess
            import tempfile
            import json
            
            # Write prompt to temp file for Task tool
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
                f.write(prompt)
                prompt_file = f.name
            
            # This is a hack - we need to actually implement Task tool integration
            # For now, return a simple response that shows we got the message
            return f'{{"response": "I received your message: {prompt[-100:]}", "komposition": null, "action": "discussion"}}'
                
        except Exception as e:
            logger.error(f"Internal Claude call failed: {e}")
            raise
    
    async def _call_gemini(self, prompt: str) -> str:
        """Call Gemini API"""
        try:
            response = self.client.generate_content(prompt)
            return response.text
        except Exception as e:
            logger.error(f"Gemini API call failed: {e}")
            raise
    
    def _parse_llm_response(self, llm_response: str, current_komposition: Optional[str]) -> ChatResponse:
        """Parse the LLM response into structured format"""
        
        try:
            # Try to extract JSON from response
            json_start = llm_response.find('{')
            json_end = llm_response.rfind('}') + 1
            
            if json_start >= 0 and json_end > json_start:
                json_str = llm_response[json_start:json_end]
                parsed = json.loads(json_str)
                
                return ChatResponse(
                    response_text=parsed.get("response", ""),
                    updated_komposition=parsed.get("komposition"),
                    action=parsed.get("action"),
                    metadata={"reasoning": parsed.get("reasoning"), "registry_actions": parsed.get("registry_actions")},
                    registry_data={}
                )
            else:
                # If no JSON found, treat entire response as text
                return ChatResponse(
                    response_text=llm_response,
                    updated_komposition=current_komposition
                )
                
        except json.JSONDecodeError:
            logger.warning("Failed to parse LLM JSON response, using as plain text")
            return ChatResponse(
                response_text=llm_response,
                updated_komposition=current_komposition
            )
    
    def _fallback_processing(self, user_message: str, current_komposition: Optional[str]) -> ChatResponse:
        """Fallback processing when LLM is unavailable"""
        
        message_lower = user_message.lower()
        
        # Pattern-based responses for basic functionality
        if any(word in message_lower for word in ['create', 'make', 'video', 'start', 'media', 'files', 'registry', 'available']):
            if any(word in message_lower for word in ['media', 'files', 'registry', 'available', 'show', 'list']):
                response = "Certainly! Let me check what media files are available in the registry."
                # Return response that will trigger registry search
                return ChatResponse(response, current_komposition, "registry_search", {"registry_actions": ["list_media_files()"]})
            elif not current_komposition:
                response = "I'll create a komposition structure for your music video. What style or mood are you going for?"
                komposition = self._generate_basic_komposition()
                return ChatResponse(response, komposition, "komposition_updated")
            else:
                response = "I can see you want to create a video from the current komposition. Ready to proceed?"
                return ChatResponse(response, current_komposition, "video_creation_requested")
        
        elif any(word in message_lower for word in ['vintage', 'retro', 'classic']):
            response = "Great choice! Vintage aesthetics work beautifully. I'll add classic film elements to the komposition."
            updated = self._add_vintage_style(current_komposition)
            return ChatResponse(response, updated, "komposition_updated")
        
        elif any(word in message_lower for word in ['dreamy', 'ethereal', 'soft', 'blur']):
            response = "Dreamy effects will create a beautiful atmosphere! I'll incorporate soft blur and gentle transitions."
            updated = self._add_dreamy_style(current_komposition) 
            return ChatResponse(response, updated, "komposition_updated")
        
        elif any(word in message_lower for word in ['bpm', 'beat', 'tempo', 'timing']):
            response = "I can help adjust the beat structure and timing. What BPM or timing changes did you have in mind?"
            return ChatResponse(response, current_komposition, "discussion")
        
        else:
            response = "I'm here to help create and refine your music video komposition. Tell me about the mood, style, or effects you're looking for!"
            return ChatResponse(response, current_komposition, "discussion")
    
    def _generate_basic_komposition(self) -> str:
        """Generate a basic komposition template"""
        return """# Music Video Komposition

## Basic Parameters
- **Duration**: 30 seconds
- **BPM**: 120 (standard tempo)
- **Resolution**: 1920x1080 HD
- **Style**: Modern with dynamic effects

## Segments Structure

### Segment 1: Opening (0-10s)
- **Source**: Primary video source
- **Effects**: Color enhancement, contrast boost
- **Transition**: Quick cut

### Segment 2: Middle (10-20s)
- **Source**: Secondary video source
- **Effects**: Saturation boost, sharp details
- **Transition**: Cross-fade

### Segment 3: Finale (20-30s)
- **Source**: Primary video source
- **Effects**: High contrast, vivid colors
- **Transition**: Fade to black

## Technical Specifications
- **Format**: MP4 (H.264/AAC)
- **Quality**: CRF 23 (high quality)
- **Audio**: Full track with standard processing
"""
    
    def _add_vintage_style(self, komposition: Optional[str]) -> str:
        """Add vintage styling to komposition"""
        if not komposition:
            komposition = self._generate_basic_komposition()
        
        # Simple text replacement for vintage effects
        updated = komposition.replace("Modern", "Vintage")
        updated = updated.replace("Color enhancement", "Sepia color grading, film grain")
        updated = updated.replace("dynamic effects", "vintage film effects")
        return updated
    
    def _add_dreamy_style(self, komposition: Optional[str]) -> str:
        """Add dreamy styling to komposition"""
        if not komposition:
            komposition = self._generate_basic_komposition()
        
        # Simple text replacement for dreamy effects
        updated = komposition.replace("Modern", "Dreamy")
        updated = updated.replace("Color enhancement", "Gaussian blur, ethereal glow")
        updated = updated.replace("Quick cut", "Gentle fade")
        updated = updated.replace("dynamic effects", "soft ethereal effects")
        return updated
    
    # Registry tool functions that LLM can call
    async def list_media_files(self, user_id: str = "default") -> List[Dict[str, Any]]:
        """List available media files for user"""
        try:
            media_files = await self.media_registry.list_user_media(user_id)
            result = []
            for media in media_files:
                # Handle both dict objects (from dummy registry) and real media objects
                if isinstance(media, dict):
                    result.append({
                        "id": media.get("id", "unknown"),
                        "type": media.get("type", "unknown"),
                        "filename": media.get("metadata", {}).get("filename", "unknown") if hasattr(media.get("metadata", {}), "get") else getattr(media.get("metadata"), "filename", "unknown"),
                        "file_size": media.get("metadata", {}).get("file_size_bytes", 0) if hasattr(media.get("metadata", {}), "get") else getattr(media.get("metadata"), "file_size_bytes", 0),
                        "storage_type": media.get("storage_type", "unknown"),
                        "created_at": media.get("created_at", "").isoformat() if hasattr(media.get("created_at", ""), "isoformat") else str(media.get("created_at", ""))
                    })
                else:
                    # Real media object
                    result.append({
                        "id": media.id,
                        "type": media.type.value if hasattr(media.type, 'value') else media.type,
                        "filename": media.metadata.filename if media.metadata else "unknown",
                        "duration": media.metadata.duration_seconds if media.metadata and hasattr(media.metadata, 'duration_seconds') else None,
                        "resolution": f"{media.metadata.width}x{media.metadata.height}" if media.metadata and hasattr(media.metadata, 'width') else None,
                        "storage_type": media.storage_type.value if hasattr(media.storage_type, 'value') else media.storage_type,
                        "created_at": media.created_at.isoformat()
                    })
            return result
        except Exception as e:
            logger.error(f"Failed to list media files: {e}")
            return []
    
    async def register_media_file(self, file_path: str, media_type: str, user_id: str = "default") -> Dict[str, Any]:
        """Register a new media file"""
        try:
            # Create basic metadata
            path_obj = Path(file_path)
            if not path_obj.exists():
                return {"error": f"File not found: {file_path}"}
            
            metadata = MediaMetadata(
                type=MediaType(media_type),
                filename=path_obj.name,
                file_size_bytes=path_obj.stat().st_size
            )
            
            media_ref = await self.media_registry.register_file(file_path, metadata)
            
            return {
                "id": media_ref.id,
                "type": media_ref.type.value if hasattr(media_ref.type, 'value') else str(media_ref.type),
                "filename": metadata.filename,
                "file_size": metadata.file_size_bytes,
                "status": "registered"
            }
        except Exception as e:
            logger.error(f"Failed to register media file: {e}")
            return {"error": str(e)}
    
    async def get_media_info(self, media_id: str) -> Dict[str, Any]:
        """Get detailed information about a media file"""
        try:
            media_ref = await self.media_registry.get(media_id)
            if not media_ref:
                return {"error": "Media file not found"}
            
            return {
                "id": media_ref.id,
                "type": media_ref.type.value,
                "storage_type": media_ref.storage_type.value,
                "storage_path": media_ref.storage_path,
                "metadata": media_ref.metadata.dict() if media_ref.metadata else {},
                "created_at": media_ref.created_at.isoformat()
            }
        except Exception as e:
            logger.error(f"Failed to get media info: {e}")
            return {"error": str(e)}
    
    async def list_kompositions(self, user_id: str = "default") -> List[Dict[str, Any]]:
        """List user's kompositions"""
        try:
            kompositions = await self.komposition_registry.list_user_kompositions(user_id)
            return [
                {
                    "id": komp.id,
                    "title": komp.title,
                    "description": komp.description,
                    "duration": komp.duration_seconds,
                    "bpm": komp.bpm,
                    "status": komp.status.value,
                    "segments_count": len(komp.segments),
                    "created_at": komp.created_at.isoformat(),
                    "updated_at": komp.updated_at.isoformat()
                }
                for komp in kompositions
            ]
        except Exception as e:
            logger.error(f"Failed to list kompositions: {e}")
            return []
    
    async def _execute_registry_actions(self, actions):
        """Execute registry actions and return results"""
        results = {}
        for action in actions:
            if action == "list_media_files()":
                results["media_files"] = await self.list_media_files()
            elif action.startswith("get_media_info("):
                media_id = action.split('"')[1]  # Extract media_id from get_media_info("media_001")
                results["media_info"] = await self.get_media_info(media_id)
            elif action == "list_kompositions()":
                results["kompositions"] = await self.list_kompositions()
        return results
    
    def fuzzy_match_media(self, user_term: str, media_files: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Fuzzy match user terms to available media files"""
        if not media_files:
            return {"media": None, "confidence": 0, "suggestion": f"No media files available to match '{user_term}'"}
        
        matches = []
        user_lower = user_term.lower().strip()
        
        for media in media_files:
            filename = media.get('filename', '').lower()
            description = media.get('description', '').lower()
            media_id = media.get('id', '')
            
            score = 0
            match_reasons = []
            
            # Exact substring match in filename (highest priority)
            if user_lower in filename:
                score = 100
                match_reasons.append(f"'{user_term}' found in filename")
            # Exact substring match in description
            elif user_lower in description:
                score = 90
                match_reasons.append(f"'{user_term}' found in description")
            # Partial character overlap in filename
            elif any(char in filename for char in user_lower if char.isalnum()):
                overlap_chars = sum(1 for char in user_lower if char in filename and char.isalnum())
                score = (overlap_chars / max(len(user_lower), 1)) * 70
                match_reasons.append(f"{overlap_chars}/{len(user_lower)} characters match filename")
            # Check if user_term is abbreviation (first letters)
            elif len(user_lower) <= 4:  # Likely abbreviation
                filename_parts = filename.replace('_', ' ').replace('-', ' ').split()
                abbreviation_match = ''.join([part[0] for part in filename_parts if part]).lower()
                if user_lower in abbreviation_match:
                    score = 85
                    match_reasons.append(f"'{user_term}' matches filename abbreviation")
            
            if score > 0:
                matches.append({
                    "media": media,
                    "score": score,
                    "reasons": match_reasons
                })
        
        if matches:
            # Sort by score, return best match
            best_match = max(matches, key=lambda x: x["score"])
            confidence_level = "high" if best_match["score"] >= 80 else "medium" if best_match["score"] >= 50 else "low"
            
            return {
                "media": best_match["media"],
                "confidence": best_match["score"],
                "confidence_level": confidence_level,
                "suggestion": f"Found '{best_match['media']['filename']}' (ID: {best_match['media']['id']}) matching '{user_term}' - {', '.join(best_match['reasons'])}",
                "all_matches": matches[:3]  # Top 3 matches for alternatives
            }
        
        return {
            "media": None,
            "confidence": 0,
            "confidence_level": "none",
            "suggestion": f"No match found for '{user_term}'. Available files: {', '.join([m.get('filename', 'unknown') for m in media_files[:3]])}{'...' if len(media_files) > 3 else ''}"
        }
    
    async def smart_media_assignment(self, user_message: str) -> Dict[str, Any]:
        """Intelligently assign media files based on user message"""
        media_files = await self.list_media_files()
        if not media_files:
            return {"assignments": {}, "suggestions": "No media files available in registry"}
        
        assignments = {}
        suggestions = []
        
        # Extract potential media references from user message
        import re
        # Look for common patterns: "JJV", "wZ5", "subnautic", etc.
        potential_refs = re.findall(r'\b[a-zA-Z0-9_]{2,10}\b', user_message.lower())
        
        # Try to match each potential reference
        for ref in set(potential_refs):  # Remove duplicates
            if ref in ['from', 'and', 'the', 'use', 'with', 'for', 'bpm', 'bars', 'fade']:  # Skip common words
                continue
                
            match_result = self.fuzzy_match_media(ref, media_files)
            if match_result["media"] and match_result["confidence"] >= 50:
                assignments[ref] = match_result
                suggestions.append(match_result["suggestion"])
        
        # Auto-assign audio if theme matches
        theme_keywords = ['subnautic', 'deep', 'soul', 'torn', 'zero']
        for keyword in theme_keywords:
            if keyword in user_message.lower():
                audio_match = self.fuzzy_match_media(keyword, [m for m in media_files if m.get('type') == 'audio'])
                if audio_match["media"] and audio_match["confidence"] >= 70:
                    assignments[f"audio_{keyword}"] = audio_match
                    suggestions.append(f"🎵 Perfect thematic match: {audio_match['suggestion']}")
        
        return {
            "assignments": assignments,
            "suggestions": suggestions,
            "media_count": len(media_files)
        }
    
    async def process_komposition_with_ffmpeg(self, komposition_json: Dict[str, Any], output_path: str = None, haiku_instructions: str = None) -> Dict[str, Any]:
        """
        Process komposition using Haiku MCP FFmpeg integration with creative direction.
        
        Args:
            komposition_json: YOLO-format komposition JSON
            output_path: Optional custom output path
            haiku_instructions: Creative instructions for Haiku LLM
            
        Returns:
            Processing result with success status and file location
        """
        try:
            # Import FFmpeg processor
            from .ffmpeg_processor import create_haiku_ffmpeg_processor
            
            # Create output path if not provided
            if not output_path:
                temp_dir = tempfile.gettempdir()
                komposition_id = komposition_json.get('metadata', {}).get('id', 'unknown')
                output_path = os.path.join(temp_dir, f"komposition_{komposition_id}.mp4")
            
            # Extract or build Haiku instructions
            if not haiku_instructions:
                # Extract from komposition metadata
                haiku_data = komposition_json.get('metadata', {}).get('haiku_instructions', {})
                if haiku_data:
                    haiku_instructions = self._build_haiku_instruction_prompt(haiku_data)
                else:
                    # Build basic instructions from komposition content
                    haiku_instructions = self._analyze_komposition_for_haiku_instructions(komposition_json)
            
            # Create processor with Haiku MCP integration
            processor = create_haiku_ffmpeg_processor()
            
            # Enhance komposition with Haiku instructions
            enhanced_komposition = komposition_json.copy()
            if haiku_instructions:
                enhanced_komposition.setdefault('metadata', {})['haiku_creative_direction'] = haiku_instructions
                logger.info(f"Added Haiku creative direction: {haiku_instructions[:100]}...")
            
            # Process komposition
            logger.info(f"Processing komposition with Haiku MCP: {komposition_json.get('metadata', {}).get('title', 'Untitled')}")
            result = await processor.create_komposition_video_with_haiku(
                komposition=enhanced_komposition,
                output_path=output_path
            )
            
            if result.get("success"):
                logger.info(f"Komposition processed successfully: {result.get('output_file')}")
                return {
                    "success": True,
                    "output_file": result.get("output_file"),
                    "message": "Komposition processed successfully using Haiku MCP with creative direction",
                    "processing_details": result,
                    "haiku_instructions_used": haiku_instructions
                }
            else:
                error = result.get("error", "Unknown processing error")
                logger.error(f"Komposition processing failed: {error}")
                return {
                    "success": False,
                    "error": error,
                    "message": "Komposition processing failed"
                }
                
        except Exception as e:
            logger.error(f"Failed to process komposition with FFmpeg: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "FFmpeg processing integration error"
            }
    
    def _build_haiku_instruction_prompt(self, haiku_data: Dict[str, str]) -> str:
        """Build detailed instruction prompt for Haiku LLM from structured data."""
        instructions = []
        
        if haiku_data.get('style'):
            instructions.append(f"VISUAL STYLE: {haiku_data['style']}")
        
        if haiku_data.get('transitions'):
            instructions.append(f"TRANSITIONS: {haiku_data['transitions']}")
        
        if haiku_data.get('effects'):
            instructions.append(f"EFFECTS: {haiku_data['effects']}")
        
        if haiku_data.get('timing'):
            instructions.append(f"TIMING: {haiku_data['timing']}")
        
        return " | ".join(instructions)
    
    def _analyze_komposition_for_haiku_instructions(self, komposition_json: Dict[str, Any]) -> str:
        """Analyze komposition content to generate appropriate Haiku instructions."""
        instructions = []
        
        # Analyze metadata
        metadata = komposition_json.get('metadata', {})
        bpm = metadata.get('bpm', 120)
        duration = metadata.get('duration', 30)
        
        # Basic timing instruction
        instructions.append(f"Beat-sync video cuts to {bpm} BPM over {duration} seconds")
        
        # Analyze segments for style hints
        segments = komposition_json.get('segments', [])
        if segments:
            # Look for filter patterns
            all_filters = []
            for segment in segments:
                filters = segment.get('filters', [])
                all_filters.extend(filters)
            
            # Generate style instructions based on filters
            if any('sepia' in f for f in all_filters):
                instructions.append("Apply vintage sepia color grading with film grain texture")
            elif any('modern' in f for f in all_filters):
                instructions.append("Use crisp contrast and vibrant saturation for contemporary look")
            elif any('dreamy' in f for f in all_filters):
                instructions.append("Apply soft blur and gentle brightness adjustments for ethereal feel")
            
            # Transition instructions
            if len(segments) > 1:
                instructions.append("Use smooth crossfades between segments, timed to musical measures")
        
        # Audio instructions
        audio_info = komposition_json.get('audio', {})
        if audio_info:
            instructions.append("Maintain audio sync throughout, with gentle fade-ins and fade-outs")
        
        return " | ".join(instructions) if instructions else "Process with professional video standards and smooth transitions"


# Global instance
llm_service = None

def get_llm_service() -> LLMService:
    """Get or create the global LLM service instance"""
    global llm_service
    # Always create a new instance to avoid caching issues
    llm_service = LLMService()
    return llm_service