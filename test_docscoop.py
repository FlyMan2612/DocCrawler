#!/usr/bin/env python3
import unittest
from unittest.mock import patch, MagicMock
from docscoop import DocScoop
from urllib.parse import urlparse

class TestDocScoop(unittest.TestCase):
    """Test cases for DocScoop."""

    def setUp(self):
        """Set up DocScoop instance for testing."""
        # Create a DocScoop instance with a mock Gemini model
        with patch('google.generativeai.GenerativeModel') as mock_model:
            self.docscoop = DocScoop()
            self.docscoop.gemini_model = MagicMock()
    
    def test_is_valid_url(self):
        """Test URL validation."""
        # Valid URLs
        self.assertTrue(self.docscoop.is_valid_url("https://example.com"))
        self.assertTrue(self.docscoop.is_valid_url("http://test.org/path"))
        
        # Invalid URLs
        self.assertFalse(self.docscoop.is_valid_url("not-a-url"))
        self.assertFalse(self.docscoop.is_valid_url(""))
        
        # Already visited URL
        self.docscoop.visited_urls.add("https://visited.com")
        self.assertFalse(self.docscoop.is_valid_url("https://visited.com"))
    
    def test_get_file_extension(self):
        """Test file extension extraction."""
        self.assertEqual(self.docscoop.get_file_extension("https://example.com/doc.pdf"), ".pdf")
        self.assertEqual(self.docscoop.get_file_extension("https://example.com/path/file.docx"), ".docx")
        self.assertEqual(self.docscoop.get_file_extension("https://example.com/"), "")
        self.assertEqual(self.docscoop.get_file_extension("https://example.com/no-extension"), "")
    
    def test_is_document_url(self):
        """Test document URL detection."""
        # Document URLs
        self.assertTrue(self.docscoop.is_document_url("https://example.com/document.pdf"))
        self.assertTrue(self.docscoop.is_document_url("https://example.com/path/file.docx"))
        self.assertTrue(self.docscoop.is_document_url("https://example.com/data.xlsx"))
        
        # Non-document URLs
        self.assertFalse(self.docscoop.is_document_url("https://example.com/image.jpg"))
        self.assertFalse(self.docscoop.is_document_url("https://example.com/"))
        self.assertFalse(self.docscoop.is_document_url("https://example.com/page.html"))
    
    def test_should_ignore_url(self):
        """Test URL ignore logic."""
        # URLs to ignore
        self.assertTrue(self.docscoop.should_ignore_url("https://example.com/image.jpg"))
        self.assertTrue(self.docscoop.should_ignore_url("https://example.com/picture.png"))
        self.assertTrue(self.docscoop.should_ignore_url("https://example.com/video.mp4"))
        
        # URLs not to ignore
        self.assertFalse(self.docscoop.should_ignore_url("https://example.com/document.pdf"))
        self.assertFalse(self.docscoop.should_ignore_url("https://example.com/"))
        self.assertFalse(self.docscoop.should_ignore_url("https://example.com/page.html"))
    
    def test_analyze_document_content(self):
        """Test document content analysis."""
        # Mock Gemini response
        mock_response = MagicMock()
        mock_response.text = "Yes\nThis document contains sensitive information\nFound: SSN, credit card numbers"
        self.docscoop.gemini_model.generate_content.return_value = mock_response
        
        # Test with sensitive document
        is_sensitive, analysis = self.docscoop.analyze_document_content(
            "This is a sensitive document with SSN 123-45-6789", 
            "https://example.com/doc.pdf"
        )
        self.assertTrue(is_sensitive)
        self.assertEqual(analysis, mock_response.text)
        
        # Test with empty document
        is_sensitive, analysis = self.docscoop.analyze_document_content("", "https://example.com/doc.pdf")
        self.assertFalse(is_sensitive)

if __name__ == "__main__":
    unittest.main() 