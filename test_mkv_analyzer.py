import os
import tempfile
import json
import subprocess
from unittest.mock import patch, MagicMock
import pytest
from mkv_analyzer import MKVAnalyzer

class TestMKVAnalyzer:
    """Test cases for MKVAnalyzer class."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.analyzer = MKVAnalyzer()
    
    def test_format_language_display(self):
        """Test language code formatting."""
        assert self.analyzer.format_language_display('eng') == 'English'
        assert self.analyzer.format_language_display('spa') == 'Spanish'
        assert self.analyzer.format_language_display('fra') == 'French'
        assert self.analyzer.format_language_display('unknown') == 'Unknown'
        assert self.analyzer.format_language_display('xyz') == 'XYZ'  # Unknown code
    
    @patch('mkv_analyzer.subprocess.run')
    @patch('mkv_analyzer.os.path.exists')
    def test_get_audio_languages_success(self, mock_exists, mock_run):
        """Test successful audio language extraction."""
        # Mock file exists
        mock_exists.return_value = True
        
        # Mock ffprobe output
        mock_output = {
            "streams": [
                {
                    "index": 1,
                    "codec_name": "aac",
                    "channels": 2,
                    "tags": {
                        "language": "eng",
                        "title": "English"
                    }
                },
                {
                    "index": 2,
                    "codec_name": "aac", 
                    "channels": 2,
                    "tags": {
                        "language": "spa",
                        "title": "Spanish"
                    }
                }
            ]
        }
        
        mock_result = MagicMock()
        mock_result.stdout = json.dumps(mock_output)
        mock_run.return_value = mock_result
        
        # Test with a dummy path
        result = self.analyzer.get_audio_languages("/dummy/path.mkv")
        
        assert len(result) == 2
        assert result[0]['language'] == 'eng'
        assert result[0]['title'] == 'English'
        assert result[0]['index'] == '1'
        assert result[1]['language'] == 'spa'
        assert result[1]['title'] == 'Spanish'
        assert result[1]['index'] == '2'
        
        # Verify ffprobe was called correctly
        mock_run.assert_called_once()
        call_args = mock_run.call_args[0][0]
        assert call_args[0] == 'ffprobe'
        assert call_args[1] == '-v'
        assert call_args[2] == 'quiet'
    
    @patch('mkv_analyzer.subprocess.run')
    @patch('mkv_analyzer.os.path.exists')
    def test_get_audio_languages_no_streams(self, mock_exists, mock_run):
        """Test handling of MKV files with no audio streams."""
        mock_exists.return_value = True
        mock_output = {"streams": []}
        mock_result = MagicMock()
        mock_result.stdout = json.dumps(mock_output)
        mock_run.return_value = mock_result
        
        result = self.analyzer.get_audio_languages("/dummy/path.mkv")
        assert result == []
    
    @patch('mkv_analyzer.subprocess.run')
    @patch('mkv_analyzer.os.path.exists')
    def test_get_audio_languages_missing_language_tag(self, mock_exists, mock_run):
        """Test handling of audio streams without language tags."""
        mock_exists.return_value = True
        mock_output = {
            "streams": [
                {
                    "index": 1,
                    "codec_name": "aac",
                    "channels": 2,
                    "tags": {}
                }
            ]
        }
        
        mock_result = MagicMock()
        mock_result.stdout = json.dumps(mock_output)
        mock_run.return_value = mock_result
        
        result = self.analyzer.get_audio_languages("/dummy/path.mkv")
        assert len(result) == 1
        assert result[0]['language'] == 'unknown'
    
    def test_get_audio_languages_file_not_found(self):
        """Test handling of non-existent files."""
        result = self.analyzer.get_audio_languages("/nonexistent/file.mkv")
        assert result == []
    
    @patch('mkv_analyzer.subprocess.run')
    @patch('mkv_analyzer.os.path.exists')
    def test_get_audio_languages_ffprobe_error(self, mock_exists, mock_run):
        """Test handling of ffprobe errors."""
        mock_exists.return_value = True
        mock_run.side_effect = subprocess.CalledProcessError(1, 'ffprobe')
        
        result = self.analyzer.get_audio_languages("/dummy/path.mkv")
        assert result == []
    
    def test_analyze_movie_folder(self):
        """Test movie folder analysis."""
        movie_names = ["Test Movie 1", "Test Movie 2"]
        
        # Mock the get_audio_languages method
        with patch.object(self.analyzer, 'get_audio_languages') as mock_get_languages:
            mock_get_languages.side_effect = [
                [{'index': '1', 'language': 'eng', 'title': 'English'}],  # First movie
                []  # Second movie (not found)
            ]
            
            # Mock os.path.exists to simulate file existence
            with patch('mkv_analyzer.os.path.exists') as mock_exists:
                # Need to handle both possible paths for each movie
                mock_exists.side_effect = [
                    True,   # Test Movie 1.mkv exists
                    False,  # Test Movie 1.MKV doesn't exist
                    False,  # Test Movie 2.mkv doesn't exist
                    False   # Test Movie 2.MKV doesn't exist
                ]
                
                result = self.analyzer.analyze_movie_folder("/dummy/folder", movie_names)
                
                assert len(result) == 2
                assert len(result["Test Movie 1"]) == 1
                assert result["Test Movie 2"] == []
    
    def test_display_language_summary(self, capsys):
        """Test the display summary method."""
        movie_languages = {
            "Test Movie 1": [
                {'index': '1', 'language': 'eng', 'title': 'English', 'codec': 'aac', 'channels': '2'},
                {'index': '2', 'language': 'spa', 'title': 'Spanish', 'codec': 'aac', 'channels': '2'}
            ],
            "Test Movie 2": []
        }
        
        # This should not raise any exceptions
        self.analyzer.display_language_summary(movie_languages)
        
        # Verify output was generated (basic check)
        captured = capsys.readouterr()
        assert "Movie Audio Language Analysis" in captured.out

if __name__ == '__main__':
    pytest.main([__file__]) 