import os
import time
import subprocess
import json
import threading
import signal
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed, CancelledError
from queue import Queue
from moviepy.video.io.VideoFileClip import VideoFileClip
from moviepy import concatenate_videoclips
from moviepy.video.VideoClip import TextClip
from moviepy.video.compositing.CompositeVideoClip import CompositeVideoClip
from moviepy import vfx
import platform
from logger import ProgressLogger, OutputRedirector
from progress_tracker import ProgressTracker, ErrorType
from progress_ui import ProgressUI

# Global variable to track scene index across chunks
scene_index_offset = 0

# Thread-safe queue for progress updates
progress_queue = Queue()

# Global cache for video file clips to avoid re-loading the same files
_video_cache = {}
_cache_lock = threading.Lock()

# Global cancellation flag for graceful shutdown
_cancellation_event = threading.Event()

def signal_handler(signum, frame):
    """Handle Ctrl+C and other termination signals gracefully."""
    print("\n🛑 Received interrupt signal. Shutting down gracefully...")
    _cancellation_event.set()
    # Give threads a moment to clean up
    time.sleep(1)
    sys.exit(1)

# Register signal handlers
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

def get_cached_video_clip(video_path, logger=None):
    """
    Get a cached video clip or load it if not cached.
    This helps avoid re-loading the same video file multiple times.
    """
    with _cache_lock:
        if video_path in _video_cache:
            return _video_cache[video_path]
        
        try:
            clip = VideoFileClip(video_path, audio_fps=44100, audio_nbytes=2)
            _video_cache[video_path] = clip
            if logger:
                logger.log_info(f"Cached video file: {video_path}")
            return clip
        except Exception as e:
            if logger:
                logger.log_error(f"Failed to load video file {video_path}: {e}")
            return None

def clear_video_cache():
    """Clear the video cache and close all cached clips."""
    with _cache_lock:
        for clip in _video_cache.values():
            try:
                clip.close()
            except:
                pass
        _video_cache.clear()


def reset_cancellation():
    """Reset the cancellation event for new processing runs."""
    global _cancellation_event
    _cancellation_event.clear()


def is_cancelled():
    """Check if processing has been cancelled."""
    return _cancellation_event.is_set()

def get_audio_track_index(video_path, audio_title):
    """
    Get the audio track index for a given audio title using ffprobe.
    
    Args:
        video_path: Path to the video file
        audio_title: Title of the audio track to find
        
    Returns:
        Audio track index (0-based) or None if not found
    """
    try:
        # Use ffprobe to get audio track information
        cmd = [
            'ffprobe',
            '-v', 'quiet',
            '-print_format', 'json',
            '-show_streams',
            '-select_streams', 'a',  # Only audio streams
            video_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        data = json.loads(result.stdout)
        
        # Search for audio track with matching title
        for i, stream in enumerate(data.get('streams', [])):
            # Check various title fields that might contain the audio track title
            stream_title = stream.get('tags', {}).get('title', '')
            if stream_title and audio_title.lower() in stream_title.lower():
                return i
            
            # Also check language field
            language = stream.get('tags', {}).get('language', '')
            if language and audio_title.lower() in language.lower():
                return i
        
        # If no exact match found, return the first audio track (index 0)
        if data.get('streams'):
            return 0
            
        return None
        
    except (subprocess.CalledProcessError, json.JSONDecodeError, KeyError) as e:
        # If ffprobe fails, return None (will use default audio track)
        return None

def get_system_font():
    """Get a system font that works across platforms."""
    system = platform.system().lower()
    if system == "windows":
        # Use working lowercase font names for Windows (tested with MoviePy 2.1.2)
        fonts_to_try = ["arial", "calibri", "verdana", "tahoma", "georgia"]
        return fonts_to_try
    elif system == "darwin":  # macOS
        return ["Helvetica", "Arial", "Geneva"]
    else:  # Linux and others
        return ["Liberation-Sans", "Arial", "DejaVu-Sans"]

def parse_timecode(tc):
    """Parse a timecode string (HH:MM:SS or MM:SS or SS) to seconds."""
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

def parse_chunk_selection(chunk_str):
    """
    Parse chunk selection string into a list of chunk numbers.
    
    Supports:
    - Single chunks: "1" -> [1]
    - Comma-separated: "1,2,4" -> [1, 2, 4]
    - Ranges: "1-3" -> [1, 2, 3]
    - Mixed: "1,3-5,7" -> [1, 3, 4, 5, 7]
    
    Args:
        chunk_str: String specifying which chunks to process
        
    Returns:
        List of unique chunk numbers, sorted
        
    Raises:
        ValueError: If the format is invalid
    """
    if not chunk_str or not chunk_str.strip():
        raise ValueError("Chunk selection string cannot be empty")
    
    chunks = set()
    
    # Split by commas and process each part
    parts = [part.strip() for part in chunk_str.split(',')]
    
    for part in parts:
        if not part:
            continue
            
        if '-' in part:
            # Handle range
            range_parts = [p.strip() for p in part.split('-')]
            if len(range_parts) != 2:
                raise ValueError(f"Invalid range format: {part}")
            
            try:
                start = int(range_parts[0])
                end = int(range_parts[1])
            except ValueError:
                raise ValueError(f"Invalid range numbers: {part}")
            
            if start <= 0 or end <= 0:
                raise ValueError(f"Chunk numbers must be positive: {part}")
            
            if start > end:
                raise ValueError(f"Invalid range (start > end): {part}")
            
            chunks.update(range(start, end + 1))
        else:
            # Handle single number
            try:
                num = int(part)
            except ValueError:
                raise ValueError(f"Invalid chunk number: {part}")
            
            if num <= 0:
                raise ValueError(f"Chunk numbers must be positive: {part}")
            
            chunks.add(num)
    
    return sorted(list(chunks))

def create_scene_clip(scene, movie_folder, logger=None, tracker=None, scene_index=None):
    """
    Create a clip for a single scene with proper resource management.
    Returns the clip and its duration, or None if the scene can't be processed.
    """
    # Check for cancellation
    if _cancellation_event.is_set():
        if logger:
            logger.log_info(f"Cancelling scene processing for {scene['movie_show']}")
        return None, 0
    
    clip = None
    start_time = time.time()
    
    try:
        # Find the video file
        base_name = scene['movie_show'].replace(':', '').replace('/', '').replace(' ', '_')
        video_path = os.path.join(movie_folder, f"{scene['movie_show']}.mkv")
        if not os.path.exists(video_path):
            # Try with underscores
            video_path = os.path.join(movie_folder, f"{base_name}.mkv")
        if not os.path.exists(video_path):
            error_msg = f"Video file not found for scene: {scene['movie_show']} at {video_path}"
            if logger:
                logger.log_warning(error_msg)
            if tracker and scene_index is not None:
                tracker.fail_scene(scene_index, ErrorType.FILE_NOT_FOUND, error_msg)
            return None, 0
        
        start = parse_timecode(scene['start_timecode'])
        end = parse_timecode(scene['end_timecode'])
        
        # Get audio track index if audio_title is specified
        audio_track_index = None
        audio_title = scene.get('audio_title', '')
        if audio_title:
            audio_track_index = get_audio_track_index(video_path, audio_title)
            if audio_track_index is not None and logger:
                logger.log_info(f"Using audio track {audio_track_index} ('{audio_title}') for {scene['movie_show']}")
            elif audio_track_index is None and logger:
                logger.log_warning(f"Audio track '{audio_title}' not found for {scene['movie_show']}, using default")
        
        # Redirect FFmpeg output during clip creation
        with OutputRedirector(logger, "stderr") if logger else _no_op_context():
            # Create the base clip with audio track selection if specified
            if audio_track_index is not None:
                # Use ffmpeg-python to specify audio track
                import ffmpeg
                
                # Create input stream with audio track selection
                input_stream = ffmpeg.input(video_path)
                
                # Select specific audio track
                audio_stream = input_stream['a:' + str(audio_track_index)]
                video_stream = input_stream['v:0']
                
                # Create temporary file with selected audio track
                temp_output = video_path + f"_temp_audio_{audio_track_index}.mkv"
                
                try:
                    # Extract video and selected audio track
                    stream = ffmpeg.output(
                        video_stream, 
                        audio_stream, 
                        temp_output,
                        acodec='copy',
                        vcodec='copy'
                    )
                    ffmpeg.run(stream, overwrite_output=True, quiet=True)
                    
                    # Create clip from temporary file
                    clip = VideoFileClip(temp_output, audio_fps=44100, audio_nbytes=2).subclipped(start, end)
                    
                    # Clean up temporary file
                    if os.path.exists(temp_output):
                        os.remove(temp_output)
                        
                except Exception as e:
                    # Fallback to default audio track if selection fails
                    if logger:
                        logger.log_warning(f"Failed to select audio track {audio_track_index} for {scene['movie_show']}: {e}")
                    # Use cached clip if available, otherwise load directly
                    base_clip = get_cached_video_clip(video_path, logger)
                    if base_clip:
                        clip = base_clip.subclipped(start, end)
                    else:
                        clip = VideoFileClip(video_path, audio_fps=44100, audio_nbytes=2).subclipped(start, end)
            else:
                # Use cached clip if available, otherwise load directly
                base_clip = get_cached_video_clip(video_path, logger)
                if base_clip:
                    clip = base_clip.subclipped(start, end)
                else:
                    clip = VideoFileClip(video_path, audio_fps=44100, audio_nbytes=2).subclipped(start, end)
        
        # Try to add timeline overlay if present - make this completely optional
        date_text = scene.get('timeline_placement', '')
        if date_text:
            text_added = False
            fonts_to_try = get_system_font()
            
            # Build comprehensive timeline text
            timeline_text = date_text
            
            # Add movie/show name
            movie_show = scene.get('movie_show', '')
            if movie_show:
                timeline_text = f"{movie_show}\n{timeline_text}"
            
            # Add season/episode info if available
            season_episode = scene.get('season_episode', '')
            episode_title = scene.get('episode_title', '')
            if season_episode:
                if episode_title:
                    timeline_text = f"{timeline_text}\n{season_episode} - {episode_title}"
                else:
                    timeline_text = f"{timeline_text}\n{season_episode}"
            
            for font in fonts_to_try:
                try:
                    txt_clip = (
                        TextClip(
                            text=timeline_text,
                            font_size=72,  # Much larger for 1080p visibility
                            color='white',
                            font=font,
                            duration=3,  # Slightly longer duration to read the additional text
                            stroke_color='black',  # Add black outline for better visibility
                            stroke_width=2
                        )
                        .with_position(("right", "top"))
                        .with_effects([vfx.FadeOut(1.5)])
                    )
                    clip = CompositeVideoClip([clip, txt_clip]).with_duration(clip.duration)
                    text_added = True
                    break
                except Exception as font_error:
                    continue  # Try next font
            
            if not text_added and logger:
                logger.log_warning(f"Could not add text overlay for {scene['movie_show']}: No working fonts found")
        
        # Track successful completion
        processing_time = time.time() - start_time
        if tracker and scene_index is not None:
            tracker.complete_scene(scene_index, processing_time)
        
        return clip, clip.duration
        
    except Exception as e:
        error_msg = f"Could not process scene {scene['movie_show']} ({scene['start_timecode']} - {scene['end_timecode']}): {e}"
        
        # Determine error type
        error_type = ErrorType.PROCESSING_ERROR
        if "codec" in str(e).lower():
            error_type = ErrorType.CODEC_ERROR
        elif "permission" in str(e).lower():
            error_type = ErrorType.PERMISSION_ERROR
        
        if logger:
            logger.log_error(error_msg)
        if tracker and scene_index is not None:
            tracker.fail_scene(scene_index, error_type, error_msg)
        
        # Ensure cleanup if clip was partially created
        if clip is not None:
            try:
                clip.close()
            except:
                pass
        return None, 0


class _no_op_context:
    """No-op context manager for when logger is None."""
    def __enter__(self):
        return self
    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

def process_scenes(scenes, movie_folder, output_folder, chunk_duration=2*3600, chunk_selection=None, verbose=False):
    """
    Process the list of scenes and create the mega cut video chunks with enhanced UX.
    Each chunk is as close to two hours as possible, but scenes are never split.
    Args:
        scenes: List of scene dicts (from csv_parser.extract_scenes)
        movie_folder: Path to the folder containing all movie/show files
        output_folder: Path to the output folder for mega cut videos
        chunk_duration: Max duration (in seconds) for each output chunk (default: 2 hours)
        chunk_selection: List of chunk numbers to process (e.g., [1, 2, 4]). If None, process all chunks.
    """
    # Reset cancellation event for new processing run
    reset_cancellation()
    
    # Initialize progress tracking and logging
    logger = ProgressLogger()
    tracker = ProgressTracker()
    ui = ProgressUI(logger, tracker, debug=verbose)
    
    try:
        os.makedirs(output_folder, exist_ok=True)
        
        # Pre-analyze scenes and create chunk plan
        logger.log_info("Starting scene analysis and chunk planning...")
        chunks_map, valid_scenes = _analyze_and_plan_chunks(scenes, movie_folder, chunk_duration, logger)
        
        if not chunks_map:
            logger.log_error("No valid scenes found, aborting processing")
            return
        
        # Initialize tracker with the plan
        tracker.initialize_plan(valid_scenes, chunks_map)
        tracker.start_processing()
        
        # Display initial summary
        ui.display_initial_summary(chunk_selection)
        
        # Start the progress display system
        ui.start_progress_display()
        
        # Filter chunks based on selection
        chunks_to_process = {}
        if chunk_selection is not None:
            logger.log_info(f"Chunk selection specified: {chunk_selection}")
            total_chunks = len(chunks_map)
            
            for chunk_num in chunk_selection:
                if 1 <= chunk_num <= total_chunks:
                    chunks_to_process[chunk_num] = chunks_map[chunk_num]
                else:
                    logger.log_warning(f"Chunk {chunk_num} does not exist (total chunks: {total_chunks})")
            
            if not chunks_to_process:
                logger.log_warning("No valid chunks selected, nothing to process")
                return
        else:
            chunks_to_process = chunks_map
        
        # Process selected chunks in order
        for chunk_num in sorted(chunks_to_process.keys()):
            # Check for cancellation before processing each chunk
            if _cancellation_event.is_set():
                logger.log_info("Processing cancelled by user")
                break
                
            chunk_scenes = chunks_to_process[chunk_num]
            logger.log_info(f"Starting processing of chunk {chunk_num} with {len(chunk_scenes)} scenes")
            if verbose:
                print(f"[DEBUG] Processing chunk {chunk_num} with {len(chunk_scenes)} scenes")
            _process_single_chunk_with_progress(chunk_scenes, movie_folder, output_folder, 
                                              chunk_num, logger, tracker, ui, scene_index_offset)
            
            # Check for cancellation after each chunk
            if _cancellation_event.is_set():
                logger.log_info("Processing cancelled after chunk completion")
                break
        
        # Display completion status
        if verbose:
            print("[DEBUG] Processing complete, displaying final status")
        ui.display_complete_status()
        ui.display_error_summary()
        
    except Exception as e:
        logger.log_error(f"Fatal error during processing: {e}")
        print(f"\n❌ FATAL ERROR: {e}")
        print(f"📄 Check logs: {logger.log_file}")
    finally:
        # Ensure progress display is stopped
        ui.stop_progress_display()
        # Clear video cache to free memory
        clear_video_cache()
        logger.close()


def _analyze_and_plan_chunks(scenes, movie_folder, chunk_duration, logger):
    """
    Analyze scenes and create chunk planning without processing videos.
    Returns: (chunks_map, valid_scenes)
    """
    scene_durations = []
    valid_scenes = []
    
    logger.log_info("Analyzing scene durations and file availability...")
    
    for scene in scenes:
        # Check if video file exists
        base_name = scene['movie_show'].replace(':', '').replace('/', '').replace(' ', '_')
        video_path = os.path.join(movie_folder, f"{scene['movie_show']}.mkv")
        if not os.path.exists(video_path):
            video_path = os.path.join(movie_folder, f"{base_name}.mkv")
        if not os.path.exists(video_path):
            logger.log_warning(f"Video file not found for scene: {scene['movie_show']} at {video_path}")
            continue
            
        try:
            start = parse_timecode(scene['start_timecode'])
            end = parse_timecode(scene['end_timecode'])
            duration = end - start
            scene_durations.append(duration)
            valid_scenes.append(scene)
        except Exception as e:
            logger.log_error(f"Could not calculate duration for scene {scene['movie_show']}: {e}")
            continue

    # Group scenes into chunks
    logger.log_info("Grouping scenes into chunks...")
    chunks_map = {}
    current_chunk = []
    current_duration = 0
    chunk_number = 1
    
    for scene, dur in zip(valid_scenes, scene_durations):
        if current_duration + dur > chunk_duration and current_chunk:
            chunks_map[chunk_number] = current_chunk
            chunk_number += 1
            current_chunk = []
            current_duration = 0
        current_chunk.append(scene)
        current_duration += dur
        
    if current_chunk:
        chunks_map[chunk_number] = current_chunk
    
    logger.log_info(f"Created {len(chunks_map)} chunks from {len(valid_scenes)} valid scenes")
    
    return chunks_map, valid_scenes

def _process_single_chunk_with_progress(chunk_scenes, movie_folder, output_folder, chunk_number, logger, tracker, ui, current_scene_offset):
    """Process a single chunk with integrated progress tracking."""
    global scene_index_offset
    chunk_clips = []
    
    # Start chunk processing
    tracker.start_chunk(chunk_number)
    ui.update_chunk_progress(chunk_number)
    
    # Process each scene in the chunk
    for local_scene_idx, scene in enumerate(chunk_scenes):
        global_scene_idx = current_scene_offset + local_scene_idx
        
        # Start scene processing
        tracker.start_scene(global_scene_idx)
        ui.update_scene_progress(scene['movie_show'], local_scene_idx + 1, len(chunk_scenes))
        
        # Create the scene clip
        clip, duration = create_scene_clip(scene, movie_folder, logger, tracker, global_scene_idx)
        if clip is not None:
            chunk_clips.append(clip)
        
        # Update progress less frequently - only after scene completion
        if clip is not None:
            # Calculate processing time (use duration for simplicity)
            tracker.complete_scene(global_scene_idx, duration if duration else 0.0)
        else:
            tracker.fail_scene(global_scene_idx, ErrorType.PROCESSING_ERROR, "Failed to create clip")
        ui.update_chunk_progress(chunk_number)  # Only update after scene is done
    
    # Clear scene progress before rendering
    ui.complete_scene_progress()
    
    # Check if we have clips to render
    if chunk_clips:
        try:
            # Update render progress
            ui.update_render_progress(f"Concatenating {len(chunk_clips)} scenes...")
            
            # Concatenate clips
            if len(chunk_clips) == 1:
                final = chunk_clips[0]
            else:
                final = concatenate_videoclips(chunk_clips)
            
            # Update render progress for writing
            ui.update_render_progress(f"Writing video file...")
            
            # Write the final video
            output_path = os.path.join(output_folder, f"mega_cut_part_{chunk_number}.mp4")
            final.write_videofile(output_path)
            
            # Clean up clips
            for clip in chunk_clips:
                clip.close()
            final.close()
            
            # Complete rendering
            ui.complete_render_progress()
            
            # Complete chunk
            tracker.complete_chunk(chunk_number, output_path)
            logger.log_info(f"Chunk {chunk_number} completed successfully: {output_path}")
            
        except Exception as e:
            error_msg = f"Failed to render chunk {chunk_number}: {str(e)}"
            logger.log_error(error_msg)
            ui.show_error(error_msg)
            tracker.fail_chunk(chunk_number, str(e))
            ui.complete_render_progress()
    else:
        # No clips to render
        error_msg = f"No valid clips in chunk {chunk_number}"
        logger.log_warning(error_msg)
        tracker.fail_chunk(chunk_number, error_msg)
    
    # Final chunk update
    ui.update_chunk_progress(chunk_number)
    
    # Update scene index offset for next chunk
    scene_index_offset += len(chunk_scenes)


def _process_single_chunk(chunk_scenes, movie_folder, output_folder, chunk_number):
    """Legacy function - kept for compatibility but redirects to new implementation."""
    # Create minimal logger and tracker for legacy calls
    logger = ProgressLogger()
    tracker = ProgressTracker()
    ui = ProgressUI(logger, tracker)
    
    # Create a simple chunks map for this single chunk
    chunks_map = {chunk_number: chunk_scenes}
    tracker.initialize_plan(chunk_scenes, chunks_map)
    tracker.start_processing()
    
    try:
        _process_single_chunk_with_progress(chunk_scenes, movie_folder, output_folder, 
                                          chunk_number, logger, tracker, ui, 0)
    finally:
        # Clear video cache to free memory
        clear_video_cache()
        logger.close()


def process_scenes_threaded(scenes, movie_folder, output_folder, chunk_duration=2*3600, chunk_selection=None, verbose=False, max_workers=4):
    """
    Process scenes using threading for improved performance.
    
    Args:
        scenes: List of scene dicts (from csv_parser.extract_scenes)
        movie_folder: Path to the folder containing all movie/show files
        output_folder: Path to the output folder for mega cut videos
        chunk_duration: Max duration (in seconds) for each output chunk (default: 2 hours)
        chunk_selection: List of chunk numbers to process (e.g., [1, 2, 4]). If None, process all chunks.
        verbose: Enable verbose logging
        max_workers: Maximum number of worker threads for scene processing
    """
    # Reset cancellation event for new processing run
    reset_cancellation()
    
    # Initialize progress tracking and logging
    logger = ProgressLogger()
    tracker = ProgressTracker()
    ui = ProgressUI(logger, tracker, debug=verbose)
    
    try:
        os.makedirs(output_folder, exist_ok=True)
        
        # Pre-analyze scenes and create chunk plan
        logger.log_info("Starting scene analysis and chunk planning...")
        chunks_map, valid_scenes = _analyze_and_plan_chunks(scenes, movie_folder, chunk_duration, logger)
        
        if not chunks_map:
            logger.log_error("No valid scenes found, aborting processing")
            return
        
        # Initialize tracker with the plan
        tracker.initialize_plan(valid_scenes, chunks_map)
        tracker.start_processing()
        
        # Display initial summary
        ui.display_initial_summary(chunk_selection)
        
        # Start the progress display system
        ui.start_progress_display()
        
        # Filter chunks based on selection
        chunks_to_process = {}
        if chunk_selection is not None:
            logger.log_info(f"Chunk selection specified: {chunk_selection}")
            total_chunks = len(chunks_map)
            
            for chunk_num in chunk_selection:
                if 1 <= chunk_num <= total_chunks:
                    chunks_to_process[chunk_num] = chunks_map[chunk_num]
                else:
                    logger.log_warning(f"Chunk {chunk_num} does not exist (total chunks: {total_chunks})")
            
            if not chunks_to_process:
                logger.log_warning("No valid chunks selected, nothing to process")
                return
        else:
            chunks_to_process = chunks_map
        
        # Process selected chunks with threading
        for chunk_num in sorted(chunks_to_process.keys()):
            # Check for cancellation before processing each chunk
            if _cancellation_event.is_set():
                logger.log_info("Processing cancelled by user")
                break
                
            chunk_scenes = chunks_to_process[chunk_num]
            logger.log_info(f"Starting threaded processing of chunk {chunk_num} with {len(chunk_scenes)} scenes")
            if verbose:
                print(f"[DEBUG] Processing chunk {chunk_num} with {len(chunk_scenes)} scenes using {max_workers} threads")
            
            _process_single_chunk_threaded(chunk_scenes, movie_folder, output_folder, 
                                         chunk_num, logger, tracker, ui, scene_index_offset, max_workers)
            
            # Check for cancellation after each chunk
            if _cancellation_event.is_set():
                logger.log_info("Processing cancelled after chunk completion")
                break
        
        # Display completion status
        if verbose:
            print("[DEBUG] Processing complete, displaying final status")
        ui.display_complete_status()
        ui.display_error_summary()
        
    except Exception as e:
        logger.log_error(f"Fatal error during processing: {e}")
        print(f"\n❌ FATAL ERROR: {e}")
        print(f"📄 Check logs: {logger.log_file}")
    finally:
        # Ensure progress display is stopped
        ui.stop_progress_display()
        logger.close()


def _process_single_chunk_threaded(chunk_scenes, movie_folder, output_folder, chunk_number, logger, tracker, ui, current_scene_offset, max_workers):
    """Process a single chunk using threading for scene processing."""
    global scene_index_offset
    
    # Check for cancellation before starting
    if _cancellation_event.is_set():
        logger.log_info(f"Processing cancelled before starting chunk {chunk_number}")
        return
    
    # Start chunk processing
    tracker.start_chunk(chunk_number)
    ui.update_chunk_progress(chunk_number)
    
    # Process scenes in parallel using ThreadPoolExecutor
    chunk_clips = []
    completed_scenes = 0
    total_scenes = len(chunk_scenes)
    
    def process_scene_worker(scene_data):
        """Worker function to process a single scene."""
        local_scene_idx, scene = scene_data
        global_scene_idx = current_scene_offset + local_scene_idx
        
        # Check for cancellation periodically
        if _cancellation_event.is_set():
            logger.log_info(f"Cancelling scene processing for {scene['movie_show']}")
            return local_scene_idx, None, scene
        
        # Start scene processing
        tracker.start_scene(global_scene_idx)
        ui.update_scene_progress(scene['movie_show'], local_scene_idx + 1, total_scenes)
        
        # Create the scene clip
        clip, duration = create_scene_clip(scene, movie_folder, logger, tracker, global_scene_idx)
        
        # Update progress
        if clip is not None:
            tracker.complete_scene(global_scene_idx, duration if duration else 0.0)
        else:
            tracker.fail_scene(global_scene_idx, ErrorType.PROCESSING_ERROR, "Failed to create clip")
        
        return local_scene_idx, clip, scene
    
    # Create scene data for threading
    scene_data = [(i, scene) for i, scene in enumerate(chunk_scenes)]
    
    # Process scenes in parallel
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all scenes for processing
        future_to_scene = {executor.submit(process_scene_worker, data): data for data in scene_data}
        
        # Collect results as they complete
        for future in as_completed(future_to_scene):
            # Check for cancellation
            if _cancellation_event.is_set():
                logger.log_info(f"Cancelling chunk {chunk_number} processing")
                # Cancel remaining futures
                for f in future_to_scene:
                    if not f.done():
                        f.cancel()
                break
            
            try:
                local_scene_idx, clip, scene = future.result()
                if clip is not None:
                    chunk_clips.append((local_scene_idx, clip))
                completed_scenes += 1
                
                # Update progress
                ui.update_chunk_progress(chunk_number)
                
            except CancelledError:
                logger.log_info(f"Scene processing cancelled for chunk {chunk_number}")
                break
            except Exception as e:
                local_scene_idx, scene = future_to_scene[future]
                error_msg = f"Thread error processing scene {scene['movie_show']}: {e}"
                logger.log_error(error_msg)
                completed_scenes += 1
    
    # Check for cancellation before rendering
    if _cancellation_event.is_set():
        logger.log_info(f"Cancelling rendering for chunk {chunk_number}")
        return
    
    # Sort clips by original scene order
    chunk_clips.sort(key=lambda x: x[0])
    final_clips = [clip for _, clip in chunk_clips]
    
    # Clear scene progress before rendering
    ui.complete_scene_progress()
    
    # Check if we have clips to render
    if final_clips:
        try:
            # Update render progress
            ui.update_render_progress(f"Concatenating {len(final_clips)} scenes...")
            
            # Concatenate clips
            if len(final_clips) == 1:
                final = final_clips[0]
            else:
                final = concatenate_videoclips(final_clips)
            
            # Update render progress for writing
            ui.update_render_progress(f"Writing video file...")
            
            # Write the final video
            output_path = os.path.join(output_folder, f"mega_cut_part_{chunk_number}.mp4")
            final.write_videofile(output_path)
            
            # Clean up clips
            for clip in final_clips:
                clip.close()
            final.close()
            
            # Complete rendering
            ui.complete_render_progress()
            
            # Complete chunk
            tracker.complete_chunk(chunk_number, output_path)
            logger.log_info(f"Chunk {chunk_number} completed successfully: {output_path}")
            
        except Exception as e:
            error_msg = f"Failed to render chunk {chunk_number}: {str(e)}"
            logger.log_error(error_msg)
            ui.show_error(error_msg)
            tracker.fail_chunk(chunk_number, str(e))
            ui.complete_render_progress()
    else:
        # No clips to render
        error_msg = f"No valid clips in chunk {chunk_number}"
        logger.log_warning(error_msg)
        tracker.fail_chunk(chunk_number, error_msg)
    
    # Final chunk update
    ui.update_chunk_progress(chunk_number)
    
    # Update scene index offset for next chunk
    scene_index_offset += len(chunk_scenes) 


def process_scenes_with_options(scenes, movie_folder, output_folder, chunk_duration=2*3600, chunk_selection=None, verbose=False, use_threading=True, max_workers=4):
    """
    Process scenes with option to use threading or sequential processing.
    
    Args:
        scenes: List of scene dicts (from csv_parser.extract_scenes)
        movie_folder: Path to the folder containing all movie/show files
        output_folder: Path to the output folder for mega cut videos
        chunk_duration: Max duration (in seconds) for each output chunk (default: 2 hours)
        chunk_selection: List of chunk numbers to process (e.g., [1, 2, 4]). If None, process all chunks.
        verbose: Enable verbose logging
        use_threading: Whether to use threaded processing (default: True)
        max_workers: Maximum number of worker threads (only used if use_threading=True)
    """
    # Reset cancellation event for new processing run
    reset_cancellation()
    
    if use_threading:
        return process_scenes_threaded(scenes, movie_folder, output_folder, chunk_duration, chunk_selection, verbose, max_workers)
    else:
        return process_scenes(scenes, movie_folder, output_folder, chunk_duration, chunk_selection, verbose) 