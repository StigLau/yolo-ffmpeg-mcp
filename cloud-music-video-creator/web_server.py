#!/usr/bin/env python3
"""
Simple Web Server for Cloud Music Video Creator
Serves the HTML interface and provides API endpoints for video creation
"""

import asyncio
import json
import logging
import uuid
from pathlib import Path
from typing import Dict, Any

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel
import uvicorn

# Import our video processing components
from test_pipeline_quick import test_quick_pipeline


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI(title="Cloud Music Video Creator", version="1.0.0")

# Mount static files (HTML, CSS, JS)
web_dir = Path(__file__).parent / "web"
app.mount("/static", StaticFiles(directory=web_dir), name="static")

# In-memory job tracking (in production, use Redis or database)
active_jobs: Dict[str, Dict] = {}


class VideoRequest(BaseModel):
    description: str
    duration: int = 30
    music_style: str = "electronic"


class VideoResponse(BaseModel):
    job_id: str
    status: str
    message: str
    progress: int = 0
    video_url: str = None


@app.get("/", response_class=HTMLResponse)
async def serve_ui():
    """Serve the main HTML interface"""
    html_file = web_dir / "index.html"
    if html_file.exists():
        return HTMLResponse(html_file.read_text())
    else:
        raise HTTPException(status_code=404, detail="UI not found")


@app.post("/api/create-video", response_model=VideoResponse)
async def create_video(request: VideoRequest, background_tasks: BackgroundTasks):
    """Create a new music video from user description"""
    
    job_id = str(uuid.uuid4())
    
    # Initialize job tracking
    active_jobs[job_id] = {
        "status": "started",
        "progress": 0,
        "message": "Starting video creation...",
        "description": request.description,
        "duration": request.duration,
        "music_style": request.music_style,
        "created_at": asyncio.get_event_loop().time()
    }
    
    # Start background processing
    background_tasks.add_task(process_video_creation, job_id, request)
    
    logger.info(f"Started video creation job {job_id}")
    
    return VideoResponse(
        job_id=job_id,
        status="processing",
        message="Video creation started",
        progress=0
    )


@app.get("/api/status/{job_id}", response_model=VideoResponse)
async def get_job_status(job_id: str):
    """Get the status of a video creation job"""
    
    if job_id not in active_jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = active_jobs[job_id]
    
    return VideoResponse(
        job_id=job_id,
        status=job["status"],
        message=job["message"],
        progress=job["progress"],
        video_url=job.get("video_url")
    )


@app.get("/api/download/{job_id}")
async def download_video(job_id: str):
    """Download the completed video file"""
    
    if job_id not in active_jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = active_jobs[job_id]
    
    if job["status"] != "completed":
        raise HTTPException(status_code=400, detail="Video not ready for download")
    
    video_path = job.get("output_file")
    if not video_path or not Path(video_path).exists():
        raise HTTPException(status_code=404, detail="Video file not found")
    
    return FileResponse(
        path=video_path,
        filename=f"music_video_{job_id}.mp4",
        media_type="video/mp4"
    )


async def process_video_creation(job_id: str, request: VideoRequest):
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
        
        await asyncio.sleep(1)  # Simulate analysis
        
        # Update status: Generating komposition
        job.update({
            "progress": 25,
            "message": "Creating komposition specification..."
        })
        
        await asyncio.sleep(1)
        
        # Update status: LLM processing
        job.update({
            "progress": 40,
            "message": "Generating FFmpeg commands..."
        })
        
        await asyncio.sleep(1.5)
        
        # Update status: Running actual pipeline
        job.update({
            "progress": 60,
            "message": "Processing video and audio..."
        })
        
        # Run the actual video processing pipeline
        result = await run_video_pipeline(request)
        
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


async def run_video_pipeline(request: VideoRequest) -> Dict[str, Any]:
    """Run the actual video processing pipeline"""
    
    try:
        # Use our existing pipeline test but with dynamic parameters
        logger.info(f"Running video pipeline for: {request.description}")
        
        # For now, use the existing test pipeline
        # In production, this would parse the description and create a custom komposition
        result = await test_quick_pipeline()
        
        if result["success"]:
            # In a real implementation, we'd move the file to a permanent location
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


@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "active_jobs": len(active_jobs),
        "message": "Cloud Music Video Creator is running"
    }


if __name__ == "__main__":
    print("🎬 Starting Cloud Music Video Creator Web Server")
    print("=" * 50)
    print("📍 Open your browser to: http://localhost:8000")
    print("🔧 API Documentation: http://localhost:8000/docs")
    print("💚 Health Check: http://localhost:8000/api/health")
    print()
    
    # Run the server
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )