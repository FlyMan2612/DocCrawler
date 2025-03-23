# DocScoop

DocScoop is a tool for scanning the web for publicly accessible documents (e.g., PDFs, .txt, .docx) that appear sensitive, private, or unintended for public release.

## Features

- Crawls websites to discover document files
- Supports PDF, TXT, DOC, DOCX, RTF, CSV, XLS, XLSX
- Automatically ignores image files
- Uses Gemini AI to analyze document content for sensitivity
- Identifies potentially sensitive information like personal data, financial information, credentials, etc.
- **Anonymous scanning via Tor network** for privacy and protection

## Requirements

- Python 3.7+
- Gemini API key from Google AI Studio
- Tor (optional, for anonymous scanning)

## Installation

1. Clone this repository:
   ```
   git clone https://github.com/yourusername/docscoop.git
   cd docscoop
   ```

2. Install required dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Install libmagic (required for python-magic):
   - On Ubuntu/Debian: `sudo apt-get install libmagic1`
   - On macOS: `brew install libmagic`
   - On Windows: See python-magic documentation for Windows setup

4. For anonymous scanning, install Tor:
   - On Ubuntu/Debian: `sudo apt-get install tor`
   - On macOS: `brew install tor`
   - On Windows: Download the Tor Browser Bundle and extract the tor.exe file

5. Copy the example environment file and add your Gemini API key:
   ```
   cp .env.example .env
   ```
   Then edit `.env` with your Gemini API key.

## Usage

### Basic Usage:
```
python docscoop.py https://example.com
```

### Specify Crawl Depth:
```
python docscoop.py https://example.com --depth 3
```

### Anonymous Scanning via Tor:
```
python docscoop.py https://example.com --anonymous
```

### Launch a New Tor Process:
```
python docscoop.py https://example.com --anonymous --launch-tor
```

### Advanced CLI Options:
```
python docscoop_cli.py https://example.com --depth 3 --anonymous --output results.csv --verbose
```

The tool will:
1. Crawl the website to find document files
2. Download each document and extract its text
3. Analyze the content using Gemini AI
4. Report potentially sensitive documents

## Anonymous Scanning

DocScoop supports anonymous scanning through the Tor network to protect your privacy when scanning websites. When using the `--anonymous` flag, DocScoop will:

1. Route all traffic through the Tor network
2. Use random user agents to avoid browser fingerprinting
3. Automatically retry failed requests with new Tor identity
4. Maintain privacy throughout the scanning process

To use this feature, either:

- Have Tor already running on your system (default ports: 9050/9051)
- Use the `--launch-tor` flag to have DocScoop start a Tor process for you

Note: Anonymous scanning will be slower than regular scanning due to Tor network latency.

## Command Line Options

```
usage: docscoop_cli.py [-h] [--depth DEPTH] [--timeout TIMEOUT] [--output OUTPUT]
                       [--include-ext INCLUDE_EXT] [--exclude-ext EXCLUDE_EXT]
                       [--verbose] [--silent] [--anonymous] [--launch-tor]
                       [--tor-port TOR_PORT] [--control-port CONTROL_PORT]
                       url

DocScoop - Scan the web for potentially sensitive documents

positional arguments:
  url                   Starting URL to scan

optional arguments:
  -h, --help            show this help message and exit
  --depth DEPTH         Maximum depth to crawl (default: 2)
  --timeout TIMEOUT     Timeout for HTTP requests in seconds (default: 30)
  --output OUTPUT       Save results to this file (CSV format)
  --include-ext INCLUDE_EXT
                        Additional file extensions to scan (comma-separated)
  --exclude-ext EXCLUDE_EXT
                        File extensions to exclude (comma-separated)
  --verbose, -v         Enable verbose output
  --silent, -s          Suppress all output except final results

Anonymous Browsing:
  --anonymous, -a       Use Tor for anonymous scanning
  --launch-tor, -l      Launch a Tor process (otherwise uses existing Tor)
  --tor-port TOR_PORT   Tor SOCKS port (default: 9050)
  --control-port CONTROL_PORT
                        Tor control port (default: 9051)
```

## Limitations

- The current implementation only extracts text from plaintext files.
- For PDFs, DOCs, etc., you'll need to add libraries like PyPDF2, python-docx, etc.
- The crawling is limited to the specified depth and may not find all documents.
- Analysis is only as good as the AI model's understanding of sensitive information.
- Anonymous scanning requires a working Tor installation or network access to launch Tor.

## Legal and Ethical Use

This tool is intended for security researchers, penetration testers, and website owners to identify their own leaked sensitive documents. Please use responsibly and ethically:

1. Only scan websites you own or have explicit permission to scan
2. Follow responsible disclosure if you find sensitive information
3. Do not use this tool for unauthorized access or data collection
4. Respect website terms of service and robots.txt directives

## License

MIT 