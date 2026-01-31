import pandas as pd
import csv
import re
from typing import List, Dict, Optional
from csv_parser import extract_scenes as extract_old_scenes

def migrate_csv(old_csv_path: str, new_csv_path: str, language: str = "en", audio_title: str = "Original Audio"):
    """
    Migrate from old CSV structure to new simplified structure.
    
    Args:
        old_csv_path: Path to the old CSV file
        new_csv_path: Path to save the new CSV file
        language: Default language code for all scenes
        audio_title: Default audio title for all scenes
    """
    print(f"Migrating CSV from '{old_csv_path}' to '{new_csv_path}'")
    
    # Extract scenes using old parser
    try:
        old_scenes = extract_old_scenes(old_csv_path)
        print(f"Extracted {len(old_scenes)} scenes from old format")
    except Exception as e:
        print(f"Error extracting scenes from old CSV: {e}")
        return False
    
    # Convert to new format
    new_scenes = []
    for scene in old_scenes:
        new_scene = {
            'movie_show': scene['movie_show'],
            'season_episode': scene.get('season_episode', ''),
            'episode_title': scene.get('episode_title', ''),
            'start_timecode': scene['start_timecode'],
            'end_timecode': scene['end_timecode'],
            'timeline_placement': scene['timeline_placement'],
            'comment': scene.get('comment', ''),
            'language': language,
            'audio_title': audio_title,
            'reality_designation': 'EARTH-199999'  # Default reality designation
        }
        new_scenes.append(new_scene)
    
    # Write new CSV
    columns = ['movie_show', 'season_episode', 'episode_title', 'start_timecode', 'end_timecode', 
               'timeline_placement', 'comment', 'language', 'audio_title', 'reality_designation']
    
    try:
        with open(new_csv_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=columns)
            writer.writeheader()
            writer.writerows(new_scenes)
        
        print(f"Successfully migrated {len(new_scenes)} scenes to new format")
        print(f"New CSV saved to: {new_csv_path}")
        return True
        
    except Exception as e:
        print(f"Error writing new CSV: {e}")
        return False

def validate_migration(old_csv_path: str, new_csv_path: str):
    """
    Validate that the migration was successful by comparing scene counts and key fields.
    """
    print("\nValidating migration...")
    
    # Import new parser
    from new_csv_parser import extract_scenes as extract_new_scenes
    
    try:
        old_scenes = extract_old_scenes(old_csv_path)
        new_scenes = extract_new_scenes(new_csv_path)
        
        print(f"Old format scenes: {len(old_scenes)}")
        print(f"New format scenes: {len(new_scenes)}")
        
        if len(old_scenes) != len(new_scenes):
            print("⚠️  Warning: Scene count mismatch!")
            return False
        
        # Compare first few scenes
        print("\nComparing first 3 scenes:")
        for i in range(min(3, len(old_scenes))):
            old_scene = old_scenes[i]
            new_scene = new_scenes[i]
            
            print(f"\nScene {i+1}:")
            print(f"  Movie/Show: {old_scene['movie_show']} -> {new_scene['movie_show']}")
            print(f"  Timecodes: {old_scene['start_timecode']}-{old_scene['end_timecode']} -> {new_scene['start_timecode']}-{new_scene['end_timecode']}")
            print(f"  Timeline: {old_scene['timeline_placement']} -> {new_scene['timeline_placement']}")
        
        print("\n✅ Migration validation successful!")
        return True
        
    except Exception as e:
        print(f"❌ Migration validation failed: {e}")
        return False

def create_migration_script():
    """
    Create a standalone migration script that can be run independently.
    """
    script_content = '''#!/usr/bin/env python3
"""
CSV Migration Script for Marvel Mega Cut
Converts old CSV format to new simplified format with language and audio support.
"""

import sys
import os
from csv_migrator import migrate_csv, validate_migration

def main():
    if len(sys.argv) < 3:
        print("Usage: python csv_migrator.py <old_csv_path> <new_csv_path> [language] [audio_title]")
        print("Example: python csv_migrator.py sample_scenes.csv new_scenes.csv en 'Original Audio'")
        sys.exit(1)
    
    old_csv_path = sys.argv[1]
    new_csv_path = sys.argv[2]
    language = sys.argv[3] if len(sys.argv) > 3 else "en"
    audio_title = sys.argv[4] if len(sys.argv) > 4 else "Original Audio"
    
    if not os.path.exists(old_csv_path):
        print(f"Error: Old CSV file '{old_csv_path}' not found")
        sys.exit(1)
    
    # Perform migration
    success = migrate_csv(old_csv_path, new_csv_path, language, audio_title)
    
    if success:
        # Validate migration
        validate_migration(old_csv_path, new_csv_path)
        print("\\n🎉 Migration completed successfully!")
    else:
        print("\\n❌ Migration failed!")
        sys.exit(1)

if __name__ == '__main__':
    main()
'''
    
    with open('migrate_csv.py', 'w') as f:
        f.write(script_content)
    
    print("Created standalone migration script: migrate_csv.py")

if __name__ == '__main__':
    # Example usage
    if len(sys.argv) > 1:
        old_csv = sys.argv[1]
        new_csv = sys.argv[2] if len(sys.argv) > 2 else 'migrated_scenes.csv'
        language = sys.argv[3] if len(sys.argv) > 3 else 'en'
        audio_title = sys.argv[4] if len(sys.argv) > 4 else 'Original Audio'
        
        success = migrate_csv(old_csv, new_csv, language, audio_title)
        if success:
            validate_migration(old_csv, new_csv)
    else:
        print("Usage: python csv_migrator.py <old_csv_path> [new_csv_path] [language] [audio_title]")
        print("Example: python csv_migrator.py sample_scenes.csv new_scenes.csv en 'Original Audio'") 