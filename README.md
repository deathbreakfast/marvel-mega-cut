# Marvel Mega Cut: Infinity Saga Edition

## Overview
This project automates the creation of a Marvel Infinity Saga "Mega Cut" by stitching together scenes from all movies and shows in the saga, based on a user-provided CSV file. The output is a series of video files, each as close to two hours as possible, with transitions and in-universe timeline placement overlays.

## Features
- Parse a documented CSV file with multi-row headers and section rows (see `sample_scenes.csv`)
- Automatically extract only complete scene rows with required fields
- Edit and concatenate video clips
- Add simple transitions between scenes
- Overlay in-universe timeline placement (e.g., "2,500,000 BCE", "2006")
- Output in ~2 hour chunks
- Configurable via CLI, environment variables, or .env file
- Dockerized for easy cloud deployment

## Requirements
- Python 3.8+
- Docker (for containerized usage)

## Installation
1. Clone the repository:
   ```bash
   git clone <repo-url>
   cd marvel-mega-cut
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Performance Optimization

### Threading Support
This project now supports multi-threaded processing to significantly improve performance:

- **Default**: Threaded processing with 4 worker threads
- **Control**: Use `--no-threading` to disable threading
- **Customization**: Use `--max-workers` to adjust thread count

#### Performance Benefits
- **Scene Processing**: Multiple scenes are processed concurrently within each chunk
- **I/O Optimization**: Parallel video file loading and processing
- **CPU Utilization**: Better use of multi-core systems
- **Memory Management**: Efficient resource handling with proper cleanup

#### Usage Examples
```bash
# Use default threading (4 workers)
python main.py process --csv scenes.csv --output output --movies movies

# Use custom thread count
python main.py process --csv scenes.csv --output output --movies movies --max-workers 8

# Disable threading (sequential processing)
python main.py process --csv scenes.csv --output output --movies movies --no-threading

# Combine with other options
python main.py process --csv scenes.csv --output output --movies movies --chunks "1-3" --max-workers 6 --verbose
```

#### Thread Count Recommendations
- **4-6 workers**: Good for most systems
- **8+ workers**: For high-end systems with many cores
- **2-3 workers**: For systems with limited resources
- **1 worker**: Use `--no-threading` for single-threaded processing

### Cancellation Support
The application now properly handles `Ctrl+C` (SIGINT) signals to gracefully stop processing:

- **Threaded Processing**: All worker threads are properly cancelled and cleaned up
- **Resource Cleanup**: Video cache and temporary files are properly cleaned up
- **Graceful Shutdown**: Processing stops at chunk boundaries to avoid partial outputs
- **Progress Preservation**: Completed work is preserved when cancellation occurs

#### Usage
```bash
# Start processing
python main.py process --csv scenes.csv --output output --movies movies

# Press Ctrl+C to stop processing gracefully
# The application will:
# - Stop all worker threads
# - Clean up resources
# - Preserve completed chunks
# - Exit cleanly
```

## File Format Requirements
- **Input movie/show files**: Must be in MKV format (`.mkv`)
- **File naming**: Files should be named exactly as they appear in the CSV's "Movie/Show" column, with `.mkv` extension
- **Output**: Generated mega cut files will be in MP4 format for wider compatibility

## CSV Template & Format
This project uses a documented CSV template (`sample_scenes.csv`) that includes:
- Multi-row headers for documentation and navigation
- Section rows that break up scenes by century, decade, or year
- Scene rows, which are the only rows extracted for editing

### Required Columns for Extraction
Only rows with the following fields are extracted:
- Movie/Show
- Season & Episode (Optional)
- Episode Title (Optional)
- Start timecode
- End timecode
- Comment (Optional)
- Timeline placement

All other rows (headers, section breaks, notes) are ignored by the parser.

## Usage
### CLI Commands

#### Process Scenes
```bash
# Using all CLI arguments
python main.py process --csv path/to/scenes.csv --output path/to/output_folder --movies path/to/movie_folder

# Using mix of CLI and environment variables
python main.py process --csv path/to/scenes.csv --output path/to/output_folder
```

#### Set Audio Track for Movie
```bash
# Set audio track for all scenes of a specific movie
python main.py set-audio-track path/to/scenes.csv "Movie Name" "audio_track_title"

# Examples:
python main.py set-audio-track scenes.csv "Black Panther" "English (Vegamovies.NL) [8ch]"
python main.py set-audio-track scenes.csv "Thor: The Dark World" "Spanish (Dual Audio) [5.1]"
python main.py set-audio-track scenes.csv "Iron Man" "French (DTS-HD) [7.1]"
```

#### Migrate CSV Format
```bash
# Migrate from old CSV format to new format
python main.py migrate old_scenes.csv new_scenes.csv --language en --audio-title "Original Audio"
```

#### Analyze Audio Languages
```bash
# Analyze MKV files to identify available audio languages
python main.py analyze-languages --csv scenes.csv --movies /path/to/movies
```

#### Create Sample CSV
```bash
# Create a sample CSV file with the new structure
python main.py create-sample sample_new_structure.csv
```

### CLI Options for Process Command
- `--csv`: Path to the scenes CSV file
- `--output`: Output folder for mega cut videos  
- `--movies`: Path to the folder containing all movie/show files
- `--chunks`: Specific chunks to process (e.g., "1,2,4-8")
- `--verbose`: Enable verbose logging for debugging
- `--no-threading`: Disable threading (use sequential processing)
- `--max-workers`: Maximum number of worker threads (default: 4)

### Environment Variables
- `MEGA_CUT_MOVIE_FOLDER`: Path to the folder containing all movie/show files (optional if provided via CLI)
- `MEGA_CUT_CSV`: Path to the CSV file (optional if provided via CLI)
- `MEGA_CUT_OUTPUT`: Output folder (optional if provided via CLI)

You can also use a `.env` file in the project root:
```
MEGA_CUT_MOVIE_FOLDER=/path/to/movies
MEGA_CUT_CSV=/path/to/scenes.csv
MEGA_CUT_OUTPUT=/path/to/output
```

## Troubleshooting

### Progress UI Stuck on Spinner
If the progress UI appears to be stuck on a spinner, the processing may actually be complete. This can happen due to display timing issues. To verify:

1. Check the log file (`mega_cut.log`) for completion messages
2. Look for output files in your output directory
3. Use the `--verbose` flag for additional debugging information:
   ```bash
   python main.py process --csv scenes.csv --output output --movies movies --verbose
   ```

**Note**: The progress display has been improved to show:
- Professional progress bars using `tqdm` library
- Real-time elapsed time and ETA calculations
- Current scene information with processing rate
- Threaded UI updates that continue during CPU-intensive video processing
- Automatic progress bar formatting and colors
- Cross-platform compatibility and reliability

### Missing Video Files
If you see warnings about missing video files, ensure:
- All movie/show files are in MKV format
- File names match exactly with the CSV "Movie/Show" column
- Files are in the specified movie folder

### Audio Track Issues
If you encounter audio track problems:
1. Use the analyze-languages command to see available tracks:
   ```bash
   python main.py analyze-languages --csv scenes.csv --movies /path/to/movies
   ```
2. Set the correct audio track for problematic movies:
   ```bash
   python main.py set-audio-track scenes.csv "Movie Name" "Audio Track Title"
   ```

## Docker Usage
Build the Docker image:
```bash
docker build -t marvel-mega-cut .
```

Run the container:
```bash
docker run --rm -v /path/to/movies:/movies -v /path/to/output:/output \
  -e MEGA_CUT_MOVIE_FOLDER=/movies \
  -e MEGA_CUT_CSV=/movies/sample_scenes.csv \
  -e MEGA_CUT_OUTPUT=/output \
  marvel-mega-cut
```

## Output
- The output folder will contain video files named `mega_cut_part_1.mp4`, `mega_cut_part_2.mp4`, etc., each as close to two hours as possible.

## Testing

To run the unit tests, you need `pytest` installed. If you don't have it, install with:
```bash
pip install pytest
```

Some tests use OCR to verify video content. You must also install the Tesseract binary:
- **Ubuntu/Debian:**
  ```bash
  sudo apt-get install tesseract-ocr
  ```
- **macOS (with Homebrew):**
  ```bash
  brew install tesseract
  ```
- **Windows:**
  Download and install from [https://github.com/tesseract-ocr/tesseract](https://github.com/tesseract-ocr/tesseract)

Then run:
```bash
pytest
```
This will automatically discover and run all tests in files named `test_*.py`.

## Contributing
Pull requests are welcome! Please open an issue first to discuss major changes.

## License
MIT 