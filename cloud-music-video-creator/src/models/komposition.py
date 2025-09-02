"""
Komposition data models for Cloud Music Video Creator

Based on proven patterns from YOLO-FFMPEG-MCP project with
adaptations for cloud service architecture.
"""

from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel, Field, validator

from .media import MediaReference


class BeatSyncType(str, Enum):
    """Beat synchronization types"""
    QUARTER_NOTE = "quarter"
    EIGHTH_NOTE = "eighth"
    HALF_NOTE = "half"
    MEASURE = "measure"
    FREE = "free"  # No beat synchronization


class EffectType(str, Enum):
    """Available video effect types"""
    # Transition effects
    CROSSFADE = "crossfade"
    FADE_IN = "fade_in"
    FADE_OUT = "fade_out"
    DISSOLVE = "dissolve"
    
    # Visual effects
    ZOOM = "zoom"
    PAN = "pan"
    ROTATE = "rotate"
    SCALE = "scale"
    
    # Color effects
    COLOR_GRADE = "color_grade"
    SATURATION = "saturation"
    BRIGHTNESS = "brightness"
    CONTRAST = "contrast"
    
    # Style effects (from YOLO learnings)
    EIGHT_BIT = "8bit"
    LEICA = "leica"
    VINTAGE = "vintage"
    BLACK_WHITE = "black_white"
    
    # Advanced effects
    VIGNETTE = "vignette"
    BLUR = "blur"
    SHARPEN = "sharpen"
    NOISE = "noise"


class ProcessingStatus(str, Enum):
    """Komposition processing status"""
    DRAFT = "draft"
    ANALYZING = "analyzing"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class Effect(BaseModel):
    """Individual video effect definition"""
    type: EffectType
    name: str
    parameters: Dict[str, Any] = Field(default_factory=dict)
    intensity: float = Field(default=1.0, ge=0.0, le=1.0)
    start_time: Optional[float] = None  # Effect start time in seconds
    duration: Optional[float] = None    # Effect duration in seconds
    
    @validator('parameters')
    def validate_parameters(cls, v, values):
        """Validate effect parameters based on type"""
        effect_type = values.get('type')
        
        # Define required/optional parameters for each effect type
        parameter_schemas = {
            EffectType.CROSSFADE: {'duration': float},
            EffectType.ZOOM: {'scale_factor': float, 'center_x': float, 'center_y': float},
            EffectType.COLOR_GRADE: {'temperature': float, 'tint': float},
            EffectType.EIGHT_BIT: {'resolution_scale': int, 'color_depth': int},
            EffectType.LEICA: {'warmth': float, 'vignette_strength': float},
        }
        
        if effect_type in parameter_schemas:
            schema = parameter_schemas[effect_type]
            for param, expected_type in schema.items():
                if param in v and not isinstance(v[param], expected_type):
                    raise ValueError(f"Parameter {param} must be of type {expected_type}")
        
        return v


class Segment(BaseModel):
    """Individual video segment within komposition"""
    id: str
    name: Optional[str] = None
    
    # Timing (beat-synchronized)
    start_beat: float = Field(ge=0)
    duration_beats: float = Field(gt=0)
    start_seconds: float = Field(ge=0)
    duration_seconds: float = Field(gt=0)
    
    # Source media
    source_media: MediaReference
    source_start_time: float = Field(default=0.0, ge=0)  # Where in source to start
    
    # Effects and processing
    effects: List[Effect] = Field(default_factory=list)
    visual_score: float = Field(default=0.5, ge=0.0, le=1.0)  # Quality/suitability score
    
    # Processing metadata
    processing_metadata: Optional[Dict[str, Any]] = None
    
    @validator('start_seconds', 'duration_seconds')
    def validate_timing_consistency(cls, v, values, field):
        """Ensure beat and second timing are consistent"""
        # This would be validated against BPM in the full komposition context
        return v


class AudioTrack(BaseModel):
    """Audio track for komposition"""
    source: MediaReference
    
    # Audio properties
    bpm: float = Field(gt=0)
    duration_seconds: float = Field(gt=0)
    sample_rate: Optional[int] = None
    channels: Optional[int] = None
    
    # Audio processing
    volume: float = Field(default=1.0, ge=0.0, le=2.0)
    fade_in: Optional[float] = Field(default=None, ge=0)
    fade_out: Optional[float] = Field(default=None, ge=0)
    
    # Audio analysis metadata
    tempo_analysis: Optional[Dict[str, Any]] = None
    beat_positions: Optional[List[float]] = None  # Beat timestamps


class ProcessingStrategy(BaseModel):
    """Video processing strategy (from FastTrack learnings)"""
    strategy_type: str  # STANDARD_CONCAT, CROSSFADE_CONCAT, etc.
    estimated_cost: float
    estimated_duration: float
    confidence: float = Field(ge=0.0, le=1.0)
    
    # Technical requirements
    requires_normalization: bool = False
    requires_keyframe_alignment: bool = False
    recommended_resolution: Optional[str] = None
    
    # Processing options
    ffmpeg_optimization: Dict[str, Any] = Field(default_factory=dict)
    quality_settings: Dict[str, Any] = Field(default_factory=dict)


class VideoOutput(BaseModel):
    """Generated video output"""
    id: str
    komposition_id: str
    
    # Output file
    file_reference: MediaReference
    
    # Generation metadata
    generation_timestamp: datetime
    processing_strategy: ProcessingStrategy
    processing_cost: float
    quality_score: float = Field(ge=0.0, le=1.0)
    processing_duration: float  # seconds
    
    # Video properties
    resolution: str
    duration_seconds: float
    frame_rate: float
    file_size_bytes: int
    
    # Quality assurance
    validation_results: Optional[Dict[str, Any]] = None
    user_rating: Optional[float] = Field(default=None, ge=1.0, le=5.0)


class KompositionSpec(BaseModel):
    """Specification for creating a new komposition"""
    title: str
    description: str
    
    # Basic parameters
    bpm: float = Field(gt=0)
    duration_seconds: float = Field(gt=0)
    resolution: str = Field(default="1920x1080")
    
    # Optional inputs
    audio_file_path: Optional[str] = None
    visual_concept: Optional[str] = None
    reference_videos: Optional[List[str]] = None
    
    # Style preferences
    preferred_effects: Optional[List[EffectType]] = None
    visual_style: Optional[str] = None
    energy_level: Optional[str] = None  # "low", "medium", "high"
    
    @validator('resolution')
    def validate_resolution(cls, v):
        """Validate resolution format"""
        if 'x' not in v:
            raise ValueError("Resolution must be in format 'WIDTHxHEIGHT'")
        try:
            width, height = v.split('x')
            int(width), int(height)
        except ValueError:
            raise ValueError("Resolution must contain valid integers")
        return v


class Komposition(BaseModel):
    """Complete music video komposition"""
    # Identity
    id: str
    title: str
    description: Optional[str] = None
    user_id: str
    
    # Timestamps
    created_at: datetime
    updated_at: datetime
    
    # Audio/tempo configuration
    bpm: float = Field(gt=0)
    total_beats: float = Field(gt=0)
    duration_seconds: float = Field(gt=0)
    audio_track: Optional[AudioTrack] = None
    
    # Visual configuration
    resolution: str = Field(default="1920x1080")
    segments: List[Segment] = Field(default_factory=list)
    
    # Processing state
    status: ProcessingStatus = ProcessingStatus.DRAFT
    processing_metadata: Optional[Dict[str, Any]] = None
    processing_strategy: Optional[ProcessingStrategy] = None
    
    # Outputs
    generated_videos: List[VideoOutput] = Field(default_factory=list)
    
    # User interaction
    conversation_context: Optional[Dict[str, Any]] = None  # Minimal context, not full conversation
    user_feedback: Optional[List[str]] = None
    
    # System metadata
    version: int = Field(default=1)
    tags: List[str] = Field(default_factory=list)
    
    @validator('total_beats')
    def calculate_total_beats(cls, v, values):
        """Ensure total_beats matches duration and BPM"""
        bpm = values.get('bpm')
        duration = values.get('duration_seconds')
        if bpm and duration:
            calculated_beats = (bpm * duration) / 60.0
            if abs(v - calculated_beats) > 0.1:  # Allow small floating point differences
                raise ValueError(f"total_beats ({v}) doesn't match calculated beats ({calculated_beats})")
        return v
    
    @property
    def is_ready_for_processing(self) -> bool:
        """Check if komposition is ready for video generation"""
        return (
            self.audio_track is not None and
            len(self.segments) > 0 and
            self.status == ProcessingStatus.DRAFT and
            all(segment.source_media for segment in self.segments)
        )
    
    @property
    def estimated_processing_cost(self) -> float:
        """Estimate processing cost based on complexity"""
        base_cost = 0.02  # Base FastTrack analysis cost
        
        # Add cost per segment
        segment_cost = len(self.segments) * 0.01
        
        # Add cost for complex effects
        effect_cost = sum(
            0.005 for segment in self.segments 
            for effect in segment.effects
            if effect.type in [EffectType.EIGHT_BIT, EffectType.LEICA, EffectType.COLOR_GRADE]
        )
        
        # Duration multiplier
        duration_multiplier = min(self.duration_seconds / 60.0, 5.0)  # Cap at 5x for long videos
        
        return (base_cost + segment_cost + effect_cost) * duration_multiplier
    
    def get_latest_video(self) -> Optional[VideoOutput]:
        """Get the most recently generated video"""
        if not self.generated_videos:
            return None
        return max(self.generated_videos, key=lambda v: v.generation_timestamp)
    
    def add_segment(self, segment: Segment) -> None:
        """Add a segment and validate timing"""
        # Validate segment doesn't overlap with existing segments
        for existing in self.segments:
            if (segment.start_seconds < existing.start_seconds + existing.duration_seconds and
                segment.start_seconds + segment.duration_seconds > existing.start_seconds):
                raise ValueError(f"Segment {segment.id} overlaps with existing segment {existing.id}")
        
        self.segments.append(segment)
        self.segments.sort(key=lambda s: s.start_seconds)  # Keep segments sorted by time
    
    def update_from_spec(self, spec: KompositionSpec) -> None:
        """Update komposition from specification"""
        self.title = spec.title
        self.description = spec.description
        self.bpm = spec.bpm
        self.duration_seconds = spec.duration_seconds
        self.resolution = spec.resolution
        self.total_beats = (spec.bpm * spec.duration_seconds) / 60.0
        self.updated_at = datetime.utcnow()
        
        # Reset processing state if significant changes
        if self.status == ProcessingStatus.COMPLETED:
            self.status = ProcessingStatus.DRAFT
            self.processing_strategy = None


class UserSession(BaseModel):
    """User session state for komposition work"""
    user_id: str
    session_id: str
    current_komposition_id: Optional[str] = None
    
    # Session context (minimal, not full conversation)
    context: Dict[str, Any] = Field(default_factory=dict)
    last_activity: datetime = Field(default_factory=datetime.utcnow)
    
    # Preferences learned during session
    preferred_styles: List[str] = Field(default_factory=list)
    feedback_patterns: List[str] = Field(default_factory=list)
    
    @property
    def is_active(self) -> bool:
        """Check if session is still active (within last hour)"""
        return (datetime.utcnow() - self.last_activity).seconds < 3600