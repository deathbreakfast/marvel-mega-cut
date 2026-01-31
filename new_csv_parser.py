import pandas as pd
from typing import List, Dict, Optional
import csv

def extract_scenes(csv_path: str) -> List[Dict[str, Optional[str]]]:
    """
    Extracts scenes from the new simplified CSV format.
    
    Expected CSV columns:
    1. movie_show (required)
    2. season_episode (optional)
    3. episode_title (optional)
    4. start_timecode (required)
    5. end_timecode (required)
    6. timeline_placement (required)
    7. comment (optional)
    8. language (optional)
    9. audio_title (optional)
    10. reality_designation (optional)
    
    Returns a list of dicts with keys:
      - movie_show
      - season_episode (optional)
      - episode_title (optional)
      - start_timecode
      - end_timecode
      - comment (optional)
      - timeline_placement
      - language (optional)
      - audio_title (optional)
      - reality_designation (optional)
    """
    scenes = []
    
    try:
        # Read CSV with headers, handling quoted fields properly
        df = pd.read_csv(csv_path, dtype=str, keep_default_na=False, quoting=csv.QUOTE_MINIMAL)
        
        # Validate required columns exist
        required_columns = ['movie_show', 'start_timecode', 'end_timecode', 'timeline_placement']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            raise ValueError(f"Missing required columns: {missing_columns}")
        
        # Process each row
        for idx, row in df.iterrows():
            # Skip empty rows
            if not row['movie_show'].strip():
                continue
                
            # Validate required fields
            if not row['start_timecode'].strip() or not row['end_timecode'].strip() or not row['timeline_placement'].strip():
                print(f"Warning: Skipping row {idx + 1} - missing required fields")
                continue
            
            # Build scene dict
            scene = {
                'movie_show': row['movie_show'].strip(),
                'start_timecode': row['start_timecode'].strip(),
                'end_timecode': row['end_timecode'].strip(),
                'timeline_placement': row['timeline_placement'].strip(),
            }
            
            # Add optional fields if they exist and have values
            optional_fields = ['season_episode', 'episode_title', 'comment', 'language', 'audio_title', 'reality_designation']
            for field in optional_fields:
                if field in df.columns and row[field].strip():
                    scene[field] = row[field].strip()
            
            scenes.append(scene)
            
    except Exception as e:
        raise ValueError(f"Error parsing CSV file '{csv_path}': {str(e)}")
    
    return scenes

def create_sample_csv(output_path: str):
    """
    Create a sample CSV file with the new structure.
    """
    sample_data = [
        {
            'movie_show': 'Black Panther',
            'season_episode': '',
            'episode_title': '',
            'start_timecode': '0:00:14',
            'end_timecode': '0:01:45',
            'timeline_placement': '2,500,000 BCE',
            'comment': 'Prologue: N\'Jobu narrating the story of the first Black Panther and the formation of Wakanda to his son N\'Jadaka (Erik).',
            'language': 'en',
            'audio_title': 'Original Audio',
            'reality_designation': 'EARTH-199999'
        },
        {
            'movie_show': 'Agents of S.H.I.E.L.D.',
            'season_episode': '3.19',
            'episode_title': 'Failed Experiments',
            'start_timecode': '0:00:45',
            'end_timecode': '0:01:35',
            'timeline_placement': '3500 BCE',
            'comment': 'NOTE: During this flashback sequence Hive is telling the story of his Inhuman transformation (Terrigenesis) in the present.',
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
            'comment': 'Prologue: Odin narrating the story of The Convergence',
            'language': 'en',
            'audio_title': 'Original Audio',
            'reality_designation': 'EARTH-199999'
        }
    ]
    
    # Define column order
    columns = ['movie_show', 'season_episode', 'episode_title', 'start_timecode', 'end_timecode', 
               'timeline_placement', 'comment', 'language', 'audio_title', 'reality_designation']
    
    with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=columns)
        writer.writeheader()
        writer.writerows(sample_data)
    
    print(f"Sample CSV created: {output_path}")

if __name__ == '__main__':
    # Create a sample CSV for testing
    create_sample_csv('sample_new_structure.csv') 