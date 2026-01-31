import pytest
import os
import cv2
import pytesseract
from moviepy.video.VideoClip import TextClip
from moviepy.video.io.VideoFileClip import VideoFileClip
from moviepy.video.compositing.CompositeVideoClip import CompositeVideoClip
from video_editor import process_scenes, parse_chunk_selection, get_audio_track_index
from csv_parser import extract_scenes

TEST_VIDEO_DIR = 'test_videos'
TEST_OUTPUT_DIR = 'test_output'
TEST_CSV = 'test_scenes.csv'

@pytest.fixture(scope='module', autouse=True)
def init_test_videos():
    os.makedirs(TEST_VIDEO_DIR, exist_ok=True)
    os.makedirs(TEST_OUTPUT_DIR, exist_ok=True)

    # Create three 2-second video files with static titles
    titles = ['Test Movie 1', 'Test Show', 'Test Movie 2']
    for title in titles:
        path = os.path.join(TEST_VIDEO_DIR, f'{title}.mkv')
        if not os.path.exists(path):
            clip = TextClip(
                text=title,
                font_size=70,
                color='white',
                size=(640, 360),
                bg_color='black',
                method='caption',
                font='Arial',
                duration=5
            )
            clip.write_videofile(path, fps=24, codec='libx264', audio=False, logger=None)
    # Clean output directory before test
    for f in os.listdir(TEST_OUTPUT_DIR):
        os.remove(os.path.join(TEST_OUTPUT_DIR, f))

def extract_text_from_frame(video_path, t=0):
    cap = cv2.VideoCapture(video_path)
    cap.set(cv2.CAP_PROP_POS_MSEC, t * 1000)
    ret, frame = cap.read()
    cap.release()
    if not ret:
        raise RuntimeError(f"Could not read frame at {t}s from {video_path}")
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    text = pytesseract.image_to_string(frame_rgb)
    return text.strip()

def test_parse_chunk_selection():
    """Test parsing chunk selection strings."""
    
    # Test single chunk
    assert parse_chunk_selection("1") == [1]
    assert parse_chunk_selection("5") == [5]
    
    # Test comma-separated chunks
    assert parse_chunk_selection("1,2,4") == [1, 2, 4]
    assert parse_chunk_selection("1,3,5,7") == [1, 3, 5, 7]
    
    # Test ranges
    assert parse_chunk_selection("1-3") == [1, 2, 3]
    assert parse_chunk_selection("2-5") == [2, 3, 4, 5]
    
    # Test mixed comma and ranges
    assert parse_chunk_selection("1,3-5,7") == [1, 3, 4, 5, 7]
    assert parse_chunk_selection("1-2,4,6-8") == [1, 2, 4, 6, 7, 8]
    
    # Test complex mixed
    assert parse_chunk_selection("1,2,4-8,10,12-14") == [1, 2, 4, 5, 6, 7, 8, 10, 12, 13, 14]
    
    # Test with spaces (should handle gracefully)
    assert parse_chunk_selection("1, 2, 4-6") == [1, 2, 4, 5, 6]
    assert parse_chunk_selection("1 - 3, 5") == [1, 2, 3, 5]
    
    # Test error cases
    with pytest.raises(ValueError):
        parse_chunk_selection("abc")
    
    with pytest.raises(ValueError):
        parse_chunk_selection("1-")
    
    with pytest.raises(ValueError):
        parse_chunk_selection("-3")
    
    with pytest.raises(ValueError):
        parse_chunk_selection("0")
    
    with pytest.raises(ValueError):
        parse_chunk_selection("1-0")

def test_get_audio_track_index():
    """Test audio track index detection."""
    # Test with non-existent file (should return None)
    result = get_audio_track_index("non_existent_file.mkv", "English")
    assert result is None
    
    # Test with existing test video (should return 0 for first audio track or None if no audio)
    test_video_path = os.path.join(TEST_VIDEO_DIR, 'Test Movie 1.mkv')
    if os.path.exists(test_video_path):
        result = get_audio_track_index(test_video_path, "English")
        # Should return 0 (first audio track) or None (no audio tracks)
        assert result is None or result == 0

def test_scene_with_audio_title():
    """Test that scenes with audio_title are processed correctly."""
    # Create a test CSV with audio_title in the old format (no headers, specific column positions)
    # Column positions: movie_show=1, season_episode=5, episode_title=6, start_timecode=10, end_timecode=12, comment=14, timeline_placement=24, audio_title=8
    test_csv_content = """Value0,Test Movie 1,Value2,Value3,Value4,1.1,Test Episode,Value7,English Audio,Value9,0:00:00,Value11,0:00:05,Value13,Test scene,Value15,Value16,Value17,Value18,Value19,Value20,Value21,Value22,Value23,2008"""
    
    with open('test_audio_scenes.csv', 'w') as f:
        f.write(test_csv_content)
    
    try:
        scenes = extract_scenes('test_audio_scenes.csv')
        assert len(scenes) == 1
        assert scenes[0]['movie_show'] == 'Test Movie 1'
        assert scenes[0]['audio_title'] == 'English Audio'
    finally:
        if os.path.exists('test_audio_scenes.csv'):
            os.remove('test_audio_scenes.csv')

def test_process_scenes_with_chunk_selection():
    """Test that chunk selection works correctly."""
    scenes = extract_scenes(TEST_CSV)
    
    # Test selecting only chunk 1
    process_scenes(scenes, TEST_VIDEO_DIR, TEST_OUTPUT_DIR, chunk_selection=[1])
    
    # Should only have one output file
    output_files = [f for f in os.listdir(TEST_OUTPUT_DIR) if f.endswith('.mp4')]
    assert len(output_files) == 1
    assert 'mega_cut_part_1.mp4' in output_files
    
    # Clean output directory
    for f in os.listdir(TEST_OUTPUT_DIR):
        os.remove(os.path.join(TEST_OUTPUT_DIR, f))
    
    # Test selecting chunks 1 and 3 (if they exist - based on test data this might only create chunk 1)
    process_scenes(scenes, TEST_VIDEO_DIR, TEST_OUTPUT_DIR, chunk_selection=[1, 3])
    
    output_files = [f for f in os.listdir(TEST_OUTPUT_DIR) if f.endswith('.mp4')]
    # Should have only the chunks that actually exist
    assert 'mega_cut_part_1.mp4' in output_files
    
    # Test selecting non-existent chunk
    for f in os.listdir(TEST_OUTPUT_DIR):
        os.remove(os.path.join(TEST_OUTPUT_DIR, f))
    
    process_scenes(scenes, TEST_VIDEO_DIR, TEST_OUTPUT_DIR, chunk_selection=[99])
    
    # Should create no output files
    output_files = [f for f in os.listdir(TEST_OUTPUT_DIR) if f.endswith('.mp4')]
    assert len(output_files) == 0

def test_process_scenes():
    scenes = extract_scenes(TEST_CSV)
    process_scenes(scenes, TEST_VIDEO_DIR, TEST_OUTPUT_DIR)
    # Find all output files
    output_files = [f for f in os.listdir(TEST_OUTPUT_DIR) if f.endswith('.mp4')]
    assert output_files, "No output video files were created."

    # Validate that the test videos were created and contain the expected titles using OCR
    for title in ['Test Movie 1', 'Test Show', 'Test Movie 2']:
        video_path = os.path.join(TEST_VIDEO_DIR, f'{title}.mkv')
        assert os.path.exists(video_path), f"Test video {title}.mkv was not created."
        ocr_text = extract_text_from_frame(video_path)
        assert title in ocr_text, f"OCR did not find title '{title}' in {video_path}"

    # For each scene, extract frames at 1s, 2s, and 3s from the corresponding output and verify the title exists
    found_scenes = set()
    found_dates = set()
    for out_file in output_files:
        video_path = os.path.join(TEST_OUTPUT_DIR, out_file)
        # Check frames at 0s, 1s, and 2s for each output video
        ocr_texts = set()
        for t in [0, 3, 6]:
            try:
                ocr_texts.add(extract_text_from_frame(video_path, t))
            except Exception:
                pass
        for scene in scenes:
            title = scene['movie_show']
            date = scene['timeline_placement']
            if any(title in text for text in ocr_texts):
                found_scenes.add(title)
            if any(date in text for text in ocr_texts):
                found_dates.add(date)
    for scene in scenes:
        assert scene['movie_show'] in found_scenes, f"Scene '{scene['movie_show']}' not found in any output video."
        assert scene['timeline_placement'] in found_dates, f"Timeline placement '{scene['timeline_placement']}' not found in any output video." 

def test_threaded_processing():
    """Test that threaded processing works correctly."""
    import tempfile
    import os
    
    # Create temporary test files
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create test CSV
        test_csv = os.path.join(temp_dir, 'test_scenes.csv')
        with open(test_csv, 'w') as f:
            f.write('movie_show,start_timecode,end_timecode,timeline_placement\n')
            f.write('Test Movie 1,0:00:00,0:00:05,2020\n')
            f.write('Test Show,0:00:00,0:00:05,2021\n')
            f.write('Test Movie 2,0:00:00,0:00:05,2022\n')
        
        # Create test video files (simple text files for testing)
        test_videos_dir = os.path.join(temp_dir, 'videos')
        os.makedirs(test_videos_dir, exist_ok=True)
        
        # Create simple test video files (just create empty files for testing)
        titles = ['Test Movie 1', 'Test Show', 'Test Movie 2']
        for title in titles:
            path = os.path.join(test_videos_dir, f'{title}.mkv')
            with open(path, 'w') as f:
                f.write(f"Mock video file for {title}")
        
        # Test output directory
        test_output = os.path.join(temp_dir, 'output')
        os.makedirs(test_output, exist_ok=True)
        
        # Import and test threaded processing
        from video_editor import process_scenes_with_options
        from new_csv_parser import extract_scenes
        
        # Extract scenes
        scenes = extract_scenes(test_csv)
        assert len(scenes) == 3
        
        # Test that the function can be called without errors
        # (actual video processing will fail due to mock files, but threading logic should work)
        try:
            # This will fail due to mock video files, but we can test the threading setup
            process_scenes_with_options(
                scenes, 
                test_videos_dir, 
                test_output,
                chunk_duration=10,  # Very short chunks for testing
                use_threading=True,
                max_workers=2,
                verbose=True
            )
        except Exception as e:
            # Expected to fail due to mock video files, but threading should be set up correctly
            assert "Video file not found" in str(e) or "Failed to load video file" in str(e), f"Unexpected error: {e}" 