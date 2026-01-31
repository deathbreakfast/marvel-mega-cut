import os
import subprocess
import json
from typing import Dict, List, Optional, Tuple
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

class MKVAnalyzer:
    """
    Analyzes MKV files to extract audio language information.
    Uses ffprobe to get detailed audio track information.
    """
    
    def __init__(self):
        self.console = Console()
    
    def get_audio_languages(self, mkv_path: str) -> List[Dict[str, str]]:
        """
        Extract audio language information from an MKV file using ffprobe.
        
        Returns a list of dictionaries with keys:
        - index: Audio track index
        - language: Language code (e.g., 'eng', 'spa')
        - title: Audio track title (if available)
        - codec: Audio codec name
        - channels: Number of audio channels
        """
        if not os.path.exists(mkv_path):
            return []
        
        try:
            # Use ffprobe to get detailed audio stream information
            cmd = [
                'ffprobe',
                '-v', 'quiet',
                '-print_format', 'json',
                '-show_streams',
                '-select_streams', 'a',  # Only audio streams
                mkv_path
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            data = json.loads(result.stdout)
            
            audio_tracks = []
            for stream in data.get('streams', []):
                track_info = {
                    'index': str(stream.get('index', '')),
                    'language': stream.get('tags', {}).get('language', 'unknown'),
                    'title': stream.get('tags', {}).get('title', ''),
                    'codec': stream.get('codec_name', ''),
                    'channels': str(stream.get('channels', '')),
                }
                audio_tracks.append(track_info)
            
            return audio_tracks
            
        except FileNotFoundError:
            self.console.print(f"[red]Error: ffprobe not found. Please install FFmpeg and ensure ffprobe is in your PATH.[/red]")
            self.console.print(f"[yellow]To install FFmpeg:[/yellow]")
            self.console.print(f"[yellow]  • Windows: Download from https://ffmpeg.org/download.html[/yellow]")
            self.console.print(f"[yellow]  • Or use: winget install ffmpeg[/yellow]")
            self.console.print(f"[yellow]  • Or use: choco install ffmpeg[/yellow]")
            self.console.print(f"[yellow]After installation, restart your terminal and try again.[/yellow]")
            return []
        except subprocess.CalledProcessError as e:
            self.console.print(f"[red]Error running ffprobe on {mkv_path}: {e}[/red]")
            if e.stderr:
                self.console.print(f"[red]ffprobe stderr: {e.stderr}[/red]")
            return []
        except json.JSONDecodeError as e:
            self.console.print(f"[red]Error parsing ffprobe output for {mkv_path}: {e}[/red]")
            return []
        except Exception as e:
            self.console.print(f"[red]Unexpected error analyzing {mkv_path}: {e}[/red]")
            return []
    
    def format_language_display(self, language_code: str) -> str:
        """Convert language code to human-readable format."""
        language_map = {
            'eng': 'English',
            'spa': 'Spanish',
            'fra': 'French',
            'deu': 'German',
            'ita': 'Italian',
            'por': 'Portuguese',
            'rus': 'Russian',
            'jpn': 'Japanese',
            'kor': 'Korean',
            'chi': 'Chinese',
            'ara': 'Arabic',
            'hin': 'Hindi',
            'unknown': 'Unknown'
        }
        return language_map.get(language_code.lower(), language_code.upper())
    
    def analyze_movie_folder(self, movie_folder: str, movie_names: List[str]) -> Dict[str, List[Dict[str, str]]]:
        """
        Analyze all movies in the folder and return language information.
        
        Args:
            movie_folder: Path to folder containing MKV files
            movie_names: List of movie names to look for
            
        Returns:
            Dictionary mapping movie names to their audio track information
        """
        results = {}
        
        # Check if the movie folder exists
        if not os.path.exists(movie_folder):
            self.console.print(f"[red]Error: Movie folder does not exist: {movie_folder}[/red]")
            return results
        
        for movie_name in movie_names:
            # Try different possible filename patterns
            possible_paths = [
                os.path.join(movie_folder, f"{movie_name}.mkv"),
                os.path.join(movie_folder, f"{movie_name}.MKV"),
                # Common variations
                os.path.join(movie_folder, f"{movie_name.replace(':', '')}.mkv"),
                os.path.join(movie_folder, f"{movie_name.replace(':', '')}.MKV"),
                os.path.join(movie_folder, f"{movie_name.replace(':', ' -')}.mkv"),
                os.path.join(movie_folder, f"{movie_name.replace(':', ' -')}.MKV"),
                os.path.join(movie_folder, f"{movie_name.replace('&', 'and')}.mkv"),
                os.path.join(movie_folder, f"{movie_name.replace('&', 'and')}.MKV"),
            ]
            
            mkv_path = None
            for path in possible_paths:
                if os.path.exists(path):
                    mkv_path = path
                    break
            
            if mkv_path:
                audio_tracks = self.get_audio_languages(mkv_path)
                results[movie_name] = audio_tracks
            else:
                results[movie_name] = []
        
        return results
    
    def display_language_summary(self, movie_languages: Dict[str, List[Dict[str, str]]]):
        """
        Display a formatted summary of all movie languages.
        """
        # Create summary table
        summary_table = Table(title="🎬 Movie Audio Language Analysis", box=None)
        summary_table.add_column("Movie", style="cyan", width=30)
        summary_table.add_column("Audio Tracks", style="green")
        summary_table.add_column("Languages", style="yellow")
        summary_table.add_column("File Status", style="magenta")
        
        for movie_name, audio_tracks in movie_languages.items():
            if audio_tracks:
                # Format audio tracks info
                track_info = []
                languages = set()
                
                for track in audio_tracks:
                    lang_display = self.format_language_display(track['language'])
                    languages.add(lang_display)
                    
                    track_desc = f"Track {track['index']}: {lang_display}"
                    if track['title']:
                        track_desc += f" ({track['title']})"
                    if track['channels']:
                        track_desc += f" [{track['channels']}ch]"
                    
                    track_info.append(track_desc)
                
                track_text = "\n".join(track_info)
                languages_text = ", ".join(sorted(languages))
                status = "✅ Found"
                
            else:
                track_text = "No audio tracks found"
                languages_text = "N/A"
                status = "❌ Not found"
            
            summary_table.add_row(movie_name, track_text, languages_text, status)
        
        self.console.print(summary_table)
        
        # Show recommendations
        self.console.print()
        self.console.print(Panel(
            "[bold cyan]💡 Recommendations:[/bold cyan]\n"
            "• Use the language codes (e.g., 'eng', 'spa') in your CSV file\n"
            "• Set the 'language' column to the desired audio track language\n"
            "• Set the 'audio_title' column to match the track title if available\n"
            "• For movies with multiple audio tracks, specify the exact language code",
            border_style="blue"
        )) 