import os
import sys
import pytest
from click.testing import CliRunner
from main import main

def test_cli_args(monkeypatch):
    runner = CliRunner()
    # Set required env var for movie folder
    monkeypatch.setenv('MEGA_CUT_MOVIE_FOLDER', 'movies')
    with runner.isolated_filesystem():
        with open('test.csv', 'w') as f:
            f.write('movie,season,episode,title,start_time,end_time,timeline\n')
        result = runner.invoke(main, ['--csv', 'test.csv', '--output', 'outdir'])
        assert 'Loading scenes from: test.csv' in result.output
        assert 'Output folder: outdir' in result.output
        assert 'Movie folder: movies' in result.output
        assert result.exit_code == 0

def test_env_vars(monkeypatch):
    runner = CliRunner()
    with runner.isolated_filesystem():
        with open('env.csv', 'w') as f:
            f.write('movie,season,episode,title,start_time,end_time,timeline\n')
        monkeypatch.setenv('MEGA_CUT_CSV', 'env.csv')
        monkeypatch.setenv('MEGA_CUT_OUTPUT', 'envout')
        monkeypatch.setenv('MEGA_CUT_MOVIE_FOLDER', 'envmovies')
        result = runner.invoke(main, [])
        assert 'Loading scenes from: env.csv' in result.output
        assert 'Movie folder: envmovies' in result.output
        assert 'Output folder: envout' in result.output
        assert result.exit_code == 0

def test_missing_all(monkeypatch):
    runner = CliRunner()
    # Unset all env vars
    monkeypatch.delenv('MEGA_CUT_CSV', raising=False)
    monkeypatch.delenv('MEGA_CUT_OUTPUT', raising=False)
    monkeypatch.delenv('MEGA_CUT_MOVIE_FOLDER', raising=False)
    # No CLI args or env vars
    result = runner.invoke(main, [])
    assert 'Error: CSV path, movie folder, and output folder must be specified' in result.output
    assert result.exit_code == 1

def test_movies_cli_arg(monkeypatch):
    runner = CliRunner()
    # Set a different env var to ensure CLI takes precedence
    monkeypatch.setenv('MEGA_CUT_MOVIE_FOLDER', 'env_movies')
    with runner.isolated_filesystem():
        with open('test.csv', 'w') as f:
            f.write('movie,season,episode,title,start_time,end_time,timeline\n')
        result = runner.invoke(main, ['--csv', 'test.csv', '--output', 'outdir', '--movies', 'cli_movies'])
        assert 'Loading scenes from: test.csv' in result.output
        assert 'Output folder: outdir' in result.output
        assert 'Movie folder: cli_movies' in result.output  # Should use CLI arg, not env var
        assert result.exit_code == 0

def test_all_cli_args(monkeypatch):
    runner = CliRunner()
    # Unset all env vars to ensure CLI args work independently
    monkeypatch.delenv('MEGA_CUT_CSV', raising=False)
    monkeypatch.delenv('MEGA_CUT_OUTPUT', raising=False)
    monkeypatch.delenv('MEGA_CUT_MOVIE_FOLDER', raising=False)
    with runner.isolated_filesystem():
        with open('test.csv', 'w') as f:
            f.write('movie,season,episode,title,start_time,end_time,timeline\n')
        result = runner.invoke(main, ['--csv', 'test.csv', '--output', 'outdir', '--movies', 'moviedir'])
        assert 'Loading scenes from: test.csv' in result.output
        assert 'Output folder: outdir' in result.output
        assert 'Movie folder: moviedir' in result.output
        assert result.exit_code == 0 