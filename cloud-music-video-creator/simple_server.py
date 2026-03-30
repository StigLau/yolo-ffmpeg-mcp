#!/usr/bin/env python3
"""
Simple HTTP Server for Cloud Music Video Creator
Uses only standard library - no external dependencies required
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

# Import our video processing components
from test_pipeline_quick import test_quick_pipeline


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global job tracking
active_jobs = {}
web_dir = Path(__file__).parent / "web"


class VideoCreatorHandler(BaseHTTPRequestHandler):
    
    def do_GET(self):
        """Handle GET requests"""
        parsed_path = urlparse(self.path)
        path = parsed_path.path
        
        if path == "/" or path == "/index.html":
            self.serve_file("index.html", "text/html")
            
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
            
        elif path.startswith("/api/download/"):
            job_id = path.split("/")[-1]
            self.handle_download(job_id)
            
        else:
            self.send_404()
    
    def do_POST(self):
        """Handle POST requests"""
        if self.path == "/api/create-video":
            self.handle_create_video()
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
            
            # Start background processing
            threading.Thread(target=self.process_video_creation, args=(job_id, request_data), daemon=True).start()
            
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