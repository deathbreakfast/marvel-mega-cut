#!/usr/bin/env python3
"""
Test script to demonstrate the analyze_languages functionality.
This script shows how the new command works with sample data.
"""

import os
import tempfile
import json
from unittest.mock import patch, MagicMock
from mkv_analyzer import MKVAnalyzer
from rich.console import Console

def test_analyze_languages_demo():
    """Demonstrate the analyze_languages functionality with mock data."""
    console = Console()
    
    console.print("[bold cyan]🎬 Testing analyze_languages command[/bold cyan]")
    console.print()
    
    # Mock sample CSV data
    sample_scenes = [
        {'movie_show': 'Black Panther'},
        {'movie_show': 'Thor: The Dark World'},
        {'movie_show': 'Agents of S.H.I.E.L.D.'},
        {'movie_show': 'Black Panther'},  # Duplicate to test deduplication
    ]
    
    # Mock MKV analysis results
    mock_movie_languages = {
        'Black Panther': [
            {'index': '1', 'language': 'eng', 'title': 'English', 'codec': 'aac', 'channels': '2'},
            {'index': '2', 'language': 'spa', 'title': 'Spanish', 'codec': 'aac', 'channels': '2'},
            {'index': '3', 'language': 'fra', 'title': 'French', 'codec': 'aac', 'channels': '2'}
        ],
        'Thor: The Dark World': [
            {'index': '1', 'language': 'eng', 'title': 'English', 'codec': 'aac', 'channels': '2'},
            {'index': '2', 'language': 'spa', 'title': 'Spanish', 'codec': 'aac', 'channels': '2'}
        ],
        'Agents of S.H.I.E.L.D.': [
            {'index': '1', 'language': 'eng', 'title': 'English', 'codec': 'aac', 'channels': '2'}
        ]
    }
    
    console.print("[green]✅ Successfully extracted movie names from CSV:[/green]")
    movie_names = list(set(scene['movie_show'] for scene in sample_scenes))
    movie_names.sort()
    for movie in movie_names:
        console.print(f"  • {movie}")
    console.print()
    
    # Display the analysis results
    analyzer = MKVAnalyzer()
    analyzer.display_language_summary(mock_movie_languages)
    
    # Show summary statistics
    found_movies = sum(1 for tracks in mock_movie_languages.values() if tracks)
    missing_movies = len(movie_names) - found_movies
    
    from rich.panel import Panel
    console.print()
    console.print(Panel(
        f"[bold]📊 Demo Summary:[/bold]\n"
        f"• Total movies in CSV: {len(movie_names)}\n"
        f"• MKV files found: {found_movies}\n"
        f"• Missing MKV files: {missing_movies}\n"
        f"• Total audio tracks found: {sum(len(tracks) for tracks in mock_movie_languages.values())}",
        border_style="green"
    ))
    
    console.print()
    console.print("[bold yellow]💡 How to use the real command:[/bold yellow]")
    console.print("python main.py analyze-languages --csv your_scenes.csv --movies /path/to/mkv/files")
    console.print()
    console.print("[bold cyan]Example:[/bold cyan]")
    console.print("python main.py analyze-languages --csv sample_new_structure.csv --movies /movies/")
    console.print()
    console.print("[dim]Note: This demo uses mock data. The real command requires actual MKV files with audio streams.[/dim]")

if __name__ == '__main__':
    test_analyze_languages_demo() 