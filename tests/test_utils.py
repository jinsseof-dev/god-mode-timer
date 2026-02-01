import unittest
from unittest.mock import MagicMock, patch, mock_open
import sys
import os

# src 폴더를 모듈 검색 경로에 추가
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from utils import load_remote_image

class TestUtils(unittest.TestCase):
    
    @patch('utils.get_user_data_path')
    @patch('os.path.exists')
    @patch('os.path.getsize')
    @patch('urllib.request.urlopen')
    @patch('PIL.Image.open')
    @patch('PIL.ImageTk.PhotoImage')
    def test_load_remote_image_cached(self, mock_photo_image, mock_image_open, mock_urlopen, mock_getsize, mock_exists, mock_get_path):
        """이미지가 로컬에 캐시되어 있을 때 다운로드 없이 로드하는지 테스트"""
        # Setup
        mock_get_path.return_value = '/fake/path/image.png'
        mock_exists.return_value = True
        mock_getsize.return_value = 1024 # 파일 크기 > 0
        
        mock_img = MagicMock()
        mock_image_open.return_value = mock_img
        mock_img.resize.return_value = mock_img
        
        mock_photo = MagicMock()
        mock_photo_image.return_value = mock_photo

        # Execute
        result = load_remote_image('image.png', 'http://example.com/image.png', (100, 100))

        # Assert
        mock_get_path.assert_called_with('image.png')
        mock_urlopen.assert_not_called() # 다운로드는 실행되지 않아야 함
        mock_image_open.assert_called_with('/fake/path/image.png')
        self.assertEqual(result, mock_photo)

    @patch('utils.get_user_data_path')
    @patch('os.path.exists')
    @patch('os.path.getsize')
    @patch('urllib.request.urlopen')
    @patch('builtins.open', new_callable=mock_open)
    @patch('PIL.Image.open')
    @patch('PIL.ImageTk.PhotoImage')
    def test_load_remote_image_download(self, mock_photo_image, mock_image_open, mock_file_open, mock_urlopen, mock_getsize, mock_exists, mock_get_path):
        """이미지가 없을 때 다운로드 후 로드하는지 테스트"""
        # Setup
        mock_get_path.return_value = '/fake/path/image.png'
        
        # 1. 첫 번째 체크: 파일 없음 (False) -> 다운로드 트리거
        # 2. 두 번째 체크: 파일 있음 (True) -> 로드 트리거
        mock_exists.side_effect = [False, True]
        mock_getsize.return_value = 1024
        
        # 네트워크 응답 Mock
        mock_response = MagicMock()
        mock_response.read.return_value = b'fake_image_data'
        mock_urlopen.return_value.__enter__.return_value = mock_response

        mock_img = MagicMock()
        mock_image_open.return_value = mock_img
        mock_img.resize.return_value = mock_img
        mock_photo_image.return_value = MagicMock()

        # Execute
        load_remote_image('image.png', 'http://example.com/image.png', (100, 100))

        # Assert
        mock_urlopen.assert_called()
        mock_file_open.assert_called_with('/fake/path/image.png', 'wb')
        mock_file_open().write.assert_called_with(b'fake_image_data')
        mock_image_open.assert_called_with('/fake/path/image.png')

    @patch('utils.get_user_data_path')
    @patch('os.path.exists')
    @patch('urllib.request.urlopen')
    def test_load_remote_image_fail(self, mock_urlopen, mock_exists, mock_get_path):
        """다운로드 실패 또는 예외 발생 시 None 반환 테스트"""
        mock_get_path.return_value = '/fake/path/image.png'
        mock_exists.return_value = False
        mock_urlopen.side_effect = Exception("Network Error")

        result = load_remote_image('image.png', 'http://example.com/image.png', (100, 100))
        self.assertIsNone(result)

if __name__ == '__main__':
    unittest.main()