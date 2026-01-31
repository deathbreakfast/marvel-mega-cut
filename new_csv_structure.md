# New CSV Structure for Marvel Mega Cut

## Overview
The new CSV structure will be much simpler and more maintainable, supporting languages and audio titles while being easier to parse and extend.

## Column Layout

| Column | Name | Type | Required | Description |
|--------|------|------|----------|-------------|
| 1 | movie_show | string | Yes | Movie or show title |
| 2 | season_episode | string | No | Season and episode (e.g., "1.05", "S02E03") |
| 3 | episode_title | string | No | Episode title |
| 4 | start_timecode | string | Yes | Start timecode (HH:MM:SS) |
| 5 | end_timecode | string | Yes | End timecode (HH:MM:SS) |
| 6 | timeline_placement | string | Yes | Timeline placement (e.g., "2016", "3500 BCE") |
| 7 | comment | string | No | Scene description or notes |
| 8 | language | string | No | Language code (e.g., "en", "es", "fr") |
| 9 | audio_title | string | No | Audio track title or description |
| 10 | reality_designation | string | No | Reality/timeline designation (e.g., "EARTH-199999") |

## Example CSV

```csv
movie_show,season_episode,episode_title,start_timecode,end_timecode,timeline_placement,comment,language,audio_title,reality_designation
Black Panther,,,0:00:14,0:01:45,2,500,000 BCE,Prologue: N'Jobu narrating the story of the first Black Panther and the formation of Wakanda to his son N'Jadaka (Erik).,en,Original Audio,EARTH-199999
Agents of S.H.I.E.L.D.,3.19,Failed Experiments,0:00:45,0:01:35,3500 BCE,NOTE: During this flashback sequence Hive is telling the story of his Inhuman transformation (Terrigenesis) in the present. The following clips leave out his narration.,en,Original Audio,EARTH-199999
Thor: The Dark World,,,0:00:35,0:03:39,2988 BCE,Prologue: Odin narrating the story of The Convergence,en,Original Audio,EARTH-199999
Loki,S01E02,The Variant,0:24:56,0:27:24,79,Loki and Mobius visiting Pompeii just prior to the eruption of Mount Vesuvius,en,Original Audio,EARTH-199999
```

## Benefits

1. **Simple**: Only 10 columns, all clearly defined
2. **Extensible**: Easy to add new columns without breaking existing code
3. **Language Support**: Dedicated language column
4. **Audio Support**: Dedicated audio title column
5. **Maintainable**: No complex parsing logic needed
6. **Compatible**: Can migrate from old structure

## Migration Strategy

1. Create new CSV parser with simple column-based parsing
2. Create migration script to convert old CSV to new format
3. Update main application to use new parser
4. Provide command-line option for migration 