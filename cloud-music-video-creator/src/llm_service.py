#!/usr/bin/env python3
"""
LLM Service for Cloud Music Video Creator
Handles real LLM integration for creative komposition discussion

Now includes FFmpeg processing integration via Haiku MCP Bridge.
"""

import json
import logging
import os
import re
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
        # Auto-detect model provider and set appropriate API key
        if model_name.startswith("claude") or model_name.startswith("sonnet"):
            self.api_key = api_key or os.getenv('ANTHROPIC_API_KEY')
            self.provider = "claude"
        elif model_name.startswith("gpt"):
            self.api_key = api_key or os.getenv('OPENAI_API_KEY') 
            self.provider = "openai"
        else:  # Default to Gemini
            self.api_key = api_key or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
            self.provider = "gemini"
            
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
        """Initialize the LLM client based on provider"""
        try:
            if self.provider == "gemini":
                import google.generativeai as genai
                genai.configure(api_key=self.api_key)
                self.client = genai.GenerativeModel(self.model_name)
                logger.info(f"Initialized {self.model_name} client")
            elif self.provider == "claude":
                try:
                    import anthropic
                    self.client = anthropic.Anthropic(api_key=self.api_key)
                    logger.info(f"Initialized {self.model_name} client")
                except ImportError:
                    logger.error("Anthropic client not installed. Install with: pip install anthropic")
                    self.fallback_mode = True
            elif self.provider == "openai":
                try:
                    import openai
                    self.client = openai.OpenAI(api_key=self.api_key)
                    logger.info(f"Initialized {self.model_name} client")
                except ImportError:
                    logger.error("OpenAI client not installed. Install with: pip install openai")
                    self.fallback_mode = True
            else:
                logger.error(f"Unsupported provider: {self.provider}")
                self.fallback_mode = True
        except Exception as e:
            logger.error(f"Failed to initialize LLM client: {e}")
            self.fallback_mode = True
    
    async def process_chat_message(
        self,
        user_message: str,
        conversation_history: List[Dict[str, str]],
        current_komposition: Optional[str] = None,
        available_media: Optional[List[Dict]] = None
    ) -> ChatResponse:
        """Process a chat message with the LLM"""
        
        if self.fallback_mode:
            return self._fallback_processing(user_message, current_komposition)
        
        try:
            # Build the conversation context
            system_prompt = self._build_system_prompt(user_message)
            context = self._build_conversation_context(
                user_message, conversation_history, current_komposition, available_media
            )
            
            # Generate response using appropriate LLM
            prompt = system_prompt + "\n\n" + context
            
            if self.model_name == "claude-internal":
                response = await self._call_internal_claude(prompt)
            elif self.provider == "gemini":
                response = await self._call_gemini(prompt)
            elif self.provider == "claude":
                response = await self._call_claude(prompt)
            elif self.provider == "openai":
                response = await self._call_openai(prompt)
            else:
                raise ValueError(f"Unsupported provider: {self.provider}")
            
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
    
    def _build_system_prompt(self, user_input: str = "") -> str:
        """Build provider-specific system prompt for the LLM"""
        try:
            from .llm.prompts import get_user_prompt
        except ImportError:
            # Fallback to absolute import
            from llm.prompts import get_user_prompt
        return get_user_prompt(self.provider, user_input)
    
    def _build_conversation_context(
        self,
        user_message: str,
        conversation_history: List[Dict[str, str]],
        current_komposition: Optional[str],
        available_media: Optional[List[Dict]] = None
    ) -> str:
        """Build the conversation context for the LLM"""
        
        context = "=== CONVERSATION CONTEXT ===\n\n"
        
        # CRITICAL: Add available media information FIRST
        context += "=== AVAILABLE MEDIA FILES ===\n"
        if available_media and len(available_media) > 0:
            context += "**MEDIA CONTENT FOUND** - You have content to work with:\n\n"
            for i, media in enumerate(available_media, 1):
                context += f"{i:03d}. {media['filename']} ({media['type']}, {media['size_mb']}MB)\n"
                context += f"     Path: {media['filepath']}\n"
            
            context += f"\n**WORKFLOW**: User wants to create from available content. Show them this list and ask which files they want to use for their video.\n\n"
        else:
            context += "**NO MEDIA CONTENT FOUND** - No multimedia files available.\n"
            context += "**WORKFLOW**: Recommend getting content first (YouTube download, file upload, etc.) before creating video.\n\n"
        
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
            logger.info(f"Gemini prompt length: {len(prompt)}")
            response = self.client.generate_content(prompt)
            result = response.text
            logger.info(f"Gemini response length: {len(result) if result else 0}")
            if result:
                logger.info(f"Gemini response preview: {result[:200]}...")
            else:
                logger.warning("Gemini returned empty response")
            return result
        except Exception as e:
            logger.error(f"Gemini API call failed: {e}")
            raise
    
    async def _call_claude(self, prompt: str) -> str:
        """Call Claude API"""
        try:
            logger.info(f"Claude prompt length: {len(prompt)}")
            response = self.client.messages.create(
                model=self.model_name,
                max_tokens=4096,
                messages=[{"role": "user", "content": prompt}]
            )
            result = response.content[0].text
            logger.info(f"Claude response length: {len(result) if result else 0}")
            if result:
                logger.info(f"Claude response preview: {result[:200]}...")
            else:
                logger.warning("Claude returned empty response")
            return result
        except Exception as e:
            logger.error(f"Claude API call failed: {e}")
            raise
    
    async def _call_openai(self, prompt: str) -> str:
        """Call OpenAI API"""
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=4096
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"OpenAI API call failed: {e}")
            raise
    
    def _parse_llm_response(self, llm_response: str, current_komposition: Optional[str]) -> ChatResponse:
        """Parse the LLM response into structured format"""
        
        logger.info(f"Parsing response length: {len(llm_response)}")
        logger.info(f"Response preview: {llm_response[:100]}...")
        
        # First try to extract markdown komposition (for Sonnet)
        komposition = self._extract_markdown_komposition(llm_response)
        if komposition:
            logger.info(f"Extracted markdown komposition: {len(komposition)} chars")
            return ChatResponse(
                response_text=llm_response,
                updated_komposition=komposition
            )
        
        try:
            # Try to extract JSON from response (for other providers)
            json_start = llm_response.find('{')
            json_end = llm_response.rfind('}') + 1
            
            logger.info(f"JSON start: {json_start}, JSON end: {json_end}")
            
            if json_start >= 0 and json_end > json_start:
                json_str = llm_response[json_start:json_end]
                parsed = json.loads(json_str)
                
                # Handle different response formats
                response_text = ""
                komposition = parsed.get("komposition")
                
                # Try different field names for response text
                if "response" in parsed:
                    response_text = parsed["response"]
                elif "message" in parsed:
                    response_text = parsed["message"]
                elif "conversation" in parsed and parsed["conversation"]:
                    # Handle Gemini conversation format
                    for msg in parsed["conversation"]:
                        if msg.get("speaker") == "assistant":
                            response_text = msg.get("message", "")
                            break
                elif "messages" in parsed and parsed["messages"]:
                    # Handle Gemini messages format
                    for msg in parsed["messages"]:
                        if msg.get("role") == "assistant":
                            response_text = msg.get("content", "")
                            break
                
                # If still no response text found and there's text before JSON, use that
                if not response_text and json_start > 0:
                    text_before_json = llm_response[:json_start].strip()
                    # Remove markdown code block indicators
                    text_before_json = text_before_json.replace("```json", "").replace("```", "").strip()
                    if text_before_json:
                        response_text = text_before_json
                        logger.info(f"Using text before JSON as response: {len(response_text)} chars")
                
                logger.info(f"Extracted response text length: {len(response_text)}")
                
                return ChatResponse(
                    response_text=response_text,
                    updated_komposition=komposition,
                    action=parsed.get("action"),
                    metadata={"reasoning": parsed.get("reasoning"), "registry_actions": parsed.get("registry_actions")},
                    registry_data={}
                )
            else:
                # If no JSON found, treat entire response as text
                logger.info(f"No JSON found, using response as plain text: {len(llm_response)} chars")
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
            
    def _extract_markdown_komposition(self, response: str) -> Optional[str]:
        """Extract markdown komposition from response if present"""
        
        # First try to extract from markdown code blocks
        markdown_patterns = [
            r'```markdown\s*\n(.*?)\n```',  # Standard markdown blocks
            r'```\s*\n(# .*?)\n```',       # Generic code blocks starting with #
        ]
        
        for pattern in markdown_patterns:
            matches = re.findall(pattern, response, re.DOTALL)
            for match in matches:
                if self._validate_komposition_content(match):
                    logger.info(f"Found valid komposition in markdown code block: {len(match)} chars")
                    return match.strip()
        
        # Fallback: Look for komposition starting with # and containing required sections
        lines = response.split('\n')
        komposition_lines = []
        in_komposition = False
        
        for line in lines:
            # Start capturing when we see a markdown title
            if line.startswith('# ') and not in_komposition:
                # Check if this looks like a komposition title
                title_lower = line.lower()
                if any(keyword in title_lower for keyword in ['video', 'music', 'komposition', 'dream', 'vintage', 'subnautic', 'journey']):
                    in_komposition = True
                    komposition_lines.append(line)
            elif in_komposition:
                komposition_lines.append(line)
                
                # Stop if we encounter another major section or end marker
                if line.strip() == '---' and len(komposition_lines) > 10:
                    # Found end marker and we have substantial content
                    komposition_lines.append('')  # Add final newline
                    break
        
        if komposition_lines and len(komposition_lines) > 5:
            komposition = '\n'.join(komposition_lines).strip()
            
            if self._validate_komposition_content(komposition):
                logger.info(f"Found valid markdown komposition: {len(komposition)} chars")
                return komposition
                
        return None
    
    def _validate_komposition_content(self, content: str) -> bool:
        """Validate that content looks like a real komposition"""
        
        # Check for required sections
        required_sections = ['Basic Parameters', 'Segments', 'Technical Specs']
        sections_found = sum(1 for section in required_sections if section in content)
        
        # Check for real file references (not placeholders)
        has_real_files = bool(re.search(r'media_\d+\s*\([^)]+\.(mp4|flac|wav|mp3)\)', content))
        
        # Check for substantial content (not just placeholders)
        has_real_effects = bool(re.search(r'- \*\*Effects\*\*:\s*\n\s+- [^T][^o]', content))  # Not "To be defined"
        
        return (sections_found >= 2 and has_real_files) or (sections_found >= 3 and has_real_effects)
    
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
            try:
                from .ffmpeg_processor import create_haiku_ffmpeg_processor
            except ImportError:
                from ffmpeg_processor import create_haiku_ffmpeg_processor
            
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

    async def process_komposition_markdown_with_haiku(self, komposition_md: str, output_path: str = None, haiku_instructions: str = None) -> Dict[str, Any]:
        """
        Process komposition markdown directly using Haiku MCP with native markdown understanding.
        
        This new approach sends markdown directly to Haiku instead of converting to JSON,
        which aligns better with Haiku's natural language processing capabilities.
        
        Includes pre-validation to prevent Haiku from falling back to synthetic content.
        
        Args:
            komposition_md: Full komposition markdown content
            output_path: Optional custom output path
            haiku_instructions: Creative instructions for Haiku LLM
            
        Returns:
            Processing result with success status and file location
        """
        try:
            # STEP 1: Pre-validation before Haiku processing
            try:
                from .haiku_validation import validate_before_haiku_processing, analyze_haiku_processing_failure
            except ImportError:
                from haiku_validation import validate_before_haiku_processing, analyze_haiku_processing_failure
            
            logger.info("🔍 Pre-validating komposition before Haiku processing...")
            try:
                validation_result = validate_before_haiku_processing(komposition_md)
                
                # NEW: Enforce validation - stop processing if validation fails
                if not validation_result.get("success", False):
                    logger.error(f"❌ Validation failed - blocking processing")
                    errors = validation_result.get("errors", [])
                    missing_files = validation_result.get("validation_details", {}).get("missing_files", [])
                    
                    error_msg = "Komposition validation failed: " + "; ".join(errors)
                    if missing_files:
                        error_msg += f" Missing files: {[f['filename'] for f in missing_files]}"
                    
                    return {
                        "success": False,
                        "error": error_msg,
                        "message": "Processing blocked due to validation failures",
                        "validation_details": validation_result,
                        "processing_method": "validation_enforced_stop",
                        "available_alternatives": validation_result.get("validation_details", {}).get("suggested_alternatives", [])
                    }
                
                logger.info(f"✅ Pre-validation passed: {len(validation_result.get('validation_details', {}).get('available_files', []))} media files validated")
                
            except Exception as validation_error:
                logger.error(f"❌ Pre-validation failed: {validation_error}")
                return {
                    "success": False,
                    "error": f"Pre-validation failed: {validation_error}",
                    "message": "Komposition validation failed - media files not available or komposition structure invalid",
                    "validation_details": validation_result if 'validation_result' in locals() else {},
                    "processing_method": "validation_blocked"
                }
            
            # Import markdown-native processor
            try:
                from .markdown_ffmpeg_processor import create_markdown_haiku_processor
            except ImportError:
                from markdown_ffmpeg_processor import create_markdown_haiku_processor
            
            # Create output path if not provided
            if not output_path:
                temp_dir = tempfile.gettempdir()
                # Generate unique ID from markdown content hash
                import hashlib
                content_hash = hashlib.md5(komposition_md.encode()).hexdigest()[:8]
                output_path = os.path.join(temp_dir, f"komposition_md_{content_hash}.mp4")
            
            # Extract or build Haiku instructions from markdown content
            if not haiku_instructions:
                haiku_instructions = self._analyze_markdown_for_haiku_instructions(komposition_md)
            
            # Create markdown-native processor
            processor = create_markdown_haiku_processor()
            
            # Process komposition markdown directly
            title = self._extract_title_from_markdown(komposition_md)
            logger.info(f"Processing markdown komposition with Haiku MCP: {title}")
            
            result = await processor.process_komposition_markdown(
                komposition_md=komposition_md,
                output_path=output_path,
                creative_direction=haiku_instructions,
                session_id="llm_service_session"  # Provide a default session ID
            )
            
            # Check for authentication errors specifically
            if not result.get("success") and result.get("error"):
                error_msg = str(result.get("error", "")).lower()
                if ("authentication" in error_msg or "apikey" in error_msg or 
                    ("api" in error_msg and "key" in error_msg) or
                    "anthropic_api_key" in error_msg):
                    logger.error("❌ Anthropic API key not configured")
                    return {
                        "success": False,
                        "error": result.get("error"),
                        "message": "Video processing service requires API credentials",
                        "processing_method": "authentication_failed",
                        "user_friendly_error": "The video processing service needs proper API credentials to work. Please ensure the ANTHROPIC_API_KEY is configured.",
                        "validation_details": validation_result
                    }
            
            if result.get("success"):
                logger.info(f"✅ Markdown komposition processed successfully: {result.get('output_file', output_path)}")
                return {
                    "success": True,
                    "output_file": result.get("output_file", output_path),
                    "message": "Markdown komposition processed successfully using native Haiku understanding",
                    "processing_details": result,
                    "haiku_instructions_used": haiku_instructions,
                    "processing_method": "markdown_native",
                    "validation_passed": True
                }
            else:
                # STEP 2: Analyze Haiku failure for improvement suggestions
                error = result.get("error", "Unknown processing error")
                logger.error(f"❌ Markdown komposition processing failed: {error}")
                
                # Analyze failure and generate improvement suggestions
                logger.info("🔍 Analyzing Haiku failure for improvement suggestions...")
                try:
                    failure_analysis = analyze_haiku_processing_failure(
                        komposition_md=komposition_md,
                        haiku_result=result,
                        validation_result=validation_result
                    )
                    logger.info(f"📋 Failure analysis completed: {failure_analysis.get('failure_type')} - {len(failure_analysis.get('improvement_suggestions', []))} suggestions generated")
                    
                    # STEP 3: Evaluate failure with outer LLM (Gemini) for improvement
                    logger.info("🤖 Requesting Gemini evaluation of failure...")
                    try:
                        gemini_evaluation = await self.evaluate_haiku_failure_with_gemini(failure_analysis)
                        
                        if gemini_evaluation.get("success"):
                            logger.info("✅ Gemini evaluation completed successfully")
                            return {
                                "success": False,
                                "error": error,
                                "message": "Markdown komposition processing failed - analyzed and evaluated for improvement",
                                "failure_analysis": failure_analysis,
                                "gemini_evaluation": gemini_evaluation,
                                "corrected_komposition": gemini_evaluation.get("corrected_komposition"),
                                "user_guidance": gemini_evaluation.get("user_communication"),
                                "processing_method": "failed_with_full_analysis"
                            }
                        else:
                            logger.warning(f"Gemini evaluation failed: {gemini_evaluation.get('error')}")
                            return {
                                "success": False,
                                "error": error,
                                "message": "Markdown komposition processing failed",
                                "failure_analysis": failure_analysis,
                                "gemini_evaluation_error": gemini_evaluation.get("error"),
                                "processing_method": "failed_with_partial_analysis"
                            }
                            
                    except Exception as eval_error:
                        logger.error(f"Gemini evaluation failed: {eval_error}")
                        return {
                            "success": False,
                            "error": error,
                            "message": "Markdown komposition processing failed",
                            "failure_analysis": failure_analysis,
                            "gemini_evaluation_error": str(eval_error),
                            "processing_method": "failed_with_analysis"
                        }
                except Exception as analysis_error:
                    logger.error(f"Failed to analyze Haiku processing failure: {analysis_error}")
                    return {
                        "success": False,
                        "error": error,
                        "message": "Markdown komposition processing failed"
                    }
                
        except Exception as e:
            logger.error(f"Failed to process markdown komposition with Haiku: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Markdown FFmpeg processing integration error"
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
    
    def _analyze_markdown_for_haiku_instructions(self, komposition_md: str) -> str:
        """Analyze markdown komposition and generate creative instructions for Haiku."""
        instructions = []
        
        # Extract style information from markdown
        if "vintage" in komposition_md.lower():
            instructions.append("Apply vintage film effects with sepia tones and grain")
        if "8-bit" in komposition_md.lower():
            instructions.append("Add retro gaming visual style")
        if "smooth" in komposition_md.lower() and "transition" in komposition_md.lower():
            instructions.append("Use smooth crossfade transitions between segments")
        if "fast" in komposition_md.lower() or "quick" in komposition_md.lower():
            instructions.append("Apply quick cuts and dynamic transitions")
        
        # Extract BPM and timing information
        import re
        bpm_match = re.search(r'(\d+)\s*BPM', komposition_md, re.IGNORECASE)
        if bpm_match:
            bpm = bpm_match.group(1)
            instructions.append(f"Sync all transitions to {bpm} BPM timing")
        
        # Extract duration
        duration_match = re.search(r'(\d+)\s*seconds?', komposition_md, re.IGNORECASE)
        if duration_match:
            duration = duration_match.group(1)
            instructions.append(f"Total duration should be {duration} seconds")
        
        # Extract effects from segments
        if "grain" in komposition_md.lower():
            instructions.append("Add film grain texture")
        if "contrast" in komposition_md.lower():
            instructions.append("Enhance contrast levels")
        if "saturation" in komposition_md.lower():
            instructions.append("Adjust color saturation")
        
        return ". ".join(instructions) if instructions else "Process according to komposition specifications"
    
    def _extract_title_from_markdown(self, komposition_md: str) -> str:
        """Extract title from markdown komposition."""
        import re
        
        # Try to find title in various formats
        patterns = [
            r'#\s*([^\n]+)',  # H1 heading
            r'\*\*Title\*\*:\s*([^\n]+)',  # **Title**: format
            r'Title:\s*([^\n]+)',  # Title: format
        ]
        
        for pattern in patterns:
            match = re.search(pattern, komposition_md, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return "Untitled Komposition"
    
    async def evaluate_haiku_failure_with_gemini(self, failure_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """
        Use Gemini to evaluate Haiku processing failure and provide improvement suggestions.
        
        This implements the outer LLM evaluation requested by the user to analyze
        failed Haiku processing and suggest improvements.
        
        Args:
            failure_analysis: Analysis from haiku_validation.analyze_haiku_failure()
            
        Returns:
            Gemini's evaluation with corrected komposition and suggestions
        """
        try:
            if self.fallback_mode:
                return {
                    "success": False,
                    "error": "Gemini evaluation not available in fallback mode",
                    "corrected_komposition": None,
                    "processing_strategy": "Manual intervention required",
                    "user_communication": "Unable to analyze failure automatically"
                }
            
            evaluation_prompt = failure_analysis.get("gemini_evaluation_prompt", "")
            if not evaluation_prompt:
                return {
                    "success": False,
                    "error": "No evaluation prompt available",
                    "message": "Failed to create evaluation prompt from failure analysis"
                }
            
            logger.info("🤖 Evaluating Haiku failure with Gemini...")
            
            # Send evaluation prompt to Gemini
            response = await self._call_gemini(evaluation_prompt)
            
            # Parse Gemini's response for structured output
            parsed_evaluation = self._parse_gemini_failure_evaluation(response)
            
            logger.info(f"✅ Gemini evaluation completed: {parsed_evaluation.get('processing_strategy', 'No strategy provided')}")
            
            return {
                "success": True,
                "evaluation_response": response,
                "corrected_komposition": parsed_evaluation.get("corrected_komposition"),
                "processing_strategy": parsed_evaluation.get("processing_strategy"),
                "user_communication": parsed_evaluation.get("user_communication"),
                "failure_type": failure_analysis.get("failure_type"),
                "improvement_suggestions": failure_analysis.get("improvement_suggestions", [])
            }
            
        except Exception as e:
            logger.error(f"Failed to evaluate Haiku failure with Gemini: {e}")
            return {
                "success": False,
                "error": str(e),
                "message": "Gemini evaluation failed"
            }
    
    def _parse_gemini_failure_evaluation(self, gemini_response: str) -> Dict[str, Any]:
        """Parse Gemini's failure evaluation response into structured format."""
        parsed = {
            "corrected_komposition": None,
            "processing_strategy": None,
            "user_communication": None
        }
        
        try:
            # Look for markdown sections in Gemini's response
            import re
            
            # Extract corrected komposition (look for markdown code blocks)
            komposition_match = re.search(r'```markdown\n(.*?)\n```', gemini_response, re.DOTALL)
            if komposition_match:
                parsed["corrected_komposition"] = komposition_match.group(1).strip()
            
            # Extract processing strategy
            strategy_patterns = [
                r'\*\*Processing Strategy\*\*:\s*([^\n]*(?:\n(?!\*\*)[^\n]*)*)',
                r'## Processing Strategy\s*\n([^\n]*(?:\n(?!##)[^\n]*)*)',
                r'Processing Strategy:\s*([^\n]*(?:\n(?![\*#])[^\n]*)*)'
            ]
            
            for pattern in strategy_patterns:
                strategy_match = re.search(pattern, gemini_response, re.MULTILINE | re.IGNORECASE)
                if strategy_match:
                    parsed["processing_strategy"] = strategy_match.group(1).strip()
                    break
            
            # Extract user communication
            comm_patterns = [
                r'\*\*User Communication\*\*:\s*([^\n]*(?:\n(?!\*\*)[^\n]*)*)',
                r'## User Communication\s*\n([^\n]*(?:\n(?!##)[^\n]*)*)',
                r'User Communication:\s*([^\n]*(?:\n(?![\*#])[^\n]*)*)'
            ]
            
            for pattern in comm_patterns:
                comm_match = re.search(pattern, gemini_response, re.MULTILINE | re.IGNORECASE)
                if comm_match:
                    parsed["user_communication"] = comm_match.group(1).strip()
                    break
            
            # Fallback: extract any section that looks like advice
            if not parsed["processing_strategy"]:
                advice_match = re.search(r'(?:suggestion|advice|strategy|approach)[^:]*:([^.\n]*(?:[.\n][^.\n]*){0,2})', 
                                       gemini_response, re.IGNORECASE)
                if advice_match:
                    parsed["processing_strategy"] = advice_match.group(1).strip()
            
            return parsed
            
        except Exception as e:
            logger.warning(f"Failed to parse Gemini evaluation response: {e}")
            # Return raw response if parsing fails
            return {
                "corrected_komposition": None,
                "processing_strategy": gemini_response[:200] + "..." if len(gemini_response) > 200 else gemini_response,
                "user_communication": "Technical processing issue - please try with different media files"
            }


# Global instance
llm_service = None

def get_llm_service(provider: str = "gemini") -> LLMService:
    """Get or create the global LLM service instance"""
    global llm_service
    # Create instance with specific provider model
    if provider == "sonnet" or provider == "claude":
        model_name = "claude-3-5-sonnet-20241022"  # Latest Sonnet model
    elif provider == "openai":
        model_name = "gpt-4o-mini"
    else:  # Default to Gemini
        model_name = "gemini-1.5-flash"
    
    llm_service = LLMService(model_name=model_name)
    return llm_service