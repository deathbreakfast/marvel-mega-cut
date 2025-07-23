import os
from moviepy.video.io.VideoFileClip import VideoFileClip
from moviepy import concatenate_videoclips
from moviepy.video.VideoClip import TextClip
from moviepy.video.compositing.CompositeVideoClip import CompositeVideoClip
from moviepy import vfx

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

def create_scene_clip(scene, movie_folder):
    """
    Create a clip for a single scene with proper resource management.
    Returns the clip and its duration, or None if the scene can't be processed.
    """
    # Find the video file
    base_name = scene['movie_show'].replace(':', '').replace('/', '').replace(' ', '_')
    video_path = os.path.join(movie_folder, f"{scene['movie_show']}.mkv")
    if not os.path.exists(video_path):
        # Try with underscores
        video_path = os.path.join(movie_folder, f"{base_name}.mkv")
    if not os.path.exists(video_path):
        print(f"[WARN] Video file not found for scene: {scene['movie_show']} at {video_path}")
        return None, 0
    
    try:
        start = parse_timecode(scene['start_timecode'])
        end = parse_timecode(scene['end_timecode'])
        
        # Create the base clip
        clip = VideoFileClip(video_path).subclipped(start, end)
        
        # Add timeline overlay if present
        date_text = scene.get('timeline_placement', '')
        if date_text:
            txt_clip = (
                TextClip(
                    text=date_text,
                    font_size=24,
                    color='white',
                    font='DejaVuSans',
                    bg_color=None,
                    size=(clip.w//2, 40),
                    method='caption',
                    duration=clip.duration
                )
                .with_position(("right", "top"))
                .with_end(2)
                .with_effects([vfx.FadeOut(1)])
            )
            clip = CompositeVideoClip([clip, txt_clip]).with_duration(clip.duration)
        
        return clip, clip.duration
        
    except Exception as e:
        print(f"[ERROR] Could not process scene {scene['movie_show']} ({scene['start_timecode']} - {scene['end_timecode']}): {e}")
        return None, 0

def process_scenes(scenes, movie_folder, output_folder, chunk_duration=2*3600):
    """
    Process the list of scenes and create the mega cut video chunks.
    Each chunk is as close to two hours as possible, but scenes are never split.
    Args:
        scenes: List of scene dicts (from csv_parser.extract_scenes)
        movie_folder: Path to the folder containing all movie/show files
        output_folder: Path to the output folder for mega cut videos
        chunk_duration: Max duration (in seconds) for each output chunk (default: 2 hours)
    """
    os.makedirs(output_folder, exist_ok=True)
    
    # Calculate scene durations and group into chunks without creating clips yet
    scene_durations = []
    valid_scenes = []
    
    print("[INFO] Calculating scene durations...")
    for scene in scenes:
        # Just calculate duration without creating clips
        base_name = scene['movie_show'].replace(':', '').replace('/', '').replace(' ', '_')
        video_path = os.path.join(movie_folder, f"{scene['movie_show']}.mkv")
        if not os.path.exists(video_path):
            video_path = os.path.join(movie_folder, f"{base_name}.mkv")
        if not os.path.exists(video_path):
            print(f"[WARN] Video file not found for scene: {scene['movie_show']} at {video_path}")
            continue
            
        try:
            start = parse_timecode(scene['start_timecode'])
            end = parse_timecode(scene['end_timecode'])
            duration = end - start
            scene_durations.append(duration)
            valid_scenes.append(scene)
        except Exception as e:
            print(f"[ERROR] Could not calculate duration for scene {scene['movie_show']}: {e}")
            continue

    # Group scenes into chunks
    print("[INFO] Grouping scenes into chunks...")
    chunks = []
    current_chunk = []
    current_duration = 0
    
    for idx, (scene, dur) in enumerate(zip(valid_scenes, scene_durations)):
        if current_duration + dur > chunk_duration and current_chunk:
            chunks.append(current_chunk)
            current_chunk = []
            current_duration = 0
        current_chunk.append(scene)
        current_duration += dur
        
    if current_chunk:
        chunks.append(current_chunk)

    # Process each chunk
    for i, chunk_scenes in enumerate(chunks, 1):
        print(f"[INFO] Processing chunk {i} with {len(chunk_scenes)} scenes...")
        
        # Create clips for this chunk only
        chunk_clips = []
        for scene in chunk_scenes:
            clip, duration = create_scene_clip(scene, movie_folder)
            if clip is not None:
                chunk_clips.append(clip)
        
        if not chunk_clips:
            print(f"[WARN] No valid clips in chunk {i}, skipping...")
            continue
            
        # Concatenate and render
        out_path = os.path.join(output_folder, f"mega_cut_part_{i}.mp4")
        print(f"[INFO] Rendering chunk {i} to {out_path}")
        
        try:
            final = concatenate_videoclips(chunk_clips, method="compose", padding=-1)
            final.write_videofile(out_path, codec="libx264", audio_codec="aac")
            
            # Clean up resources immediately after rendering
            final.close()
            for clip in chunk_clips:
                clip.close()
                
        except Exception as e:
            print(f"[ERROR] Failed to render chunk {i}: {e}")
            # Clean up even if rendering failed
            for clip in chunk_clips:
                try:
                    clip.close()
                except:
                    pass
            continue
        
        print(f"[INFO] Successfully rendered chunk {i}") 