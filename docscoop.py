#!/usr/bin/env python3
import os
import requests
import magic
import time
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import google.generativeai as genai
from dotenv import load_dotenv
import tempfile
from tqdm import tqdm
import argparse
from document_parser import DocumentParser
from anonymous_connection import AnonymousConnection

# Load environment variables from .env file
load_dotenv()

# Get API key from environment variables
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Configure Gemini API
genai.configure(api_key=GEMINI_API_KEY)

class DocScoop:
    """
    DocScoop: A tool for scanning the web for potentially sensitive documents.
    """
    
    # File extensions to look for
    DOCUMENT_EXTENSIONS = ['.pdf', '.txt', '.doc', '.docx', '.rtf', '.csv', '.xls', '.xlsx']
    # File extensions to ignore (images, videos, etc.)
    IGNORE_EXTENSIONS = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg', '.mp4', '.avi', '.mov']
    
    def __init__(self, use_tor=False, launch_tor=False, tor_port=9050, control_port=9051):
        self.visited_urls = set()
        self.document_urls = set()
        self.gemini_model = genai.GenerativeModel('gemini-1.5-pro')
        self.document_parser = DocumentParser()
        
        # Initialize anonymous connection
        self.anonymous = use_tor
        self.anonymous_conn = AnonymousConnection(
            use_tor=use_tor, 
            tor_port=tor_port, 
            control_port=control_port
        )
        
        if use_tor:
            # Start Tor
            print("Setting up anonymous connection via Tor...")
            self.anonymous_conn.start_tor(launch=launch_tor)
            
        # Initialize session
        self.session = self.anonymous_conn.get_session() if use_tor else requests.Session()
    
    def __del__(self):
        """Clean up resources when object is destroyed."""
        if self.anonymous:
            self.anonymous_conn.stop_tor()
    
    def is_valid_url(self, url):
        """Check if the URL is valid and not already visited."""
        parsed = urlparse(url)
        return bool(parsed.netloc) and bool(parsed.scheme) and url not in self.visited_urls
    
    def get_file_extension(self, url):
        """Extract the file extension from a URL."""
        parsed = urlparse(url)
        path = parsed.path
        return os.path.splitext(path)[1].lower()
    
    def is_document_url(self, url):
        """Check if the URL points to a document."""
        ext = self.get_file_extension(url)
        return ext in self.DOCUMENT_EXTENSIONS
    
    def should_ignore_url(self, url):
        """Check if the URL should be ignored (images, videos, etc.)."""
        ext = self.get_file_extension(url)
        return ext in self.IGNORE_EXTENSIONS
    
    def crawl_page(self, url, depth=1, max_depth=3):
        """Crawl a web page and extract document URLs."""
        if depth > max_depth or not self.is_valid_url(url):
            return
        
        self.visited_urls.add(url)
        print(f"Crawling: {url}")
        
        try:
            # Use the session for requests
            response = self.session.get(url, timeout=10)
            if response.status_code != 200:
                print(f"Failed to fetch {url}: Status code {response.status_code}")
                return
            
            content_type = response.headers.get('Content-Type', '')
            
            # If it's a document, add it to the list
            if self.is_document_url(url) or ('application/pdf' in content_type or 
                                          'application/msword' in content_type or
                                          'application/vnd.openxmlformats' in content_type):
                print(f"Found document: {url}")
                self.document_urls.add(url)
                return
            
            # If it's an HTML page, extract links and continue crawling
            if 'text/html' in content_type:
                soup = BeautifulSoup(response.text, 'html.parser')
                links = soup.find_all('a', href=True)
                
                for link in links:
                    next_url = urljoin(url, link['href'])
                    
                    # Skip images and other non-document files
                    if self.should_ignore_url(next_url):
                        continue
                    
                    # If it's a document, add it to the list
                    if self.is_document_url(next_url):
                        print(f"Found document: {next_url}")
                        self.document_urls.add(next_url)
                    # Otherwise, continue crawling
                    elif depth < max_depth:
                        self.crawl_page(next_url, depth + 1, max_depth)
        
        except Exception as e:
            print(f"Error crawling {url}: {str(e)}")
            
            # If using Tor and we encounter an error, try to get a new identity
            if self.anonymous and depth <= 1:
                print("Trying to renew Tor identity and retry...")
                self.anonymous_conn.renew_tor_identity()
                self.session = self.anonymous_conn.get_session()
                self.crawl_page(url, depth, max_depth)
    
    def download_document(self, url):
        """Download a document from a URL."""
        try:
            # Use the session for anonymous downloads
            response = self.session.get(url, stream=True, timeout=30)
            if response.status_code != 200:
                print(f"Failed to download {url}: Status code {response.status_code}")
                return None
            
            # Create a temporary file with the correct extension
            ext = self.get_file_extension(url)
            if not ext:
                content_type = response.headers.get('Content-Type', '')
                if 'application/pdf' in content_type:
                    ext = '.pdf'
                elif 'application/msword' in content_type:
                    ext = '.doc'
                elif 'application/vnd.openxmlformats' in content_type:
                    ext = '.docx'
                else:
                    ext = '.txt'
            
            with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as temp_file:
                for chunk in response.iter_content(chunk_size=8192):
                    temp_file.write(chunk)
                temp_path = temp_file.name
            
            return temp_path
        
        except Exception as e:
            print(f"Error downloading {url}: {str(e)}")
            
            # If using Tor and we encounter an error, try to get a new identity and retry
            if self.anonymous:
                print("Trying to renew Tor identity and retry download...")
                self.anonymous_conn.renew_tor_identity()
                self.session = self.anonymous_conn.get_session()
                return self.download_document(url)
            
            return None
    
    def extract_text_from_document(self, file_path):
        """Extract text content from a document file using DocumentParser."""
        try:
            # Use the document parser to extract text
            text = self.document_parser.parse(file_path)
            return text
        
        except Exception as e:
            print(f"Error extracting text from {file_path}: {str(e)}")
            return ""
    
    def analyze_document_content(self, text, url):
        """Use Gemini to analyze document content for sensitivity."""
        if not text or len(text) < 10:
            return False, "Document is empty or too short."
        
        # Limit text length for the API call
        text_sample = text[:10000]  # First 10K characters
        
        prompt = f"""
        Analyze this document content and determine if it appears to be sensitive, private, 
        or unintended for public release. Look for:
        
        1. Personal information (names, addresses, phone numbers, SSNs, etc.)
        2. Financial data (credit card numbers, bank accounts, etc.)
        3. Internal/confidential business information (marked confidential, internal only, etc.)
        4. Login credentials or API keys
        5. Draft documents not meant for public consumption
        6. Any information that seems inappropriate for public access
        
        Document URL: {url}
        
        Document sample text:
        {text_sample}
        
        Respond with:
        1. Is this document potentially sensitive? (Yes/No)
        2. Brief explanation of your determination
        3. Specific sensitive elements found (if any)
        """
        
        try:
            response = self.gemini_model.generate_content(prompt)
            analysis = response.text
            
            # Simple parsing logic - in a real system, you'd want more robust parsing
            is_sensitive = 'yes' in analysis.lower().split('\n')[0].lower()
            
            return is_sensitive, analysis
        
        except Exception as e:
            print(f"Error analyzing document: {str(e)}")
            return False, f"Error analyzing document: {str(e)}"
    
    def scan_url(self, start_url, max_depth=2):
        """Scan a URL for documents and analyze them."""
        print(f"Starting DocScoop scan of {start_url} (max depth: {max_depth})")
        
        if self.anonymous:
            print("Using anonymous connection via Tor")
        
        # Step 1: Crawl the site to find documents
        self.crawl_page(start_url, max_depth=max_depth)
        
        results = []
        
        # Step 2: Process each document
        print(f"\nFound {len(self.document_urls)} documents. Analyzing...")
        for url in tqdm(self.document_urls):
            print(f"\nAnalyzing document: {url}")
            
            # Download the document
            temp_path = self.download_document(url)
            if not temp_path:
                continue
            
            try:
                # Extract text
                text = self.extract_text_from_document(temp_path)
                
                # Analyze with Gemini
                is_sensitive, analysis = self.analyze_document_content(text, url)
                
                result = {
                    "url": url,
                    "is_sensitive": is_sensitive,
                    "analysis": analysis
                }
                
                results.append(result)
                
                if is_sensitive:
                    print(f"⚠️ POTENTIALLY SENSITIVE DOCUMENT: {url}")
                    print(f"Analysis: {analysis}")
                else:
                    print(f"Document appears non-sensitive: {url}")
            
            finally:
                # Clean up the temporary file
                try:
                    os.unlink(temp_path)
                except:
                    pass
        
        return results

def main():
    parser = argparse.ArgumentParser(description='DocScoop - Scan the web for potentially sensitive documents')
    parser.add_argument('url', help='Starting URL to scan')
    parser.add_argument('--depth', type=int, default=2, help='Maximum depth to crawl (default: 2)')
    parser.add_argument('--anonymous', '-a', action='store_true', help='Use Tor for anonymous scanning')
    parser.add_argument('--launch-tor', '-l', action='store_true', help='Launch a Tor process (otherwise uses existing Tor)')
    args = parser.parse_args()
    
    # Check if API key is set
    if not GEMINI_API_KEY:
        print("Error: GEMINI_API_KEY is not set. Please set it in your environment or .env file.")
        return
    
    scoop = DocScoop(use_tor=args.anonymous, launch_tor=args.launch_tor)
    results = scoop.scan_url(args.url, max_depth=args.depth)
    
    # Print summary
    sensitive_count = sum(1 for r in results if r["is_sensitive"])
    print(f"\n=== SCAN SUMMARY ===")
    print(f"Total documents scanned: {len(results)}")
    print(f"Potentially sensitive documents: {sensitive_count}")
    
    if sensitive_count > 0:
        print("\nPotentially sensitive document URLs:")
        for result in results:
            if result["is_sensitive"]:
                print(f"- {result['url']}")

if __name__ == "__main__":
    main() 