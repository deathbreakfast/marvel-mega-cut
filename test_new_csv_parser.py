import os
import tempfile
import pandas as pd
from new_csv_parser import extract_scenes, create_sample_csv

def test_new_csv_parser():
    """Test the new CSV parser with a sample file."""
    
    # Create a temporary CSV file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
        csv_content = """movie_show,season_episode,episode_title,start_timecode,end_timecode,timeline_placement,comment,language,audio_title,reality_designation
Black Panther,,,0:00:14,0:01:45,"2,500,000 BCE",Prologue: N'Jobu narrating the story of the first Black Panther and the formation of Wakanda to his son N'Jadaka (Erik).,en,Original Audio,EARTH-199999
Agents of S.H.I.E.L.D.,3.19,Failed Experiments,0:00:45,0:01:35,3500 BCE,NOTE: During this flashback sequence Hive is telling the story of his Inhuman transformation (Terrigenesis) in the present.,en,Original Audio,EARTH-199999
Thor: The Dark World,,,0:00:35,0:03:39,2988 BCE,Prologue: Odin narrating the story of The Convergence,en,Original Audio,EARTH-199999
Loki,S01E02,The Variant,0:24:56,0:27:24,79,Loki and Mobius visiting Pompeii just prior to the eruption of Mount Vesuvius,es,Spanish Audio,EARTH-199999
"""
        f.write(csv_content)
        temp_csv_path = f.name
    
    try:
        # Test extraction
        scenes = extract_scenes(temp_csv_path)
        
        print(f"Extracted {len(scenes)} scenes")
        
        # Verify scene structure
        assert len(scenes) == 4, f"Expected 4 scenes, got {len(scenes)}"
        
        # Check first scene
        first_scene = scenes[0]
        assert first_scene['movie_show'] == 'Black Panther'
        assert first_scene['start_timecode'] == '0:00:14'
        assert first_scene['end_timecode'] == '0:01:45'
        assert first_scene['timeline_placement'] == '2,500,000 BCE'
        assert first_scene['language'] == 'en'
        assert first_scene['audio_title'] == 'Original Audio'
        
        # Check scene with optional fields
        third_scene = scenes[2]
        assert third_scene['movie_show'] == 'Thor: The Dark World'
        assert 'season_episode' not in third_scene  # Should not be included if empty
        assert 'episode_title' not in third_scene   # Should not be included if empty
        
        # Check scene with language and audio variations
        fourth_scene = scenes[3]
        assert fourth_scene['language'] == 'es'
        assert fourth_scene['audio_title'] == 'Spanish Audio'
        
        print("✅ All tests passed!")
        
    finally:
        # Clean up
        os.unlink(temp_csv_path)

def test_create_sample_csv():
    """Test creating a sample CSV file."""
    
    with tempfile.NamedTemporaryFile(suffix='.csv', delete=False) as f:
        temp_csv_path = f.name
    
    try:
        # Create sample CSV
        create_sample_csv(temp_csv_path)
        
        # Verify it was created
        assert os.path.exists(temp_csv_path)
        
        # Read and verify content
        scenes = extract_scenes(temp_csv_path)
        assert len(scenes) == 3
        
        print("✅ Sample CSV creation test passed!")
        
    finally:
        # Clean up
        os.unlink(temp_csv_path)

if __name__ == '__main__':
    print("Testing new CSV parser...")
    test_new_csv_parser()
    test_create_sample_csv()
    print("All tests completed!") 