#!/usr/bin/env python3
"""
Test script for the new set-audio-track command functionality.
"""

import os
import tempfile
import pandas as pd
from main import set_movie_audio_track

def test_set_audio_track():
    """Test the set_movie_audio_track function with various scenarios."""
    
    # Create a temporary CSV file for testing
    test_data = [
        {
            'movie_show': 'Black Panther',
            'season_episode': '',
            'episode_title': '',
            'start_timecode': '0:00:14',
            'end_timecode': '0:01:45',
            'timeline_placement': '2,500,000 BCE',
            'comment': 'Prologue scene',
            'language': 'en',
            'audio_title': 'Original Audio',
            'reality_designation': 'EARTH-199999'
        },
        {
            'movie_show': 'Thor: The Dark World',
            'season_episode': '',
            'episode_title': '',
            'start_timecode': '0:00:35',
            'end_timecode': '0:03:39',
            'timeline_placement': '2988 BCE',
            'comment': 'Prologue scene',
            'language': 'en',
            'audio_title': 'Original Audio',
            'reality_designation': 'EARTH-199999'
        },
        {
            'movie_show': 'Black Panther',
            'season_episode': '',
            'episode_title': '',
            'start_timecode': '0:05:00',
            'end_timecode': '0:07:30',
            'timeline_placement': '1992',
            'comment': 'Another scene',
            'language': 'en',
            'audio_title': 'Original Audio',
            'reality_designation': 'EARTH-199999'
        }
    ]
    
    # Create temporary file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        df = pd.DataFrame(test_data)
        df.to_csv(f.name, index=False)
        temp_csv_path = f.name
    
    try:
        print("Testing set_movie_audio_track function...")
        
        # Test 1: Update audio track for existing movie
        print("\n1. Testing audio track update for 'Black Panther' to 'English (Vegamovies.NL) [8ch]'...")
        result = set_movie_audio_track(temp_csv_path, "Black Panther", "English (Vegamovies.NL) [8ch]")
        assert result == True, "Should successfully update audio track"
        
        # Verify the change
        df = pd.read_csv(temp_csv_path)
        black_panther_rows = df[df['movie_show'] == 'Black Panther']
        assert all(black_panther_rows['audio_title'] == 'English (Vegamovies.NL) [8ch]'), "All Black Panther scenes should have the new audio track"
        print("✅ Success: Black Panther audio track updated")
        
        # Test 2: Case-insensitive matching
        print("\n2. Testing case-insensitive matching with 'black panther'...")
        result = set_movie_audio_track(temp_csv_path, "black panther", "Spanish (Dual Audio) [5.1]")
        assert result == True, "Should successfully update audio track with case-insensitive matching"
        
        # Verify the change
        df = pd.read_csv(temp_csv_path)
        black_panther_rows = df[df['movie_show'] == 'Black Panther']
        assert all(black_panther_rows['audio_title'] == 'Spanish (Dual Audio) [5.1]'), "All Black Panther scenes should have the new audio track"
        print("✅ Success: Case-insensitive matching works")
        
        # Test 3: Non-existent movie
        print("\n3. Testing non-existent movie...")
        result = set_movie_audio_track(temp_csv_path, "Non-existent Movie", "German Audio [7.1]")
        assert result == False, "Should return False for non-existent movie"
        print("✅ Success: Properly handles non-existent movies")
        
        # Test 4: Update specific movie (Thor)
        print("\n4. Testing audio track update for 'Thor: The Dark World' to 'French (DTS-HD) [7.1]'...")
        result = set_movie_audio_track(temp_csv_path, "Thor: The Dark World", "French (DTS-HD) [7.1]")
        assert result == True, "Should successfully update audio track"
        
        # Verify the change
        df = pd.read_csv(temp_csv_path)
        thor_rows = df[df['movie_show'] == 'Thor: The Dark World']
        assert all(thor_rows['audio_title'] == 'French (DTS-HD) [7.1]'), "All Thor scenes should have the new audio track"
        print("✅ Success: Thor audio track updated")
        
        print("\n🎉 All tests passed!")
        
    finally:
        # Clean up temporary file
        os.unlink(temp_csv_path)

if __name__ == '__main__':
    test_set_audio_track() 