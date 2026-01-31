# Analyze Languages Feature

## Overview

The `analyze-languages` command has been added to the Marvel Mega Cut Processor to help identify available audio languages in MKV files for movies referenced in the CSV file. This feature helps users properly configure the language and audio track settings in their CSV files.

## New Command

```bash
python main.py analyze-languages --csv <csv_path> --movies <movie_folder>
```

### Options

- `--csv`: Path to the scenes CSV file (can also use `MEGA_CUT_CSV` environment variable)
- `--movies`: Path to the folder containing MKV files (can also use `MEGA_CUT_MOVIE_FOLDER` environment variable)

## Features

### 1. CSV Parsing
- Automatically detects CSV format (old vs new)
- Extracts unique movie names from the `movie_show` column
- Handles both old and new CSV formats seamlessly

### 2. MKV Analysis
- Uses `ffprobe` to analyze MKV files for audio streams
- Extracts detailed audio track information:
  - Language codes (e.g., 'eng', 'spa', 'fra')
  - Audio track titles
  - Codec information
  - Channel count
- Supports multiple filename patterns (.mkv, .MKV)

### 3. Rich Display
- Beautiful formatted table showing all movies and their audio tracks
- Color-coded status indicators (✅ Found, ❌ Not found)
- Human-readable language names (English, Spanish, French, etc.)
- Summary statistics

### 4. Recommendations
- Provides helpful guidance on how to use the language information
- Explains how to set the `language` and `audio_title` columns in CSV
- Suggests best practices for handling multiple audio tracks

## Example Output

```
Analyzing audio languages for movies in CSV...
CSV file: sample_new_structure.csv
Movie folder: /path/to/movies

Found 3 unique movies in CSV:
  • Agents of S.H.I.E.L.D.
  • Black Panther
  • Thor: The Dark World

                                    🎬 Movie Audio Language Analysis                                        
 Movie                           Audio Tracks                      Languages                 File Status    
 Black Panther                   Track 1: English (English) [2ch]  English, French, Spanish  ✅ Found       
                                 Track 2: Spanish (Spanish) [2ch]
                                 Track 3: French (French) [2ch]
 Thor: The Dark World            Track 1: English (English) [2ch]  English, Spanish          ✅ Found       
                                 Track 2: Spanish (Spanish) [2ch]
 Agents of S.H.I.E.L.D.          Track 1: English (English) [2ch]  English                   ✅ Found       

╭──────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ 💡 Recommendations:                                                                                      │
│ • Use the language codes (e.g., 'eng', 'spa') in your CSV file                                           │
│ • Set the 'language' column to the desired audio track language                                          │
│ • Set the 'audio_title' column to match the track title if available                                     │
│ • For movies with multiple audio tracks, specify the exact language code                                 │
╰──────────────────────────────────────────────────────────────────────────────────────────────────────────╯

╭──────────────────────────────────────────────────────────────────────────────────────────────────────────╮
│ 📊 Summary:                                                                                              │
│ • Total movies in CSV: 3                                                                                 │
│ • MKV files found: 3                                                                                     │
│ • Missing MKV files: 0                                                                                   │
╰──────────────────────────────────────────────────────────────────────────────────────────────────────────╯
```

## Implementation Details

### New Files Created

1. **`mkv_analyzer.py`** - Core MKV analysis functionality
   - `MKVAnalyzer` class for analyzing MKV files
   - Language code to human-readable name mapping
   - Rich display formatting

2. **`test_mkv_analyzer.py`** - Comprehensive test suite
   - Unit tests for all MKV analyzer functionality
   - Mock testing for ffprobe integration
   - Error handling tests

3. **`test_analyze_languages.py`** - Demo script
   - Shows how the feature works with sample data
   - Demonstrates the output format

### Modified Files

1. **`main.py`** - Added new CLI command
   - `analyze-languages` command implementation
   - Integration with existing CSV parsing
   - Rich console output

## Usage Workflow

1. **Run the analysis:**
   ```bash
   python main.py analyze-languages --csv your_scenes.csv --movies /path/to/mkv/files
   ```

2. **Review the output:**
   - Check which movies have MKV files
   - Note the available audio languages for each movie
   - See the language codes (eng, spa, fra, etc.)

3. **Update your CSV:**
   - Set the `language` column to the desired language code
   - Set the `audio_title` column to match the track title if needed
   - For movies with multiple audio tracks, specify the exact language code

4. **Process your scenes:**
   ```bash
   python main.py process --csv your_scenes.csv --movies /path/to/mkv/files --output /output/folder
   ```

## Requirements

- `ffprobe` must be installed and available in PATH
- MKV files must have proper audio stream metadata
- CSV files must have a `movie_show` column

## Error Handling

- Gracefully handles missing MKV files
- Shows clear error messages for ffprobe failures
- Continues processing even if some files can't be analyzed
- Provides helpful debugging information

## Benefits

1. **Easy Language Discovery:** Quickly see what audio languages are available
2. **Proper CSV Configuration:** Ensure language settings are correct before processing
3. **Quality Assurance:** Verify that all required MKV files are present
4. **User-Friendly:** Beautiful, informative output with clear recommendations
5. **Integration:** Seamlessly works with existing CSV parsing and processing pipeline 