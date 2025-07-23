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
### CLI
```bash
# Using all CLI arguments
python main.py --csv path/to/scenes.csv --output path/to/output_folder --movies path/to/movie_folder

# Using mix of CLI and environment variables
python main.py --csv path/to/scenes.csv --output path/to/output_folder
```

### CLI Options
- `--csv`: Path to the scenes CSV file
- `--output`: Output folder for mega cut videos  
- `--movies`: Path to the folder containing all movie/show files

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