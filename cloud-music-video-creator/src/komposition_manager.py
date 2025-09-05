#!/usr/bin/env python3
"""
Komposition Manager for Cloud Music Video Creator
Handles local komposition.md file management and chat session mapping
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
import uuid

logger = logging.getLogger(__name__)


@dataclass
class KompositionSession:
    """Represents a komposition session with its associated files"""
    session_id: str
    title: str
    komposition_file: Path
    chat_log_file: Path
    created_at: datetime
    last_modified: datetime
    metadata: Dict[str, any]


class KompositionManager:
    """Manages local komposition files and chat sessions"""
    
    def __init__(self, base_dir: Optional[Path] = None):
        # Use temp directory to avoid root pollution
        self.base_dir = base_dir or Path("/tmp/kompo/cloud-music-video-creator/kompositions")
        self.sessions_file = self.base_dir / "sessions.json"
        
        # Create directories
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.chat_logs_dir = self.base_dir / "chat_logs"
        self.chat_logs_dir.mkdir(exist_ok=True)
        
        # Load existing sessions
        self.sessions = self._load_sessions()
        
        logger.info(f"KompositionManager initialized with base_dir: {self.base_dir}")
    
    def create_session(self, title: str = None, initial_komposition: str = None) -> KompositionSession:
        """Create a new komposition session"""
        
        session_id = str(uuid.uuid4())[:8]  # Short ID for files
        now = datetime.now()
        
        if not title:
            title = f"Komposition {now.strftime('%Y-%m-%d %H:%M')}"
        
        # Create file paths
        safe_title = self._sanitize_filename(title)
        komposition_file = self.base_dir / f"{session_id}_{safe_title}.md"
        chat_log_file = self.chat_logs_dir / f"{session_id}_chat.json"
        
        # Create initial komposition file
        if initial_komposition:
            komposition_file.write_text(initial_komposition)
        else:
            komposition_file.write_text(self._get_default_komposition())
        
        # Create initial chat log
        chat_log = {
            "session_id": session_id,
            "title": title,
            "created_at": now.isoformat(),
            "messages": []
        }
        chat_log_file.write_text(json.dumps(chat_log, indent=2))
        
        # Create session object
        session = KompositionSession(
            session_id=session_id,
            title=title,
            komposition_file=komposition_file,
            chat_log_file=chat_log_file,
            created_at=now,
            last_modified=now,
            metadata={}
        )
        
        # Store session
        self.sessions[session_id] = session
        self._save_sessions()
        
        logger.info(f"Created new session: {session_id} - {title}")
        return session
    
    def get_session(self, session_id: str) -> Optional[KompositionSession]:
        """Get a session by ID"""
        return self.sessions.get(session_id)
    
    def list_sessions(self) -> List[KompositionSession]:
        """List all sessions ordered by last modified (most recent first)"""
        sessions = list(self.sessions.values())
        sessions.sort(key=lambda s: s.last_modified, reverse=True)
        return sessions
    
    def get_current_komposition(self, session_id: str) -> Optional[str]:
        """Get the current komposition content for a session"""
        session = self.get_session(session_id)
        if not session or not session.komposition_file.exists():
            return None
        
        try:
            return session.komposition_file.read_text()
        except Exception as e:
            logger.error(f"Failed to read komposition file: {e}")
            return None
    
    def update_komposition(self, session_id: str, content: str) -> bool:
        """Update the komposition content for a session"""
        session = self.get_session(session_id)
        if not session:
            return False
        
        try:
            session.komposition_file.write_text(content)
            session.last_modified = datetime.now()
            self._save_sessions()
            logger.info(f"Updated komposition for session {session_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to update komposition: {e}")
            return False
    
    def log_chat_interaction(
        self,
        session_id: str,
        user_message: str,
        llm_response: str,
        llm_metadata: Dict = None,
        ffmpeg_commands: List[str] = None
    ) -> bool:
        """Log a chat interaction with comprehensive details"""
        session = self.get_session(session_id)
        if not session:
            return False
        
        try:
            # Load current chat log
            if session.chat_log_file.exists():
                chat_log = json.loads(session.chat_log_file.read_text())
            else:
                chat_log = {
                    "session_id": session_id,
                    "title": session.title,
                    "created_at": session.created_at.isoformat(),
                    "messages": []
                }
            
            # Add new interaction
            interaction = {
                "timestamp": datetime.now().isoformat(),
                "user_message": user_message,
                "llm_response": llm_response,
                "llm_metadata": llm_metadata or {},
                "ffmpeg_commands": ffmpeg_commands or [],
                "interaction_id": str(uuid.uuid4())[:8]
            }
            
            chat_log["messages"].append(interaction)
            
            # Save updated log
            session.chat_log_file.write_text(json.dumps(chat_log, indent=2))
            
            # Update session modified time
            session.last_modified = datetime.now()
            self._save_sessions()
            
            logger.info(f"Logged chat interaction for session {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to log chat interaction: {e}")
            return False
    
    def get_chat_history(self, session_id: str, limit: int = 10) -> List[Dict]:
        """Get recent chat history for a session"""
        session = self.get_session(session_id)
        if not session or not session.chat_log_file.exists():
            return []
        
        try:
            chat_log = json.loads(session.chat_log_file.read_text())
            messages = chat_log.get("messages", [])
            return messages[-limit:] if limit else messages
        except Exception as e:
            logger.error(f"Failed to get chat history: {e}")
            return []
    
    def delete_session(self, session_id: str) -> bool:
        """Delete a session and its associated files"""
        session = self.get_session(session_id)
        if not session:
            return False
        
        try:
            # Remove files
            if session.komposition_file.exists():
                session.komposition_file.unlink()
            if session.chat_log_file.exists():
                session.chat_log_file.unlink()
            
            # Remove from sessions
            del self.sessions[session_id]
            self._save_sessions()
            
            logger.info(f"Deleted session {session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete session: {e}")
            return False
    
    def _load_sessions(self) -> Dict[str, KompositionSession]:
        """Load sessions from storage"""
        if not self.sessions_file.exists():
            return {}
        
        try:
            data = json.loads(self.sessions_file.read_text())
            sessions = {}
            
            for session_data in data.get("sessions", []):
                session = KompositionSession(
                    session_id=session_data["session_id"],
                    title=session_data["title"],
                    komposition_file=Path(session_data["komposition_file"]),
                    chat_log_file=Path(session_data["chat_log_file"]),
                    created_at=datetime.fromisoformat(session_data["created_at"]),
                    last_modified=datetime.fromisoformat(session_data["last_modified"]),
                    metadata=session_data.get("metadata", {})
                )
                sessions[session.session_id] = session
            
            return sessions
            
        except Exception as e:
            logger.error(f"Failed to load sessions: {e}")
            return {}
    
    def _save_sessions(self):
        """Save sessions to storage"""
        try:
            sessions_data = []
            for session in self.sessions.values():
                session_data = {
                    "session_id": session.session_id,
                    "title": session.title,
                    "komposition_file": str(session.komposition_file),
                    "chat_log_file": str(session.chat_log_file),
                    "created_at": session.created_at.isoformat(),
                    "last_modified": session.last_modified.isoformat(),
                    "metadata": session.metadata
                }
                sessions_data.append(session_data)
            
            data = {
                "sessions": sessions_data,
                "last_updated": datetime.now().isoformat()
            }
            
            self.sessions_file.write_text(json.dumps(data, indent=2))
            
        except Exception as e:
            logger.error(f"Failed to save sessions: {e}")
    
    def _sanitize_filename(self, filename: str) -> str:
        """Sanitize filename for safe file creation"""
        # Remove/replace unsafe characters
        safe_chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_"
        safe_name = "".join(c if c in safe_chars else "_" for c in filename)
        
        # Limit length
        return safe_name[:50] if len(safe_name) > 50 else safe_name
    
    def _get_default_komposition(self) -> str:
        """Get default komposition template"""
        return """# New Music Video Komposition

## Basic Parameters
- **Duration**: 30 seconds
- **BPM**: 120 (standard tempo)
- **Resolution**: 1920x1080 HD
- **Style**: Ready for customization

## Segments Structure

### Segment 1: Opening (0-10s)
- **Source**: Primary video source
- **Effects**: To be defined
- **Transition**: To be defined

### Segment 2: Middle (10-20s)
- **Source**: Secondary video source
- **Effects**: To be defined
- **Transition**: To be defined

### Segment 3: Finale (20-30s)
- **Source**: Primary video source
- **Effects**: To be defined
- **Transition**: To be defined

## Technical Specifications
- **Format**: MP4 (H.264/AAC)
- **Quality**: CRF 23 (high quality)
- **Audio**: Full track with standard processing

---
*Tell me about your vision and I'll help customize this komposition!*
"""


# Global instance
komposition_manager = None

def get_komposition_manager() -> KompositionManager:
    """Get or create the global komposition manager instance"""
    global komposition_manager
    if komposition_manager is None:
        komposition_manager = KompositionManager()
    return komposition_manager