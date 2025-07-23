import os
from csv_parser import extract_scenes

def test_extract_scenes():
    scenes = extract_scenes('sample_scenes.csv')
    # There should be at least one known scene from the sample
    assert any(scene['movie_show'] == 'Iron Man' for scene in scenes)
    assert any(scene['timeline_placement'] == '2008' for scene in scenes)
    # Check that all extracted scenes have required fields
    for scene in scenes:
        assert scene['movie_show']
        assert scene['start_timecode']
        assert scene['end_timecode']
        assert scene['timeline_placement']
    # Check that header/section rows are not included
    assert not any(scene['movie_show'].startswith('EVERYTHING') for scene in scenes)
    assert not any(scene['movie_show'].startswith('LEGEND') for scene in scenes)

def test_agents_of_shield_s3e19():
    scenes = extract_scenes('sample_scenes.csv')
    aos_s3e19 = [s for s in scenes if s['movie_show'] == 'Agents of S.H.I.E.L.D.' and s['season_episode'] == '3.19']
    # There should be 6 rows for this episode
    assert len(aos_s3e19) == 6
    # Check all fields for each row
    expected = [
        {
            'episode_title': 'Failed Experiments',
            'start_timecode': '0:00:45',
            'end_timecode': '0:01:35',
            'timeline_placement': '3500 BCE',
        },
        {
            'episode_title': 'Failed Experiments',
            'start_timecode': '0:01:38',
            'end_timecode': '0:01:43',
            'timeline_placement': '3500 BCE',
        },
        {
            'episode_title': 'Failed Experiments',
            'start_timecode': '0:01:46',
            'end_timecode': '0:01:54',
            'timeline_placement': '3500 BCE',
        },
        {
            'episode_title': 'Failed Experiments',
            'start_timecode': '0:01:59',
            'end_timecode': '0:02:02',
            'timeline_placement': '3500 BCE',
        },
        {
            'episode_title': 'Failed Experiments',
            'start_timecode': '0:02:09',
            'end_timecode': '0:02:20',
            'timeline_placement': '3500 BCE',
        },
        {
            'episode_title': 'Failed Experiments',
            'start_timecode': '0:01:20',
            'end_timecode': '0:40:18',
            'timeline_placement': 'JUN 2016',
        },
    ]
    for i, exp in enumerate(expected):
        row = aos_s3e19[i]
        assert row['movie_show'] == 'Agents of S.H.I.E.L.D.'
        assert row['season_episode'] == '3.19'
        assert row['episode_title'] == exp['episode_title']
        assert row['start_timecode'] == exp['start_timecode']
        assert row['end_timecode'] == exp['end_timecode']
        assert row['timeline_placement'] == exp['timeline_placement'] 