import pytest
import os
import cv2
import pytesseract
from moviepy.video.VideoClip import TextClip
from moviepy.video.io.VideoFileClip import VideoFileClip
from moviepy.video.compositing.CompositeVideoClip import CompositeVideoClip
from video_editor import process_scenes
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
        path = os.path.join(TEST_VIDEO_DIR, f'{title}.mp4')
        if not os.path.exists(path):
            clip = TextClip(
                text=title,
                font_size=70,
                color='white',
                size=(640, 360),
                bg_color='black',
                method='caption',
                font='DejaVuSans',
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

def test_process_scenes():
    scenes = extract_scenes(TEST_CSV)
    process_scenes(scenes, TEST_VIDEO_DIR, TEST_OUTPUT_DIR)
    # Find all output files
    output_files = [f for f in os.listdir(TEST_OUTPUT_DIR) if f.endswith('.mp4')]
    assert output_files, "No output video files were created."

    # Validate that the test videos were created and contain the expected titles using OCR
    for title in ['Test Movie 1', 'Test Show', 'Test Movie 2']:
        video_path = os.path.join(TEST_VIDEO_DIR, f'{title}.mp4')
        assert os.path.exists(video_path), f"Test video {title}.mp4 was not created."
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