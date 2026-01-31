import os
import click
import pandas as pd
from dotenv import load_dotenv
from csv_parser import extract_scenes as extract_old_scenes
from new_csv_parser import extract_scenes as extract_new_scenes
from video_editor import process_scenes, process_scenes_with_options, parse_chunk_selection
from csv_migrator import migrate_csv, validate_migration
from mkv_analyzer import MKVAnalyzer

# Load .env if present
load_dotenv()

def detect_csv_format(csv_path: str) -> str:
    """
    Detect whether CSV is in old or new format.
    Returns 'old' or 'new'.
    """
    try:
        df = pd.read_csv(csv_path, dtype=str, keep_default_na=False)
        
        # Check if new format columns exist
        new_format_columns = ['movie_show', 'start_timecode', 'end_timecode', 'timeline_placement']
        if all(col in df.columns for col in new_format_columns):
            return 'new'
        else:
            return 'old'
    except Exception:
        # If we can't read with headers, assume old format
        return 'old'

def extract_scenes(csv_path: str):
    """
    Extract scenes using the appropriate parser based on CSV format.
    """
    format_type = detect_csv_format(csv_path)
    
    if format_type == 'new':
        print(f"[cyan]Detected new CSV format[/cyan]")
        return extract_new_scenes(csv_path)
    else:
        print(f"[cyan]Detected old CSV format[/cyan]")
        return extract_old_scenes(csv_path)

def set_movie_audio_track(csv_path: str, movie_name: str, audio_track: str) -> bool:
    """
    Set the audio_title field for all scenes of a specific movie in the CSV file.
    
    Args:
        csv_path: Path to the CSV file
        movie_name: Name of the movie to update
        audio_track: Audio track title to set (e.g., "English (Vegamovies.NL) [8ch]")
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Read the CSV file
        df = pd.read_csv(csv_path, dtype=str, keep_default_na=False)
        
        # Check if this is the new format (has audio_title column)
        if 'audio_title' not in df.columns:
            print(f"[red]Error: CSV file does not have an 'audio_title' column. This feature requires the new CSV format.[/red]")
            return False
        
        # Find rows where movie_show matches the target movie
        movie_mask = df['movie_show'].str.strip().str.lower() == movie_name.lower()
        matching_rows = df[movie_mask]
        
        if len(matching_rows) == 0:
            print(f"[yellow]Warning: No scenes found for movie '{movie_name}'[/yellow]")
            return False
        
        # Update the audio_title field for matching rows
        df.loc[movie_mask, 'audio_title'] = audio_track
        
        # Save the updated CSV
        df.to_csv(csv_path, index=False)
        
        print(f"[green]Successfully updated audio track to '{audio_track}' for {len(matching_rows)} scenes of '{movie_name}'[/green]")
        return True
        
    except Exception as e:
        print(f"[red]Error updating audio track: {e}[/red]")
        return False

@click.group()
def cli():
    """Marvel Mega Cut Processor - Process movie/show scenes into chronological mega cuts."""
    pass

@cli.command()
@click.option('--csv', 'csv_path', default=None, help='Path to the scenes CSV file')
@click.option('--output', 'output_folder', default=None, help='Output folder for mega cut videos')
@click.option('--movies', 'movie_folder', default=None, help='Path to the folder containing movie/show files')
@click.option('--chunks', 'chunks_str', default=None, help='Specific chunks to process (e.g., "1,2,4-8")')
@click.option('--verbose', is_flag=True, help='Enable verbose logging for debugging')
@click.option('--no-threading', is_flag=True, help='Disable threading (use sequential processing)')
@click.option('--max-workers', default=4, help='Maximum number of worker threads (default: 4)')
def process(csv_path, output_folder, movie_folder, chunks_str, verbose, no_threading, max_workers):
    """Process scenes into chronological mega cuts."""
    # Create a Rich console for all output
    from rich.console import Console
    console = Console()
    
    # Get env vars if CLI not provided
    csv_path = csv_path or os.getenv('MEGA_CUT_CSV')
    output_folder = output_folder or os.getenv('MEGA_CUT_OUTPUT')
    movie_folder = movie_folder or os.getenv('MEGA_CUT_MOVIE_FOLDER')

    if not csv_path or not movie_folder or not output_folder:
        console.print("[red]Error: CSV path, movie folder, and output folder must be specified via CLI or environment variables.[/red]")
        exit(1)

    # Parse chunk selection if provided
    chunk_selection = None
    if chunks_str:
        try:
            chunk_selection = parse_chunk_selection(chunks_str)
            console.print(f"[yellow]Chunk selection: {chunk_selection}[/yellow]")
        except ValueError as e:
            console.print(f"[red]Error parsing chunk selection '{chunks_str}': {e}[/red]")
            exit(1)
    
    console.print(f"[cyan]Loading scenes from:[/cyan] {csv_path}")
    console.print(f"[cyan]Movie folder:[/cyan] {movie_folder}")
    console.print(f"[cyan]Output folder:[/cyan] {output_folder}")

    # Extract valid scenes
    scenes = extract_scenes(csv_path)
    console.print(f"[green]Extracted {len(scenes)} valid scenes.[/green]")
    console.print("[cyan]First 3 scenes:[/cyan]")
    for i, scene in enumerate(scenes[:3], 1):
        console.print(f"  {i}. [yellow]{scene['movie_show']}[/yellow] ({scene['start_timecode']} - {scene['end_timecode']})")
    console.print()  # Add spacing before progress starts

    # Show threading configuration
    use_threading = not no_threading
    if use_threading:
        console.print(f"[cyan]Using threaded processing with {max_workers} workers[/cyan]")
    else:
        console.print("[cyan]Using sequential processing[/cyan]")

    # Call the video editing logic with threading options
    process_scenes_with_options(scenes, movie_folder, output_folder, 
                              chunk_selection=chunk_selection, verbose=verbose,
                              use_threading=use_threading, max_workers=max_workers)

@cli.command()
@click.argument('old_csv_path', type=click.Path(exists=True))
@click.argument('new_csv_path', type=click.Path())
@click.option('--language', default='en', help='Default language code for all scenes')
@click.option('--audio-title', default='Original Audio', help='Default audio title for all scenes')
def migrate(old_csv_path, new_csv_path, language, audio_title):
    """Migrate from old CSV format to new simplified format with language and audio support."""
    from rich.console import Console
    console = Console()
    
    console.print(f"[cyan]Migrating CSV from old format to new format...[/cyan]")
    console.print(f"[cyan]Old CSV:[/cyan] {old_csv_path}")
    console.print(f"[cyan]New CSV:[/cyan] {new_csv_path}")
    console.print(f"[cyan]Default Language:[/cyan] {language}")
    console.print(f"[cyan]Default Audio Title:[/cyan] {audio_title}")
    console.print()
    
    # Perform migration
    success = migrate_csv(old_csv_path, new_csv_path, language, audio_title)
    
    if success:
        # Validate migration
        validate_migration(old_csv_path, new_csv_path)
        console.print("\n[green]🎉 Migration completed successfully![/green]")
        console.print(f"[cyan]New CSV saved to:[/cyan] {new_csv_path}")
    else:
        console.print("\n[red]❌ Migration failed![/red]")
        exit(1)

@cli.command()
@click.argument('output_path', type=click.Path())
def create_sample(output_path):
    """Create a sample CSV file with the new structure."""
    from new_csv_parser import create_sample_csv
    from rich.console import Console
    console = Console()
    
    console.print(f"[cyan]Creating sample CSV with new structure...[/cyan]")
    create_sample_csv(output_path)
    console.print(f"[green]✅ Sample CSV created:[/green] {output_path}")

@cli.command()
@click.option('--csv', 'csv_path', default=None, help='Path to the scenes CSV file')
@click.option('--movies', 'movie_folder', default=None, help='Path to the folder containing movie/show files')
def analyze_languages(csv_path, movie_folder):
    """Analyze MKV files to identify available audio languages for movies in the CSV."""
    from rich.console import Console
    console = Console()
    
    # Get env vars if CLI not provided
    csv_path = csv_path or os.getenv('MEGA_CUT_CSV')
    movie_folder = movie_folder or os.getenv('MEGA_CUT_MOVIE_FOLDER')

    if not csv_path or not movie_folder:
        console.print("[red]Error: CSV path and movie folder must be specified via CLI or environment variables.[/red]")
        exit(1)

    console.print(f"[cyan]Analyzing audio languages for movies in CSV...[/cyan]")
    console.print(f"[cyan]CSV file:[/cyan] {csv_path}")
    console.print(f"[cyan]Movie folder:[/cyan] {movie_folder}")
    console.print()

    # Extract unique movie names from CSV
    try:
        scenes = extract_scenes(csv_path)
        movie_names = list(set(scene['movie_show'] for scene in scenes))
        movie_names.sort()  # Sort alphabetically
        
        console.print(f"[green]Found {len(movie_names)} unique movies in CSV:[/green]")
        for movie in movie_names:
            console.print(f"  • {movie}")
        console.print()
        
    except Exception as e:
        console.print(f"[red]Error reading CSV file: {e}[/red]")
        exit(1)

    # Analyze MKV files
    analyzer = MKVAnalyzer()
    movie_languages = analyzer.analyze_movie_folder(movie_folder, movie_names)
    
    # Display results
    analyzer.display_language_summary(movie_languages)
    
    # Summary statistics
    found_movies = sum(1 for tracks in movie_languages.values() if tracks)
    missing_movies = len(movie_names) - found_movies
    
    console.print()
    from rich.panel import Panel
    console.print(Panel(
        f"[bold]📊 Summary:[/bold]\n"
        f"• Total movies in CSV: {len(movie_names)}\n"
        f"• MKV files found: {found_movies}\n"
        f"• Missing MKV files: {missing_movies}",
        border_style="green" if missing_movies == 0 else "yellow"
    ))

@cli.command()
@click.argument('csv_path', type=click.Path(exists=True))
@click.argument('movie_name')
@click.argument('audio_track')
def set_audio_track(csv_path, movie_name, audio_track):
    """Set the audio_title field for all scenes of a specific movie in the CSV file.
    
    CSV_PATH: Path to the CSV file to update
    MOVIE_NAME: Name of the movie to update (case-insensitive)
    AUDIO_TRACK: Audio track title to set (e.g., "English (Vegamovies.NL) [8ch]")
    """
    from rich.console import Console
    console = Console()
    
    console.print(f"[cyan]Setting audio track for movie scenes...[/cyan]")
    console.print(f"[cyan]CSV file:[/cyan] {csv_path}")
    console.print(f"[cyan]Movie:[/cyan] {movie_name}")
    console.print(f"[cyan]Audio Track:[/cyan] {audio_track}")
    console.print()
    
    success = set_movie_audio_track(csv_path, movie_name, audio_track)
    
    if success:
        console.print("[green]✅ Audio track update completed successfully![/green]")
    else:
        console.print("[red]❌ Audio track update failed![/red]")
        exit(1)

if __name__ == '__main__':
    cli() 