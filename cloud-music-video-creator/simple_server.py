#!/usr/bin/env python3
"""
Simple HTTP Server for Cloud Music Video Creator
Now with real LLM integration and comprehensive logging
"""

import asyncio
import json
import logging
import uuid
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from urllib.parse import urlparse, parse_qs
import threading
import time
import sys

# Add src to path for imports
sys.path.append(str(Path(__file__).parent / "src"))

# Import our video processing components
from test_pipeline_quick import test_quick_pipeline

# Import new services
from llm_service import get_llm_service
from komposition_manager import get_komposition_manager
from interaction_logger import get_interaction_logger
from ffmpeg_processor import get_ffmpeg_processor


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global job tracking
active_jobs = {}
job_threads = {}  # Track threads for job cancellation
web_dir = Path(__file__).parent / "web"


class VideoCreatorHandler(BaseHTTPRequestHandler):
    
    def do_GET(self):
        """Handle GET requests"""
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        
        if path == "/" or path == "/index.html":
            self.serve_file("index.html", "text/html")
            
        elif path == "/chat" or path == "/chat.html":
            self.serve_file("chat.html", "text/html")
            
        elif path == "/app.js":
            self.serve_file("app.js", "application/javascript")
            
        elif path.startswith("/api/status/"):
            # Extract job ID from path
            job_id = path.split("/")[-1]
            self.handle_status_check(job_id)
            
        elif path == "/api/health":
            self.send_json_response({
                "status": "healthy",
                "active_jobs": len(active_jobs),
                "message": "Cloud Music Video Creator is running"
            })
            
        elif path == "/api/sessions":
            self.handle_list_sessions()
            
        elif path.startswith("/api/sessions/"):
            # Extract session ID from path
            session_id = path.split("/")[-1]
            self.handle_get_session(session_id)
            
        elif path.startswith("/api/download/"):
            job_id = path.split("/")[-1]
            self.handle_download(job_id)
            
        else:
            self.send_404()
    
    def do_POST(self):
        """Handle POST requests"""
        if self.path == "/api/create-video":
            self.handle_create_video()
        elif self.path == "/api/chat":
            self.handle_chat()
        elif self.path == "/api/create-video-from-komposition":
            self.handle_create_video_from_komposition()
        elif self.path == "/api/sessions":
            self.handle_create_session()
        elif self.path == "/api/register-media":
            self.handle_register_media()
        elif self.path == "/api/populate-test-data":
            self.handle_populate_test_data()
        elif self.path.startswith("/api/stop/"):
            job_id = self.path.split("/")[-1]
            self.handle_stop_job(job_id)
        else:
            self.send_404()
    
    def serve_file(self, filename, content_type):
        """Serve a static file"""
        file_path = web_dir / filename
        if file_path.exists():
            self.send_response(200)
            self.send_header('Content-type', content_type)
            self.end_headers()
            self.wfile.write(file_path.read_bytes())
        else:
            self.send_404()
    
    def handle_create_video(self):
        """Handle video creation request"""
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            request_data = json.loads(post_data.decode('utf-8'))
            
            job_id = str(uuid.uuid4())
            
            # Initialize job tracking
            active_jobs[job_id] = {
                "status": "started",
                "progress": 0,
                "message": "Starting video creation...",
                "description": request_data.get("description", ""),
                "duration": request_data.get("duration", 30),
                "music_style": request_data.get("music_style", "electronic"),
                "created_at": time.time()
            }
            
            # Start background processing and track the thread
            thread = threading.Thread(target=self.process_video_creation, args=(job_id, request_data), daemon=True)
            job_threads[job_id] = thread
            thread.start()
            
            logger.info(f"Started video creation job {job_id}")
            
            response = {
                "job_id": job_id,
                "status": "processing",
                "message": "Video creation started",
                "progress": 0
            }
            
            self.send_json_response(response)
            
        except Exception as e:
            logger.error(f"Error creating video: {e}")
            self.send_json_response({"error": str(e)}, 400)
    
    def handle_status_check(self, job_id):
        """Handle status check request"""
        if job_id not in active_jobs:
            self.send_json_response({"error": "Job not found"}, 404)
            return
        
        job = active_jobs[job_id]
        
        response = {
            "job_id": job_id,
            "status": job["status"],
            "message": job["message"],
            "progress": job["progress"],
            "video_url": job.get("video_url")
        }
        
        self.send_json_response(response)
    
    def handle_download(self, job_id):
        """Handle video download request"""
        if job_id not in active_jobs:
            self.send_404()
            return
        
        job = active_jobs[job_id]
        
        if job["status"] != "completed":
            self.send_json_response({"error": "Video not ready for download"}, 400)
            return
        
        video_path = job.get("output_file")
        if not video_path or not Path(video_path).exists():
            self.send_404()
            return
        
        # Serve the video file
        try:
            self.send_response(200)
            self.send_header('Content-type', 'video/mp4')
            self.send_header('Content-Disposition', f'attachment; filename="music_video_{job_id}.mp4"')
            self.end_headers()
            
            with open(video_path, 'rb') as f:
                self.wfile.write(f.read())
                
        except Exception as e:
            logger.error(f"Error serving video file: {e}")
            self.send_404()
    
    def handle_chat(self):
        """Handle chat conversation with LLM"""
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            request_data = json.loads(post_data.decode('utf-8'))
            
            user_message = request_data.get("message", "")
            conversation_history = request_data.get("conversation_history", [])
            current_komposition = request_data.get("current_komposition")
            session_id = request_data.get("session_id")
            
            # Create session if none provided
            if not session_id:
                km = get_komposition_manager()
                session = km.create_session("New Chat Session")
                session_id = session.session_id
            
            # Process with real LLM
            response = asyncio.run(self.process_with_real_llm(
                user_message, conversation_history, current_komposition, session_id
            ))
            
            # Add session_id to response
            response["session_id"] = session_id
            
            self.send_json_response(response)
            
        except Exception as e:
            logger.error(f"Chat error: {e}")
            self.send_json_response({"error": str(e)}, 400)
    
    def handle_create_video_from_komposition(self):
        """Handle video creation from komposition"""
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            request_data = json.loads(post_data.decode('utf-8'))
            
            komposition = request_data.get("komposition", "")
            
            # Create a video creation job using the komposition
            job_id = str(uuid.uuid4())
            
            # Initialize job tracking
            active_jobs[job_id] = {
                "status": "started",
                "progress": 0,
                "message": "Starting komposition-based video creation...",
                "komposition": komposition,
                "created_at": time.time()
            }
            
            # Start background processing and track the thread
            thread = threading.Thread(target=self.process_komposition_video, args=(job_id, komposition), daemon=True)
            job_threads[job_id] = thread
            thread.start()
            
            logger.info(f"Started komposition video job {job_id}")
            
            response = {
                "job_id": job_id,
                "status": "processing",
                "message": "Komposition video creation started"
            }
            
            self.send_json_response(response)
            
        except Exception as e:
            logger.error(f"Komposition video error: {e}")
            self.send_json_response({"error": str(e)}, 400)
    
    def process_video_creation(self, job_id, request_data):
        """Background task to process video creation"""
        job = active_jobs[job_id]
        
        try:
            logger.info(f"Processing video creation for job {job_id}")
            
            # Update status: Starting processing
            job.update({
                "status": "processing",
                "progress": 10,
                "message": "Analyzing your request..."
            })
            
            time.sleep(1)  # Simulate analysis
            
            # Update status: Generating komposition
            job.update({
                "progress": 25,
                "message": "Creating komposition specification..."
            })
            
            time.sleep(1)
            
            # Update status: LLM processing
            job.update({
                "progress": 40,
                "message": "Generating FFmpeg commands..."
            })
            
            time.sleep(1.5)
            
            # Update status: Running actual pipeline
            job.update({
                "progress": 60,
                "message": "Processing video and audio..."
            })
            
            # Run the actual video processing pipeline
            result = asyncio.run(self.run_video_pipeline(request_data))
            
            if result["success"]:
                job.update({
                    "status": "completed",
                    "progress": 100,
                    "message": "Video creation completed successfully!",
                    "output_file": result.get("output_file"),
                    "video_url": f"/api/download/{job_id}",
                    "processing_time": result.get("total_duration", 0),
                    "file_size": result.get("file_size", 0)
                })
            else:
                raise Exception(f"Video processing failed: {result.get('error', 'Unknown error')}")
                
        except Exception as e:
            logger.error(f"Video creation failed for job {job_id}: {e}")
            job.update({
                "status": "failed",
                "progress": 0,
                "message": f"Video creation failed: {str(e)}"
            })
    
    async def run_video_pipeline(self, request_data):
        """Run the actual video processing pipeline"""
        try:
            logger.info(f"Running video pipeline for: {request_data.get('description', '')}")
            
            # Use our existing pipeline test
            result = await test_quick_pipeline()
            
            if result["success"]:
                output_file = "/tmp/music-video-creator/pipeline-test/pipeline_test_final.mp4"
                
                return {
                    "success": True,
                    "output_file": output_file,
                    "total_duration": result["total_duration"],
                    "file_size": Path(output_file).stat().st_size if Path(output_file).exists() else 0
                }
            else:
                return {
                    "success": False,
                    "error": "Pipeline processing failed"
                }
                
        except Exception as e:
            logger.error(f"Pipeline execution failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def scan_available_media_files(self):
        """Scan available media files in the source directory"""
        import os
        import subprocess
        
        media_files = []
        media_dirs = ["/tmp/music/source", "/tmp/music", "/tmp/kompo"]
        
        for media_dir in media_dirs:
            if os.path.exists(media_dir):
                for filename in os.listdir(media_dir):
                    if filename.startswith('.'):
                        continue
                    
                    filepath = os.path.join(media_dir, filename)
                    if os.path.isfile(filepath):
                        # Get file size
                        file_size = os.path.getsize(filepath)
                        size_mb = round(file_size / (1024 * 1024), 1)
                        
                        # Determine media type
                        ext = filename.lower().split('.')[-1]
                        if ext in ['mp4', 'avi', 'mov', 'mkv']:
                            media_type = 'video'
                        elif ext in ['mp3', 'wav', 'flac', 'm4a']:
                            media_type = 'audio'
                        elif ext in ['jpg', 'jpeg', 'png', 'gif']:
                            media_type = 'image'
                        else:
                            media_type = 'unknown'
                        
                        media_files.append({
                            'filename': filename,
                            'filepath': filepath,
                            'size_mb': size_mb,
                            'type': media_type,
                            'directory': media_dir
                        })
        
        return media_files

    async def process_with_real_llm(self, user_message, conversation_history, current_komposition, session_id):
        """Process user message with REAL LLM integration"""
        
        # Get services
        llm = get_llm_service()
        km = get_komposition_manager()
        logger_service = get_interaction_logger()
        
        try:
            # Log user message
            logger_service.log_user_message(session_id, user_message)
            
            # Get current komposition from session if not provided
            if not current_komposition:
                current_komposition = km.get_current_komposition(session_id)
            
            # Scan available media files
            available_media = self.scan_available_media_files()
            
            # Process with LLM (include media context)
            llm_response = await llm.process_chat_message(
                user_message, conversation_history, current_komposition, available_media
            )
            
            # Log LLM response
            logger_service.log_llm1_response(
                session_id=session_id,
                request=user_message,
                response=llm_response.response_text,
                model=llm.model_name,
                metadata=llm_response.metadata or {}
            )
            
            # Update komposition if changed
            if llm_response.updated_komposition and llm_response.updated_komposition != current_komposition:
                km.update_komposition(session_id, llm_response.updated_komposition)
                
                # Log komposition update
                logger_service.log_system_event(
                    session_id=session_id,
                    event="komposition_updated",
                    details={"updated_by": "llm", "action": llm_response.action}
                )
            
            # Log the full interaction in chat history
            km.log_chat_interaction(
                session_id=session_id,
                user_message=user_message,
                llm_response=llm_response.response_text,
                llm_metadata=llm_response.metadata
            )
            
            response_data = {
                "response": llm_response.response_text,
                "komposition": llm_response.updated_komposition,
                "action": llm_response.action
            }
            
            # Add registry data if available
            if llm_response.registry_data:
                response_data["registry_data"] = llm_response.registry_data
                
                # If media files were retrieved, enhance the response
                if "media_files" in llm_response.registry_data:
                    media_files = llm_response.registry_data["media_files"]
                    if media_files:
                        files_summary = []
                        for media in media_files:
                            files_summary.append(f"• {media['filename']} ({media['type']}, {media['file_size']} bytes) - ID: {media['id']}")
                        
                        enhanced_response = llm_response.response_text + "\n\nAvailable media files in registry:\n" + "\n".join(files_summary)
                        response_data["response"] = enhanced_response
            
            # Check if komposition was created and should be processed with FFmpeg
            if (llm_response.action == "create_komposition" and 
                llm_response.updated_komposition and 
                "process_video" in user_message.lower()):
                
                # Try to process with Haiku MCP if requested
                try:
                    # Parse komposition as JSON if it's a string
                    komposition_data = llm_response.updated_komposition
                    if isinstance(komposition_data, str):
                        # Try to extract JSON from markdown if needed
                        import re
                        json_match = re.search(r'```json\s*(\{.*?\})\s*```', komposition_data, re.DOTALL)
                        if json_match:
                            komposition_data = json.loads(json_match.group(1))
                        else:
                            # Assume the whole string is JSON
                            komposition_data = json.loads(komposition_data)
                    
                    # NEW: Process with markdown-native Haiku flow instead of JSON conversion
                    # This approach sends the original markdown directly to Haiku for better understanding
                    komposition_md = data.get("komposition", "")
                    ffmpeg_result = await llm.process_komposition_markdown_with_haiku(komposition_md)
                    
                    if ffmpeg_result.get("success"):
                        response_data["ffmpeg_result"] = ffmpeg_result
                        response_data["video_created"] = True
                        response_data["output_file"] = ffmpeg_result.get("output_file")
                        
                        # Enhance response with user-friendly processing info (hide technical details)
                        processing_msg = f"\n\n🎬 Your music video has been rendered and is ready! You can find it at: {ffmpeg_result.get('output_file')}"
                        response_data["response"] += processing_msg
                        
                        logger.info(f"Successfully processed komposition: {ffmpeg_result.get('output_file')}")
                    else:
                        error_msg = f"\n\n⚠️ Video rendering encountered an issue: {ffmpeg_result.get('error', 'Unknown error')}"
                        response_data["response"] += error_msg
                        logger.error(f"Video processing failed: {ffmpeg_result.get('error')}")
                        
                except Exception as e:
                    logger.warning(f"Could not process komposition with FFmpeg: {e}")
                    # Don't fail the whole request - just log the issue
            
            return response_data
            
        except Exception as e:
            logger.error(f"Real LLM processing failed: {e}")
            
            # Log error
            logger_service.log_error(
                session_id=session_id,
                error_type="llm_processing_error",
                error_message=str(e)
            )
            
            # Fall back to basic response
            return {
                "response": f"I encountered an issue processing your request. Error: {str(e)}. Please try again.",
                "komposition": current_komposition,
                "action": None
            }
    
    def handle_create_session(self):
        """Handle session creation request"""
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            request_data = json.loads(post_data.decode('utf-8'))
            
            title = request_data.get("title", "")
            initial_komposition = request_data.get("initial_komposition", "")
            
            km = get_komposition_manager()
            session = km.create_session(title, initial_komposition)
            
            response = {
                "session_id": session.session_id,
                "title": session.title,
                "created_at": session.created_at.isoformat(),
                "komposition": km.get_current_komposition(session.session_id)
            }
            
            self.send_json_response(response)
            
        except Exception as e:
            logger.error(f"Session creation error: {e}")
            self.send_json_response({"error": str(e)}, 400)
    
    def handle_list_sessions(self):
        """Handle session listing request"""
        try:
            km = get_komposition_manager()
            sessions = km.list_sessions()
            
            sessions_data = []
            for session in sessions:
                sessions_data.append({
                    "session_id": session.session_id,
                    "title": session.title,
                    "created_at": session.created_at.isoformat(),
                    "last_modified": session.last_modified.isoformat()
                })
            
            self.send_json_response({"sessions": sessions_data})
            
        except Exception as e:
            logger.error(f"Session listing error: {e}")
            self.send_json_response({"error": str(e)}, 400)
    
    def handle_get_session(self, session_id):
        """Handle get session request"""
        try:
            km = get_komposition_manager()
            session = km.get_session(session_id)
            
            if not session:
                self.send_json_response({"error": "Session not found"}, 404)
                return
            
            response = {
                "session_id": session.session_id,
                "title": session.title,
                "created_at": session.created_at.isoformat(),
                "last_modified": session.last_modified.isoformat(),
                "komposition": km.get_current_komposition(session_id),
                "chat_history": km.get_chat_history(session_id, limit=20)
            }
            
            self.send_json_response(response)
            
        except Exception as e:
            logger.error(f"Get session error: {e}")
            self.send_json_response({"error": str(e)}, 400)
    
    def handle_register_media(self):
        """Handle media file registration request"""
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            request_data = json.loads(post_data.decode('utf-8'))
            
            file_path = request_data.get("file_path", "")
            media_type = request_data.get("media_type", "video")
            user_id = request_data.get("user_id", "default")
            
            # Use LLM service to register media
            llm = get_llm_service()
            result = asyncio.run(llm.register_media_file(file_path, media_type, user_id))
            
            self.send_json_response(result)
            
        except Exception as e:
            logger.error(f"Media registration error: {e}")
            self.send_json_response({"error": str(e)}, 400)
    
    def handle_populate_test_data(self):
        """Populate registry with test media files"""
        try:
            llm = get_llm_service()
            results = []
            
            # Real .testdata multimedia files to register
            test_files = [
                # Videos
                {
                    "path": "../.testdata/JJVtt947FfI_136.mp4",
                    "type": "video",
                    "description": "Test video content JJV"
                },
                {
                    "path": "../.testdata/_wZ5Hof5tXY_136.mp4", 
                    "type": "video",
                    "description": "Test video content wZ5"
                },
                # Audio files
                {
                    "path": "../.testdata/16BL - Deep In My Soul (Original Mix).mp3",
                    "type": "audio", 
                    "description": "Deep In My Soul - Electronic track"
                },
                {
                    "path": "../.testdata/Subnautic Measures.flac",
                    "type": "audio",
                    "description": "Subnautic Measures - Ambient track"
                },
                {
                    "path": "../.testdata/Torn on TDF.flac",
                    "type": "audio",
                    "description": "Torn on TDF - Electronic track"
                },
                {
                    "path": "../.testdata/ZeroSoul.flac",
                    "type": "audio", 
                    "description": "ZeroSoul - Ambient track"
                },
                # Image
                {
                    "path": "../.testdata/Boat having a sad day.jpeg",
                    "type": "image",
                    "description": "Boat image for visual elements"
                }
            ]
            
            # Register each file
            for file_info in test_files:
                result = asyncio.run(llm.register_media_file(
                    file_info["path"], 
                    file_info["type"], 
                    "default"
                ))
                result["description"] = file_info["description"]
                results.append(result)
            
            self.send_json_response({
                "message": "Test data populated successfully",
                "files_registered": len(results),
                "results": results
            })
            
        except Exception as e:
            logger.error(f"Test data population error: {e}")
            self.send_json_response({"error": str(e)}, 400)
    
    def handle_stop_job(self, job_id):
        """Handle job cancellation request"""
        try:
            if job_id not in active_jobs:
                self.send_json_response({"error": "Job not found"}, 404)
                return
                
            job = active_jobs[job_id]
            
            # Check if job can be stopped
            if job["status"] in ["completed", "failed", "cancelled"]:
                self.send_json_response({
                    "error": f"Cannot stop job with status: {job['status']}"
                }, 400)
                return
            
            # Mark job as cancelled
            job.update({
                "status": "cancelled",
                "progress": 0,
                "message": "Job cancellation requested",
                "cancelled_at": time.time()
            })
            
            logger.info(f"Job {job_id} marked as cancelled")
            
            # Note: We can't forcefully stop threads in Python, but we set the status
            # The processing functions should check for cancellation status
            
            self.send_json_response({
                "job_id": job_id,
                "status": "cancelled",
                "message": "Job cancellation requested"
            })
            
        except Exception as e:
            logger.error(f"Stop job error: {e}")
            self.send_json_response({"error": str(e)}, 400)
    
    def generate_sample_komposition(self, user_input, style="general"):
        """Generate a sample komposition based on user input"""
        
        if style == "vintage":
            return """# Vintage Music Video Komposition

## Basic Parameters
- **Duration**: 30 seconds
- **BPM**: 90 (moderate vintage tempo)
- **Resolution**: 1920x1080 HD
- **Style**: Classic vintage with sepia and film grain

## Segments Structure

### Segment 1: Vintage Opening (0-10s)
- **Source**: Primary video source
- **Effects**: Sepia color grading, film grain texture
- **Transition**: Soft fade

### Segment 2: Nostalgic Middle (10-20s) 
- **Source**: Secondary video source
- **Effects**: Warm color temperature, subtle vignette
- **Transition**: Cross-fade

### Segment 3: Classic Finale (20-30s)
- **Source**: Primary video source
- **Effects**: Enhanced sepia, vintage film look
- **Transition**: Fade to black

## Technical Specifications
- **Format**: MP4 (H.264/AAC)
- **Quality**: CRF 23 (high quality)
- **Audio**: Background track at 75% volume
"""
        
        elif style == "dreamy":
            return """# Dreamy Music Video Komposition

## Basic Parameters
- **Duration**: 30 seconds
- **BPM**: 80 (slow, atmospheric)
- **Resolution**: 1920x1080 HD
- **Style**: Ethereal and soft with blur effects

## Segments Structure

### Segment 1: Soft Opening (0-10s)
- **Source**: Primary video source
- **Effects**: Gaussian blur, brightness boost
- **Transition**: Gentle fade-in

### Segment 2: Ethereal Middle (10-20s)
- **Source**: Secondary video source  
- **Effects**: Soft glow, enhanced saturation
- **Transition**: Smooth crossfade

### Segment 3: Dreamy Finale (20-30s)
- **Source**: Primary video source
- **Effects**: Heavy blur, ethereal atmosphere
- **Transition**: Long fade to white

## Technical Specifications
- **Format**: MP4 (H.264/AAC)
- **Quality**: CRF 23 (high quality)
- **Audio**: Ambient track with fade effects
"""
        
        else:
            return """# Music Video Komposition

## Basic Parameters
- **Duration**: 30 seconds
- **BPM**: 120 (standard tempo)
- **Resolution**: 1920x1080 HD
- **Style**: Modern with dynamic effects

## Segments Structure

### Segment 1: Dynamic Opening (0-10s)
- **Source**: Primary video source
- **Effects**: Color enhancement, contrast boost
- **Transition**: Quick cut

### Segment 2: Energetic Middle (10-20s)
- **Source**: Secondary video source
- **Effects**: Saturation boost, sharp details
- **Transition**: Cross-fade

### Segment 3: Strong Finale (20-30s)
- **Source**: Primary video source
- **Effects**: High contrast, vivid colors
- **Transition**: Fade to black

## Technical Specifications
- **Format**: MP4 (H.264/AAC)
- **Quality**: CRF 23 (high quality)
- **Audio**: Full track with standard processing
"""
    
    def add_vintage_effects(self, komposition):
        """Add vintage effects to existing komposition"""
        # Simple text replacement for demo
        updated = komposition.replace("Modern", "Vintage")
        updated = updated.replace("dynamic", "vintage sepia")
        updated = updated.replace("Color enhancement", "Sepia color grading, film grain")
        return updated
    
    def add_dreamy_effects(self, komposition):
        """Add dreamy effects to existing komposition"""
        updated = komposition.replace("dynamic", "soft blur")
        updated = komposition.replace("Color enhancement", "Gaussian blur, ethereal glow")
        updated = updated.replace("Quick cut", "Gentle fade")
        return updated
    
    def adjust_timing(self, komposition, user_input):
        """Adjust timing in komposition"""
        # Demo implementation
        if "longer" in user_input.lower():
            updated = komposition.replace("30 seconds", "45 seconds")
            updated = updated.replace("(0-10s)", "(0-15s)")
            updated = updated.replace("(10-20s)", "(15-30s)")
            updated = updated.replace("(20-30s)", "(30-45s)")
        else:
            updated = komposition.replace("30 seconds", "20 seconds")
            updated = updated.replace("(0-10s)", "(0-7s)")
            updated = updated.replace("(10-20s)", "(7-13s)")
            updated = updated.replace("(20-30s)", "(13-20s)")
        return updated
    
    def adjust_beats(self, komposition, user_input):
        """Adjust beat structure in komposition"""
        # Demo implementation
        import re
        bpm_match = re.search(r'(\d+)\s*bpm', user_input.lower())
        if bpm_match:
            new_bpm = bpm_match.group(1)
            updated = re.sub(r'BPM\*\*: \d+', f'BPM**: {new_bpm}', komposition)
            return updated
        return komposition
    
    def process_komposition_video(self, job_id, komposition):
        """Process video creation from komposition using real FFmpeg processing"""
        job = active_jobs[job_id]
        
        try:
            logger.info(f"Processing komposition video for job {job_id}")
            
            # Check for cancellation
            if job.get("status") == "cancelled":
                logger.info(f"Job {job_id} was cancelled before starting")
                return
            
            # Update status
            job.update({
                "progress": 10,
                "message": "Analyzing komposition structure..."
            })
            
            # Check for cancellation
            if job.get("status") == "cancelled":
                logger.info(f"Job {job_id} cancelled during analysis")
                return
            
            # Get session ID from job metadata or create temporary one
            session_id = job.get("session_id", f"temp_{job_id}")
            
            # Use real FFmpeg processing
            result = asyncio.run(self.run_komposition_pipeline(komposition, session_id, job_id))
            
            # Check for cancellation after processing
            if job.get("status") == "cancelled":
                logger.info(f"Job {job_id} cancelled after processing")
                return
            
            job.update({
                "progress": 30,
                "message": "Converting komposition to FFmpeg commands..."
            })
            
            time.sleep(1)
            
            # Check for cancellation
            if job.get("status") == "cancelled":
                logger.info(f"Job {job_id} cancelled during conversion")
                return
            
            job.update({
                "progress": 60,
                "message": "Executing video processing commands..."
            })
            
            if result["success"]:
                job.update({
                    "status": "completed",
                    "progress": 100,
                    "message": "Komposition video created successfully!",
                    "output_file": result.get("output_file"),
                    "video_url": f"/api/download/{job_id}",
                    "processing_method": result.get("processing_method"),
                    "validation_passed": result.get("validation_passed", False),
                    "session_id": session_id
                })
                # Clean up thread tracking
                if job_id in job_threads:
                    del job_threads[job_id]
            else:
                # Enhanced failure handling with user-friendly messages
                if result.get("processing_method") == "failed_with_full_analysis":
                    # We have full analysis with Gemini evaluation
                    failure_analysis = result.get("failure_analysis", {})
                    gemini_evaluation = result.get("gemini_evaluation", {})
                    corrected_komposition = result.get("corrected_komposition")
                    
                    # Use Gemini evaluation for user-friendly failure message
                    gemini_user_communication = gemini_evaluation.get("user_communication", "")
                    if gemini_user_communication:
                        # Extract the first option from Gemini's user communication suggestions
                        import re
                        option_match = re.search(r'\* \*\*Option \d+ \([^)]+\):\*\* "([^"]+)"', gemini_user_communication)
                        if option_match:
                            user_friendly_msg = option_match.group(1)
                        else:
                            # Use the full Gemini communication if no option pattern found
                            user_friendly_msg = gemini_user_communication.strip()
                    else:
                        # Fallback to showing actual technical error if no Gemini evaluation
                        technical_error = result.get("error", "Unknown error")
                        failure_type = failure_analysis.get("failure_type", "unknown")
                        
                        # Show the actual technical error instead of generic messages
                        user_friendly_msg = f"Video processing failed: {technical_error}"
                    
                    if corrected_komposition:
                        user_friendly_msg += " An improved version has been generated that should work better."
                    
                    job.update({
                        "status": "failed",
                        "progress": 0,
                        "message": user_friendly_msg,
                        "corrected_komposition": corrected_komposition,
                        "failure_analysis": failure_analysis,
                        "gemini_evaluation": gemini_evaluation,
                        "processing_method": "failed_with_full_analysis",
                        "enhanced_analysis": True
                    })
                elif result.get("processing_method") in ["failed_with_partial_analysis", "failed_with_analysis"]:
                    # We have failure analysis but limited Gemini evaluation
                    failure_analysis = result.get("failure_analysis", {})
                    failure_type = failure_analysis.get("failure_type", "unknown")
                    
                    if failure_type == "validation_error":
                        user_friendly_msg = "Your video project has validation issues that need to be addressed."
                    elif failure_type == "missing_media":
                        user_friendly_msg = "Some required media files are missing from your project."
                    else:
                        user_friendly_msg = "Your video project encountered processing issues."
                    
                    job.update({
                        "status": "failed",
                        "progress": 0,
                        "message": user_friendly_msg,
                        "failure_analysis": failure_analysis,
                        "processing_method": result.get("processing_method"),
                        "enhanced_analysis": True
                    })
                else:
                    # Standard failure - show actual technical error
                    error_msg = result.get("error", "Unknown processing error")
                    job.update({
                        "status": "failed", 
                        "progress": 0,
                        "message": f"Video processing failed: {error_msg}",
                        "technical_error": error_msg,
                        "processing_method": result.get("processing_method", "basic"),
                        "enhanced_analysis": False
                    })
                
                # Clean up thread tracking for failures
                if job_id in job_threads:
                    del job_threads[job_id]
                
        except Exception as e:
            logger.error(f"Komposition video failed for job {job_id}: {e}")
            job.update({
                "status": "failed",
                "progress": 0,
                "message": f"Komposition video creation failed: {str(e)}"
            })
            # Clean up thread tracking for exceptions
            if job_id in job_threads:
                del job_threads[job_id]
    
    async def run_komposition_pipeline(self, komposition: str, session_id: str, job_id: str = None):
        """Run the komposition-to-video pipeline with enhanced validation and failure analysis"""
        try:
            logger.info(f"🎬 Running enhanced komposition pipeline for session {session_id}")
            
            # Check for job cancellation before processing
            if job_id and job_id in active_jobs and active_jobs[job_id].get("status") == "cancelled":
                logger.info(f"Job {job_id} cancelled, aborting pipeline")
                return {
                    "success": False,
                    "error": "Job was cancelled",
                    "cancelled": True
                }
            
            # Use the new LLM service with markdown-native Haiku processing
            from src.llm_service import get_llm_service
            llm_service = get_llm_service()
            
            # Process komposition markdown with validation and failure analysis
            result = await llm_service.process_komposition_markdown_with_haiku(
                komposition_md=komposition,
                output_path=None,  # Let it generate path
                haiku_instructions=None  # Let it auto-generate from markdown
            )
            
            # Check for cancellation after processing
            if job_id and job_id in active_jobs and active_jobs[job_id].get("status") == "cancelled":
                logger.info(f"Job {job_id} cancelled after processing")
                return {
                    "success": False,
                    "error": "Job was cancelled",
                    "cancelled": True
                }
            
            if result.get("success"):
                logger.info(f"✅ Enhanced komposition processing successful")
                return {
                    "success": True,
                    "output_file": result.get("output_file"),
                    "processing_method": result.get("processing_method"),
                    "haiku_instructions_used": result.get("haiku_instructions_used"),
                    "validation_passed": result.get("validation_passed", False)
                }
            else:
                # Enhanced failure handling with analysis and user guidance
                error_message = result.get("error", "Unknown processing error")
                
                # Check for authentication-specific errors first
                if result.get("processing_method") == "authentication_failed":
                    auth_message = result.get("user_friendly_error", "Video processing service requires API credentials")
                    logger.error(f"🔑 Authentication failed: {auth_message}")
                    
                    # Update job status for authentication failure  
                    if job_id and job_id in active_jobs:
                        active_jobs[job_id].update({
                            "status": "failed",
                            "progress": 0,
                            "message": "🔑 Video processing service is currently unavailable. API credentials need to be configured by the system administrator.",
                            "technical_error": error_message,
                            "processing_method": "authentication_failed",
                            "requires_admin_setup": True,
                            "enhanced_failure_handling": True
                        })
                    
                    return {
                        "success": False,
                        "error": error_message,
                        "user_message": "🔑 Video processing service is currently unavailable. API credentials need to be configured by the system administrator.",
                        "progress": 0,
                        "processing_method": "authentication_failed",
                        "requires_admin_setup": True,
                        "enhanced_failure_handling": True
                    }
                
                # Check if we have failure analysis and user guidance
                elif result.get("failure_analysis") and result.get("user_guidance"):
                    user_friendly_message = result.get("user_guidance")
                    logger.warning(f"🔍 Processing failed with analysis: {user_friendly_message}")
                    
                    return {
                        "success": False,
                        "error": error_message,
                        "user_message": user_friendly_message,
                        "failure_analysis": result.get("failure_analysis"),
                        "gemini_evaluation": result.get("gemini_evaluation"),
                        "corrected_komposition": result.get("corrected_komposition"),
                        "processing_method": result.get("processing_method"),
                        "enhanced_failure_handling": True
                    }
                else:
                    # Standard failure without enhanced analysis
                    logger.error(f"❌ Processing failed: {error_message}")
                    return {
                        "success": False,
                        "error": error_message,
                        "processing_method": result.get("processing_method", "basic"),
                        "enhanced_failure_handling": False
                    }
                
        except Exception as e:
            logger.error(f"❌ Komposition pipeline execution failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def send_json_response(self, data, status_code=200):
        """Send JSON response"""
        self.send_response(status_code)
        self.send_header('Content-type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))
    
    def send_404(self):
        """Send 404 response"""
        self.send_response(404)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write(b'Not Found')
    
    def do_OPTIONS(self):
        """Handle CORS preflight requests"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()


def run_server(port=8000):
    """Run the HTTP server"""
    server_address = ('', port)
    httpd = HTTPServer(server_address, VideoCreatorHandler)
    
    print("🎬 Cloud Music Video Creator - Simple Web Server")
    print("=" * 50)
    print(f"📍 Server running at: http://localhost:{port}")
    print("🔧 Features: Video creation API, file serving, job tracking")
    print("💚 Health Check: http://localhost:8000/api/health")
    print()
    print("Press Ctrl+C to stop the server")
    print()
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Server stopped")
        httpd.server_close()


if __name__ == "__main__":
    import sys
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8001
    run_server(port)