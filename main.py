import os
import click
import pandas as pd
from dotenv import load_dotenv
from csv_parser import extract_scenes
from video_editor import process_scenes

# Load .env if present
load_dotenv()

@click.command()
@click.option('--csv', 'csv_path', default=None, help='Path to the scenes CSV file')
@click.option('--output', 'output_folder', default=None, help='Output folder for mega cut videos')
@click.option('--movies', 'movie_folder', default=None, help='Path to the folder containing movie/show files')
def main(csv_path, output_folder, movie_folder):
    # Get env vars if CLI not provided
    csv_path = csv_path or os.getenv('MEGA_CUT_CSV')
    output_folder = output_folder or os.getenv('MEGA_CUT_OUTPUT')
    movie_folder = movie_folder or os.getenv('MEGA_CUT_MOVIE_FOLDER')

    if not csv_path or not movie_folder or not output_folder:
        print("Error: CSV path, movie folder, and output folder must be specified via CLI or environment variables.")
        exit(1)

    print(f"Loading scenes from: {csv_path}")
    print(f"Movie folder: {movie_folder}")
    print(f"Output folder: {output_folder}")

    # Extract valid scenes
    scenes = extract_scenes(csv_path)
    print(f"Extracted {len(scenes)} valid scenes.")
    print("First 3 scenes:")
    for scene in scenes[:3]:
        print(scene)

    # Call the video editing logic
    process_scenes(scenes, movie_folder, output_folder)

if __name__ == '__main__':
    main() 