#!/usr/bin/env python3
"""
Interaction Logger for Cloud Music Video Creator
Comprehensive logging of User, LLM1, LLM2, and FFmpeg interactions
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum
import uuid

logger = logging.getLogger(__name__)


class InteractionType(Enum):
    USER_MESSAGE = "user_message"
    LLM1_RESPONSE = "llm1_response"
    LLM2_CALL = "llm2_call"
    LLM2_RESPONSE = "llm2_response"
    FFMPEG_COMMAND = "ffmpeg_command"
    FFMPEG_OUTPUT = "ffmpeg_output"
    SYSTEM_EVENT = "system_event"
    ERROR = "error"


@dataclass
class InteractionLog:
    """Single interaction log entry"""
    interaction_id: str
    session_id: str
    timestamp: datetime
    interaction_type: InteractionType
    content: Dict[str, Any]
    metadata: Dict[str, Any]


class InteractionLogger:
    """Comprehensive logger for all system interactions"""
    
    def __init__(self, base_dir: Optional[Path] = None):
        # Use temp directory to avoid root pollution
        self.base_dir = base_dir or Path("/tmp/kompo/cloud-music-video-creator/logs")
        self.base_dir.mkdir(parents=True, exist_ok=True)
        
        # Log files
        self.interactions_dir = self.base_dir / "interactions"
        self.interactions_dir.mkdir(exist_ok=True)
        
        self.summary_file = self.base_dir / "daily_summary.json"
        
        logger.info(f"InteractionLogger initialized with base_dir: {self.base_dir}")
    
    def log_user_message(self, session_id: str, message: str, metadata: Dict = None) -> str:
        """Log a user message"""
        interaction_id = self._log_interaction(
            session_id=session_id,
            interaction_type=InteractionType.USER_MESSAGE,
            content={
                "message": message,
                "character_count": len(message)
            },
            metadata=metadata or {}
        )
        logger.info(f"Logged user message for session {session_id}")
        return interaction_id
    
    def log_llm1_response(self, session_id: str, request: str, response: str, 
                         model: str, metadata: Dict = None) -> str:
        """Log LLM1 (High-level creative) response"""
        interaction_id = self._log_interaction(
            session_id=session_id,
            interaction_type=InteractionType.LLM1_RESPONSE,
            content={
                "request": request,
                "response": response,
                "model": model,
                "request_length": len(request),
                "response_length": len(response)
            },
            metadata=metadata or {}
        )
        logger.info(f"Logged LLM1 response for session {session_id}")
        return interaction_id
    
    def log_llm2_call(self, session_id: str, purpose: str, request: str, 
                      model: str, metadata: Dict = None) -> str:
        """Log LLM2 (Technical FFmpeg) call"""
        interaction_id = self._log_interaction(
            session_id=session_id,
            interaction_type=InteractionType.LLM2_CALL,
            content={
                "purpose": purpose,
                "request": request,
                "model": model,
                "request_length": len(request)
            },
            metadata=metadata or {}
        )
        logger.info(f"Logged LLM2 call for session {session_id}")
        return interaction_id
    
    def log_llm2_response(self, session_id: str, call_id: str, response: str, 
                         commands_generated: List[str], metadata: Dict = None) -> str:
        """Log LLM2 (Technical FFmpeg) response"""
        interaction_id = self._log_interaction(
            session_id=session_id,
            interaction_type=InteractionType.LLM2_RESPONSE,
            content={
                "call_id": call_id,
                "response": response,
                "commands_generated": commands_generated,
                "command_count": len(commands_generated),
                "response_length": len(response)
            },
            metadata=metadata or {}
        )
        logger.info(f"Logged LLM2 response for session {session_id}")
        return interaction_id
    
    def log_ffmpeg_command(self, session_id: str, command: str, purpose: str,
                          metadata: Dict = None) -> str:
        """Log FFmpeg command execution"""
        interaction_id = self._log_interaction(
            session_id=session_id,
            interaction_type=InteractionType.FFMPEG_COMMAND,
            content={
                "command": command,
                "purpose": purpose,
                "command_length": len(command)
            },
            metadata=metadata or {}
        )
        logger.info(f"Logged FFmpeg command for session {session_id}")
        return interaction_id
    
    def log_ffmpeg_output(self, session_id: str, command_id: str, 
                         stdout: str, stderr: str, return_code: int,
                         execution_time: float, metadata: Dict = None) -> str:
        """Log FFmpeg command output and results"""
        interaction_id = self._log_interaction(
            session_id=session_id,
            interaction_type=InteractionType.FFMPEG_OUTPUT,
            content={
                "command_id": command_id,
                "stdout": stdout,
                "stderr": stderr,
                "return_code": return_code,
                "execution_time": execution_time,
                "success": return_code == 0,
                "stdout_length": len(stdout),
                "stderr_length": len(stderr)
            },
            metadata=metadata or {}
        )
        logger.info(f"Logged FFmpeg output for session {session_id}")
        return interaction_id
    
    def log_system_event(self, session_id: str, event: str, details: Dict,
                        metadata: Dict = None) -> str:
        """Log system events (session creation, file operations, etc.)"""
        interaction_id = self._log_interaction(
            session_id=session_id,
            interaction_type=InteractionType.SYSTEM_EVENT,
            content={
                "event": event,
                "details": details
            },
            metadata=metadata or {}
        )
        logger.info(f"Logged system event for session {session_id}: {event}")
        return interaction_id
    
    def log_error(self, session_id: str, error_type: str, error_message: str,
                  stack_trace: str = None, metadata: Dict = None) -> str:
        """Log errors and exceptions"""
        interaction_id = self._log_interaction(
            session_id=session_id,
            interaction_type=InteractionType.ERROR,
            content={
                "error_type": error_type,
                "error_message": error_message,
                "stack_trace": stack_trace,
                "message_length": len(error_message)
            },
            metadata=metadata or {}
        )
        logger.error(f"Logged error for session {session_id}: {error_type}")
        return interaction_id
    
    def get_session_interactions(self, session_id: str, 
                               interaction_types: List[InteractionType] = None) -> List[InteractionLog]:
        """Get all interactions for a session"""
        session_file = self.interactions_dir / f"{session_id}.json"
        if not session_file.exists():
            return []
        
        try:
            data = json.loads(session_file.read_text())
            interactions = []
            
            for entry in data.get("interactions", []):
                # Convert string timestamp back to datetime
                timestamp = datetime.fromisoformat(entry["timestamp"])
                interaction_type = InteractionType(entry["interaction_type"])
                
                # Filter by interaction types if specified
                if interaction_types and interaction_type not in interaction_types:
                    continue
                
                interaction = InteractionLog(
                    interaction_id=entry["interaction_id"],
                    session_id=entry["session_id"],
                    timestamp=timestamp,
                    interaction_type=interaction_type,
                    content=entry["content"],
                    metadata=entry["metadata"]
                )
                interactions.append(interaction)
            
            return interactions
            
        except Exception as e:
            logger.error(f"Failed to load interactions for session {session_id}: {e}")
            return []
    
    def get_session_summary(self, session_id: str) -> Dict[str, Any]:
        """Get summary statistics for a session"""
        interactions = self.get_session_interactions(session_id)
        
        summary = {
            "session_id": session_id,
            "total_interactions": len(interactions),
            "interaction_counts": {},
            "timespan": {},
            "llm_usage": {
                "llm1_calls": 0,
                "llm2_calls": 0,
                "total_request_chars": 0,
                "total_response_chars": 0
            },
            "ffmpeg_usage": {
                "commands_executed": 0,
                "successful_commands": 0,
                "failed_commands": 0,
                "total_execution_time": 0.0
            },
            "errors": []
        }
        
        if not interactions:
            return summary
        
        # Count interactions by type
        for interaction in interactions:
            interaction_type = interaction.interaction_type.value
            summary["interaction_counts"][interaction_type] = \
                summary["interaction_counts"].get(interaction_type, 0) + 1
        
        # Timespan
        timestamps = [i.timestamp for i in interactions]
        summary["timespan"] = {
            "start": min(timestamps).isoformat(),
            "end": max(timestamps).isoformat(),
            "duration_minutes": (max(timestamps) - min(timestamps)).total_seconds() / 60
        }
        
        # LLM usage
        for interaction in interactions:
            if interaction.interaction_type == InteractionType.LLM1_RESPONSE:
                summary["llm_usage"]["llm1_calls"] += 1
                summary["llm_usage"]["total_request_chars"] += \
                    interaction.content.get("request_length", 0)
                summary["llm_usage"]["total_response_chars"] += \
                    interaction.content.get("response_length", 0)
            elif interaction.interaction_type == InteractionType.LLM2_RESPONSE:
                summary["llm_usage"]["llm2_calls"] += 1
                summary["llm_usage"]["total_response_chars"] += \
                    interaction.content.get("response_length", 0)
        
        # FFmpeg usage
        for interaction in interactions:
            if interaction.interaction_type == InteractionType.FFMPEG_OUTPUT:
                summary["ffmpeg_usage"]["commands_executed"] += 1
                if interaction.content.get("success", False):
                    summary["ffmpeg_usage"]["successful_commands"] += 1
                else:
                    summary["ffmpeg_usage"]["failed_commands"] += 1
                summary["ffmpeg_usage"]["total_execution_time"] += \
                    interaction.content.get("execution_time", 0)
        
        # Errors
        error_interactions = [i for i in interactions if i.interaction_type == InteractionType.ERROR]
        summary["errors"] = [
            {
                "timestamp": i.timestamp.isoformat(),
                "error_type": i.content.get("error_type"),
                "error_message": i.content.get("error_message")
            }
            for i in error_interactions
        ]
        
        return summary
    
    def _log_interaction(self, session_id: str, interaction_type: InteractionType,
                        content: Dict[str, Any], metadata: Dict[str, Any]) -> str:
        """Internal method to log an interaction"""
        
        interaction_id = str(uuid.uuid4())[:8]
        timestamp = datetime.now()
        
        # Create interaction log
        interaction = InteractionLog(
            interaction_id=interaction_id,
            session_id=session_id,
            timestamp=timestamp,
            interaction_type=interaction_type,
            content=content,
            metadata=metadata
        )
        
        # Save to session file
        session_file = self.interactions_dir / f"{session_id}.json"
        
        # Load existing data or create new
        if session_file.exists():
            try:
                data = json.loads(session_file.read_text())
            except:
                data = {"session_id": session_id, "interactions": []}
        else:
            data = {"session_id": session_id, "interactions": []}
        
        # Add new interaction
        interaction_data = {
            "interaction_id": interaction_id,
            "session_id": session_id,
            "timestamp": timestamp.isoformat(),
            "interaction_type": interaction_type.value,
            "content": content,
            "metadata": metadata
        }
        
        data["interactions"].append(interaction_data)
        data["last_updated"] = timestamp.isoformat()
        
        # Save updated data
        try:
            session_file.write_text(json.dumps(data, indent=2))
        except Exception as e:
            logger.error(f"Failed to save interaction log: {e}")
        
        return interaction_id


# Global instance
interaction_logger = None

def get_interaction_logger() -> InteractionLogger:
    """Get or create the global interaction logger instance"""
    global interaction_logger
    if interaction_logger is None:
        interaction_logger = InteractionLogger()
    return interaction_logger