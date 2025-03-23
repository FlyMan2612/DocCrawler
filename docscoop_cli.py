#!/usr/bin/env python3
import os
import sys
import argparse
from docscoop import DocScoop

def main():
    """Main entry point for the DocScoop CLI."""
    
    # Create argument parser
    parser = argparse.ArgumentParser(
        description='DocScoop - Scan the web for potentially sensitive documents',
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    # Required arguments
    parser.add_argument('url', help='Starting URL to scan')
    
    # Optional arguments
    parser.add_argument('--depth', type=int, default=2, 
                       help='Maximum depth to crawl')
    parser.add_argument('--timeout', type=int, default=30,
                       help='Timeout for HTTP requests in seconds')
    parser.add_argument('--output', type=str, 
                       help='Save results to this file (CSV format)')
    parser.add_argument('--include-ext', type=str, 
                       help='Additional file extensions to scan (comma-separated)')
    parser.add_argument('--exclude-ext', type=str,
                       help='File extensions to exclude (comma-separated)')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Enable verbose output')
    parser.add_argument('--silent', '-s', action='store_true',
                       help='Suppress all output except final results')
    
    # Anonymous browsing options
    anonymous_group = parser.add_argument_group('Anonymous Browsing')
    anonymous_group.add_argument('--anonymous', '-a', action='store_true',
                               help='Use Tor for anonymous scanning')
    anonymous_group.add_argument('--launch-tor', '-l', action='store_true',
                               help='Launch a Tor process (otherwise uses existing Tor)')
    anonymous_group.add_argument('--tor-port', type=int, default=9050,
                               help='Tor SOCKS port')
    anonymous_group.add_argument('--control-port', type=int, default=9051,
                               help='Tor control port')
    
    # Parse arguments
    args = parser.parse_args()
    
    # Check for API key
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("Error: GEMINI_API_KEY is not set. Please set it in your environment or .env file.")
        return 1
    
    # Configure output mode
    if args.silent:
        # Redirect stdout to null
        sys.stdout = open(os.devnull, 'w')
    
    # Create DocScoop instance with anonymous options if specified
    scoop = DocScoop(
        use_tor=args.anonymous,
        launch_tor=args.launch_tor,
        tor_port=args.tor_port,
        control_port=args.control_port
    )
    
    # Process extensions
    if args.include_ext:
        additional_exts = [f".{ext.strip().lower()}" for ext in args.include_ext.split(',')]
        scoop.DOCUMENT_EXTENSIONS.extend(additional_exts)
    
    if args.exclude_ext:
        excluded_exts = [f".{ext.strip().lower()}" for ext in args.exclude_ext.split(',')]
        # Remove from document extensions
        scoop.DOCUMENT_EXTENSIONS = [ext for ext in scoop.DOCUMENT_EXTENSIONS if ext not in excluded_exts]
        # Add to ignore extensions
        scoop.IGNORE_EXTENSIONS.extend(excluded_exts)
    
    # Run the scan
    try:
        results = scoop.scan_url(args.url, max_depth=args.depth)
        
        # Restore stdout if silent mode was enabled
        if args.silent:
            sys.stdout = sys.__stdout__
        
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
                    if args.verbose:
                        print(f"  Analysis: {result['analysis']}")
        
        # Save results to file if requested
        if args.output:
            save_results_to_csv(results, args.output)
            print(f"\nResults saved to {args.output}")
        
        return 0
    
    except KeyboardInterrupt:
        print("\nScan interrupted by user.")
        return 130
    except Exception as e:
        print(f"Error: {str(e)}")
        return 1

def save_results_to_csv(results, output_file):
    """Save results to a CSV file."""
    import csv
    
    with open(output_file, 'w', newline='') as csvfile:
        fieldnames = ['url', 'is_sensitive', 'analysis']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        for result in results:
            writer.writerow(result)

if __name__ == "__main__":
    sys.exit(main()) 