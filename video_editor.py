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
    clips = []
    scene_durations = []
    for scene in scenes:
        # Find the video file (simple heuristic: movie_show + .mp4)
        # You may want to improve this for real use cases
        base_name = scene['movie_show'].replace(':', '').replace('/', '').replace(' ', '_')
        video_path = os.path.join(movie_folder, f"{scene['movie_show']}.mp4")
        if not os.path.exists(video_path):
            # Try with underscores
            video_path = os.path.join(movie_folder, f"{base_name}.mp4")
        if not os.path.exists(video_path):
            print(f"[WARN] Video file not found for scene: {scene['movie_show']} at {video_path}")
            continue
        try:
            start = parse_timecode(scene['start_timecode'])
            end = parse_timecode(scene['end_timecode'])
            clip = VideoFileClip(video_path).subclipped(start, end)
            # Overlay timeline_placement (date) in the top right corner
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
            clips.append(clip)
            scene_durations.append(clip.duration)
        except Exception as e:
            print(f"[ERROR] Could not process scene {scene['movie_show']} ({scene['start_timecode']} - {scene['end_timecode']}): {e}")
            continue

    # Split into ~2 hour chunks, do not split scenes
    chunks = []
    current_chunk = []
    current_duration = 0
    current_indices = []
    chunk_indices = []
    for idx, (clip, dur) in enumerate(zip(clips, scene_durations)):
        if current_duration + dur > chunk_duration and current_chunk:
            chunks.append(current_chunk)
            chunk_indices.append(current_indices)
            current_chunk = []
            current_indices = []
            current_duration = 0
        current_chunk.append(clip)
        current_indices.append(idx)
        current_duration += dur
    if current_chunk:
        chunks.append(current_chunk)
        chunk_indices.append(current_indices)

    # Render each chunk
    for i, (chunk, indices) in enumerate(zip(chunks, chunk_indices), 1):
        processed_chunk = []
        for j, (clip, scene_idx) in enumerate(zip(chunk, indices)):
            # Rebuild the base VideoFileClip and overlay for each scene
            scene = scenes[scene_idx]
            base_name = scene['movie_show'].replace(':', '').replace('/', '').replace(' ', '_')
            video_path = os.path.join(movie_folder, f"{scene['movie_show']}.mp4")
            if not os.path.exists(video_path):
                video_path = os.path.join(movie_folder, f"{base_name}.mp4")
            start = parse_timecode(scene['start_timecode'])
            end = parse_timecode(scene['end_timecode'])
            base_clip = VideoFileClip(video_path).subclipped(start, end)
            date_text = scene.get('timeline_placement', '')
            if date_text:
                txt_clip = (
                    TextClip(
                        text=date_text,
                        font_size=24,
                        color='white',
                        font='DejaVuSans',
                        bg_color=None,
                        size=(base_clip.w//2, 40),
                        method='caption',
                        duration=base_clip.duration
                    )
                    .with_position(("right", "top"))
                    .with_end(2)
                    .with_effects([vfx.FadeOut(1)])
                )
                base_clip = CompositeVideoClip([base_clip, txt_clip]).with_duration(base_clip.duration)
            processed_chunk.append(base_clip)
        out_path = os.path.join(output_folder, f"mega_cut_part_{i}.mp4")
        print(f"[INFO] Rendering chunk {i} with {len(processed_chunk)} scenes to {out_path}")
        final = concatenate_videoclips(processed_chunk, method="compose", padding=-1)
        final.write_videofile(out_path, codec="libx264", audio_codec="aac")
        for c in processed_chunk:
            c.close()
        final.close() 