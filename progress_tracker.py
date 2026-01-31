import time
from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum

class ErrorType(Enum):
    """Categories of errors that can occur during processing."""
    CODEC_ERROR = "codec_error"
    FILE_NOT_FOUND = "file_not_found"
    PERMISSION_ERROR = "permission_error"
    PROCESSING_ERROR = "processing_error"
    UNKNOWN_ERROR = "unknown_error"

@dataclass
class SceneInfo:
    """Information about a scene being processed."""
    movie_show: str
    start_timecode: str
    end_timecode: str
    duration: float
    chunk_number: int
    scene_index: int
    status: str = "pending"  # pending, processing, completed, failed
    error_type: Optional[ErrorType] = None
    error_message: Optional[str] = None
    processing_time: Optional[float] = None

@dataclass
class ChunkInfo:
    """Information about a chunk being processed."""
    chunk_number: int
    total_scenes: int
    completed_scenes: int = 0
    failed_scenes: int = 0
    estimated_duration: float = 0.0
    actual_duration: float = 0.0
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    status: str = "pending"  # pending, processing, completed, failed
    output_file: Optional[str] = None
    file_size: str = ""
    error_message: Optional[str] = None
    failed_scene_names: List[str] = field(default_factory=list)
    output_file: Optional[str] = None
    file_size: Optional[str] = None
    failed_scene_names: List[str] = field(default_factory=list)

class ProgressTracker:
    """
    Comprehensive progress tracking for Marvel Mega Cut processing.
    Manages scene and chunk progress, timing, ETAs, and error reporting.
    """
    
    def __init__(self):
        self.scenes: List[SceneInfo] = []
        self.chunks: Dict[int, ChunkInfo] = {}
        self.current_chunk: Optional[int] = None
        self.current_scene: Optional[int] = None
        self.processing_start_time: Optional[datetime] = None
        self.scene_processing_times: List[float] = []
        self.total_scenes_processed: int = 0
        
    def initialize_plan(self, scenes_data: List[Dict], chunk_scenes_map: Dict[int, List[Dict]]):
        """
        Initialize the processing plan with scene and chunk information.
        
        Args:
            scenes_data: List of scene dictionaries from CSV parser
            chunk_scenes_map: Mapping of chunk numbers to their scenes
        """
        self.scenes.clear()
        self.chunks.clear()
        
        # Create scene info objects
        scene_index = 0
        for chunk_num, chunk_scenes in chunk_scenes_map.items():
            chunk_duration = 0.0
            
            for scene_data in chunk_scenes:
                # Calculate scene duration
                start = self._parse_timecode(scene_data['start_timecode'])
                end = self._parse_timecode(scene_data['end_timecode'])
                duration = end - start
                chunk_duration += duration
                
                scene_info = SceneInfo(
                    movie_show=scene_data['movie_show'],
                    start_timecode=scene_data['start_timecode'],
                    end_timecode=scene_data['end_timecode'],
                    duration=duration,
                    chunk_number=chunk_num,
                    scene_index=scene_index
                )
                self.scenes.append(scene_info)
                scene_index += 1
            
            # Create chunk info
            chunk_info = ChunkInfo(
                chunk_number=chunk_num,
                total_scenes=len(chunk_scenes),
                estimated_duration=chunk_duration
            )
            self.chunks[chunk_num] = chunk_info
    
    def start_processing(self):
        """Mark the start of overall processing."""
        self.processing_start_time = datetime.now()
    
    def start_chunk(self, chunk_number: int):
        """Mark the start of processing a specific chunk."""
        self.current_chunk = chunk_number
        if chunk_number in self.chunks:
            self.chunks[chunk_number].status = "processing"
            self.chunks[chunk_number].start_time = datetime.now()
    
    def start_scene(self, scene_index: int):
        """Mark the start of processing a specific scene."""
        self.current_scene = scene_index
        if scene_index < len(self.scenes):
            self.scenes[scene_index].status = "processing"
    
    def complete_scene(self, scene_index: int, processing_time: float):
        """Mark a scene as completed successfully."""
        if scene_index < len(self.scenes):
            scene = self.scenes[scene_index]
            scene.status = "completed"
            scene.processing_time = processing_time
            
            # Update chunk progress
            chunk_num = scene.chunk_number
            if chunk_num in self.chunks:
                self.chunks[chunk_num].completed_scenes += 1
            
            # Track processing times for ETA calculation
            self.scene_processing_times.append(processing_time)
            self.total_scenes_processed += 1
    
    def fail_scene(self, scene_index: int, error_type: ErrorType, error_message: str):
        """Mark a scene as failed with error details."""
        if scene_index < len(self.scenes):
            scene = self.scenes[scene_index]
            scene.status = "failed"
            scene.error_type = error_type
            scene.error_message = error_message
            
            # Update chunk progress
            chunk_num = scene.chunk_number
            if chunk_num in self.chunks:
                chunk = self.chunks[chunk_num]
                chunk.failed_scenes += 1
                chunk.failed_scene_names.append(scene.movie_show)
    
    def complete_chunk(self, chunk_number: int, output_file: str, file_size: str = ""):
        """Mark a chunk as completed."""
        if chunk_number in self.chunks:
            chunk = self.chunks[chunk_number]
            chunk.status = "completed"
            chunk.end_time = datetime.now()
            chunk.output_file = output_file
            chunk.file_size = file_size
            
            if chunk.start_time:
                chunk.actual_duration = (chunk.end_time - chunk.start_time).total_seconds()
    
    def fail_chunk(self, chunk_number: int, error_message: str):
        """Mark a chunk as failed."""
        if chunk_number in self.chunks:
            chunk = self.chunks[chunk_number]
            chunk.status = "failed"
            chunk.end_time = datetime.now()
            chunk.error_message = error_message
            
            if chunk.start_time:
                chunk.actual_duration = (chunk.end_time - chunk.start_time).total_seconds()
    
    def get_overall_progress(self) -> Dict:
        """Get overall processing progress statistics."""
        total_scenes = len(self.scenes)
        completed_scenes = sum(1 for s in self.scenes if s.status == "completed")
        failed_scenes = sum(1 for s in self.scenes if s.status == "failed")
        
        total_chunks = len(self.chunks)
        completed_chunks = sum(1 for c in self.chunks.values() if c.status == "completed")
        
        return {
            'total_scenes': total_scenes,
            'completed_scenes': completed_scenes,
            'failed_scenes': failed_scenes,
            'total_chunks': total_chunks,
            'completed_chunks': completed_chunks,
            'progress_percent': (completed_scenes / total_scenes * 100) if total_scenes > 0 else 0
        }
    
    def get_chunk_progress(self, chunk_number: int) -> Dict:
        """Get progress information for a specific chunk."""
        if chunk_number not in self.chunks:
            return {}
        
        chunk = self.chunks[chunk_number]
        progress_percent = (chunk.completed_scenes / chunk.total_scenes * 100) if chunk.total_scenes > 0 else 0
        
        return {
            'chunk_number': chunk_number,
            'status': chunk.status,
            'total_scenes': chunk.total_scenes,
            'completed_scenes': chunk.completed_scenes,
            'failed_scenes': chunk.failed_scenes,
            'progress_percent': progress_percent,
            'estimated_duration': chunk.estimated_duration,
            'actual_duration': chunk.actual_duration,
            'start_time': chunk.start_time,
            'output_file': chunk.output_file,
            'file_size': chunk.file_size,
            'failed_scene_names': chunk.failed_scene_names
        }
    
    def get_current_scene_info(self) -> Optional[Dict]:
        """Get information about the currently processing scene."""
        if self.current_scene is None or self.current_scene >= len(self.scenes):
            return None
        
        scene = self.scenes[self.current_scene]
        return {
            'movie_show': scene.movie_show,
            'chunk_number': scene.chunk_number,
            'scene_index': scene.scene_index,
            'duration': scene.duration,
            'status': scene.status
        }
    
    def get_eta_estimate(self) -> Optional[str]:
        """Calculate estimated time remaining based on average processing times."""
        if not self.scene_processing_times:
            return None
        
        # Calculate average processing time per scene
        avg_time = sum(self.scene_processing_times) / len(self.scene_processing_times)
        
        # Count remaining scenes
        remaining_scenes = sum(1 for s in self.scenes if s.status == "pending")
        
        if remaining_scenes == 0:
            return "Complete"
        
        # Calculate ETA
        estimated_seconds = remaining_scenes * avg_time
        eta_delta = timedelta(seconds=estimated_seconds)
        
        # Format as human readable
        if estimated_seconds < 60:
            return f"{int(estimated_seconds)}s"
        elif estimated_seconds < 3600:
            minutes = int(estimated_seconds // 60)
            seconds = int(estimated_seconds % 60)
            return f"{minutes}m {seconds}s"
        else:
            hours = int(estimated_seconds // 3600)
            minutes = int((estimated_seconds % 3600) // 60)
            return f"{hours}h {minutes}m"
    
    def get_average_scene_time(self) -> Optional[float]:
        """Get average processing time per scene."""
        if not self.scene_processing_times:
            return None
        return sum(self.scene_processing_times) / len(self.scene_processing_times)
    
    def get_processing_duration(self) -> Optional[str]:
        """Get total processing duration so far."""
        if not self.processing_start_time:
            return None
        
        duration = datetime.now() - self.processing_start_time
        total_seconds = duration.total_seconds()
        
        if total_seconds < 60:
            return f"{int(total_seconds)}s"
        elif total_seconds < 3600:
            minutes = int(total_seconds // 60)
            seconds = int(total_seconds % 60)
            return f"{minutes}m {seconds}s"
        else:
            hours = int(total_seconds // 3600)
            minutes = int((total_seconds % 3600) // 60)
            return f"{hours}h {minutes}m"
    
    def _parse_timecode(self, tc):
        """Parse a timecode string to seconds (reused from video_editor.py)."""
        if isinstance(tc, (int, float)):
            return float(tc)
        parts = str(tc).split(":")
        parts = [float(p) for p in parts]
        if len(parts) == 3:
            return parts[0]*3600 + parts[1]*60 + parts[2]
        elif len(parts) == 2:
            return parts[0]*60 + parts[1]
        elif len(parts) == 1:
            return parts[0]
        else:
            raise ValueError(f"Invalid timecode: {tc}") 