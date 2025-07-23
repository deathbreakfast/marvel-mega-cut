import pandas as pd
from typing import List, Dict, Optional
import re

def extract_scenes(csv_path: str) -> List[Dict[str, Optional[str]]]:
    """
    Extracts only complete scene rows from the documented CSV file.

    Timeline placement extraction rules:
    - If the timeline placement cell contains a year (e.g., '2016', '3500 BCE', '2008'), use it as is.
    - If the timeline placement cell contains only a month (e.g., 'JUN'), find the most recent section header row above (row[1]) that is a 4-digit year, and use that year to construct the timeline placement (e.g., 'JUN 2016').
    - If the timeline placement cell is blank, propagate the last non-blank value (to handle merged cells in the CSV).
    - If the timeline placement cell is a month and no year section header is found above, leave as just the month.

    Returns a list of dicts with keys:
      - movie_show
      - season_episode (optional)
      - episode_title (optional)
      - start_timecode
      - end_timecode
      - comment (optional)
      - timeline_placement
    """
    scenes = []
    df = pd.read_csv(csv_path, header=None, dtype=str, keep_default_na=False)
    last_scene_timeline = ''
    last_scene_comment = ''
    year_pattern = re.compile(r'^\d{4}$')
    month_pattern = re.compile(r'^(JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|OCT|NOV|DEC)$', re.IGNORECASE)
    for idx, row in enumerate(df.itertuples(index=False)):
        movie_show = row[1].strip() if len(row) > 1 else ''
        season_episode = row[5].strip() if len(row) > 5 else ''
        episode_title = row[6].strip() if len(row) > 6 else ''
        start_timecode = row[10].strip() if len(row) > 10 else ''
        end_timecode = row[12].strip() if len(row) > 12 else ''
        comment = row[14].strip() if len(row) > 14 else ''
        timeline_placement = row[24].strip() if len(row) > 24 else ''

        # Only propagate timeline and comment from previous valid scene rows
        if movie_show and start_timecode and end_timecode:
            if timeline_placement:
                last_scene_timeline = timeline_placement
            else:
                timeline_placement = last_scene_timeline
            if comment:
                last_scene_comment = comment
            else:
                comment = last_scene_comment
        else:
            # Not a valid scene row, do not update last_scene_timeline/comment
            if not timeline_placement:
                timeline_placement = last_scene_timeline
            if not comment:
                comment = last_scene_comment

        # If timeline_placement is just a month, search upwards for the most recent section header year
        if month_pattern.fullmatch(timeline_placement):
            year_found = None
            for prev_idx in range(idx-1, -1, -1):
                prev_row = df.iloc[prev_idx]
                possible_year = str(prev_row[1]).strip()
                if year_pattern.fullmatch(possible_year):
                    year_found = possible_year
                    break
            if year_found:
                timeline_placement = f"{timeline_placement} {year_found}"

        # Only extract rows with Movie/Show, start and end timecodes, and timeline placement
        if movie_show and start_timecode and end_timecode and timeline_placement:
            scenes.append({
                'movie_show': movie_show,
                'season_episode': season_episode,
                'episode_title': episode_title,
                'start_timecode': start_timecode,
                'end_timecode': end_timecode,
                'comment': comment,
                'timeline_placement': timeline_placement
            })
    if not scenes:
        print('DEBUG: First 2 rows:', [tuple(df.iloc[i]) for i in range(min(2, len(df)))])
    return scenes 