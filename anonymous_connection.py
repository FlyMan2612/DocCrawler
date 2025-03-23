#!/usr/bin/env python3
import os
import time
import socket
import requests
import socks
import stem.process
from stem.util import term
from stem.control import Controller
from contextlib import contextmanager

class AnonymousConnection:
    """
    Provides anonymous connection capabilities through Tor network.
    """
    
    def __init__(self, use_tor=False, tor_port=9050, control_port=9051, tor_password=None):
        """
        Initialize the anonymous connection handler.
        
        Args:
            use_tor (bool): Whether to use Tor for connections
            tor_port (int): The SOCKS port for Tor
            control_port (int): The control port for Tor
            tor_password (str): Password for Tor control port authentication
        """
        self.use_tor = use_tor
        self.tor_port = tor_port
        self.control_port = control_port
        self.tor_password = tor_password
        self.tor_process = None
        self.previous_proxy = None
        
    def start_tor(self, launch=False):
        """
        Start the Tor connection.
        
        Args:
            launch (bool): Whether to launch a new Tor process
                           If False, assumes Tor is already running
        """
        if not self.use_tor:
            return
        
        # Test if Tor is actually running
        if not self._is_tor_running():
            print(term.format("Warning: Tor is not accessible. Falling back to direct connection.", term.Color.YELLOW))
            self.use_tor = False
            return
            
        # Store the previous proxy configuration
        self.previous_proxy = {
            'http': os.environ.get('HTTP_PROXY'),
            'https': os.environ.get('HTTPS_PROXY')
        }
        
        # Launch Tor if required
        if launch:
            try:
                print(term.format("Starting Tor process...", term.Color.BLUE))
                self.tor_process = stem.process.launch_tor_with_config(
                    config = {
                        'SocksPort': str(self.tor_port),
                        'ControlPort': str(self.control_port),
                        'DataDirectory': os.path.join(os.path.expanduser('~'), '.docscoop', 'tor_data'),
                        'CookieAuthentication': '1'
                    },
                    init_msg_handler = self._print_tor_bootstrap_line,
                    take_ownership = True
                )
                print(term.format("Tor process started successfully.", term.Color.GREEN))
            except Exception as e:
                print(term.format(f"Failed to start Tor: {str(e)}", term.Color.RED))
                print(term.format("Falling back to direct connection.", term.Color.YELLOW))
                self.use_tor = False
                return
        
        # Configure requests to use Tor
        self._configure_tor_for_requests()
        
    def _is_tor_running(self):
        """Check if Tor is running and accessible."""
        try:
            # Try to connect to the Tor SOCKS port
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)  # 2 second timeout
            result = sock.connect_ex(('127.0.0.1', self.tor_port))
            sock.close()
            return result == 0
        except:
            return False
        
    def stop_tor(self):
        """Stop the Tor connection and restore previous settings."""
        if not self.use_tor:
            return
            
        # Stop the Tor process if we started it
        if self.tor_process:
            print(term.format("Stopping Tor process...", term.Color.BLUE))
            self.tor_process.kill()
            self.tor_process = None
            print(term.format("Tor process stopped.", term.Color.GREEN))
        
        # Restore the previous proxy configuration
        if self.previous_proxy:
            if self.previous_proxy['http']:
                os.environ['HTTP_PROXY'] = self.previous_proxy['http']
            else:
                os.environ.pop('HTTP_PROXY', None)
                
            if self.previous_proxy['https']:
                os.environ['HTTPS_PROXY'] = self.previous_proxy['https']
            else:
                os.environ.pop('HTTPS_PROXY', None)
    
    def _configure_tor_for_requests(self):
        """Configure the requests library to use Tor."""
        try:
            # Set up the proxy for requests
            os.environ['HTTP_PROXY'] = f'socks5://127.0.0.1:{self.tor_port}'
            os.environ['HTTPS_PROXY'] = f'socks5://127.0.0.1:{self.tor_port}'
            
            # Configure socket for direct connections that bypass requests
            socks.set_default_proxy(socks.SOCKS5, "127.0.0.1", self.tor_port)
            socket.socket = socks.socksocket
            
            # Test the connection
            test_session = requests.Session()
            test_session.get('https://www.google.com', timeout=5)
            
        except Exception as e:
            print(term.format(f"Error configuring Tor connection: {str(e)}", term.Color.RED))
            print(term.format("Falling back to direct connection.", term.Color.YELLOW))
            
            # Reset proxy settings
            os.environ.pop('HTTP_PROXY', None)
            os.environ.pop('HTTPS_PROXY', None)
            
            # Reset socket to normal
            socket.socket = socket._socketobject if hasattr(socket, '_socketobject') else socket._orig_socket
            
            # Disable Tor usage
            self.use_tor = False
    
    def renew_tor_identity(self):
        """Get a new Tor identity (new IP address)."""
        if not self.use_tor:
            return
            
        try:
            print(term.format("Renewing Tor identity...", term.Color.YELLOW))
            with Controller.from_port(port=self.control_port) as controller:
                # Authenticate with the control port
                if self.tor_password:
                    controller.authenticate(password=self.tor_password)
                else:
                    controller.authenticate()
                    
                # Signal Tor to get a new identity
                controller.signal("NEWNYM")
                
                # Wait a moment for the new identity to be established
                time.sleep(5)
            print(term.format("Tor identity renewed.", term.Color.GREEN))
        except Exception as e:
            print(term.format(f"Error renewing Tor identity: {str(e)}", term.Color.RED))
            print(term.format("Continuing with current identity.", term.Color.YELLOW))
    
    def get_session(self):
        """
        Get a requests session configured for anonymous browsing.
        
        Returns:
            requests.Session: A session configured for anonymous access
        """
        session = requests.Session()
        
        if self.use_tor:
            # Add random user agent and other headers to avoid fingerprinting
            session.headers.update({
                'User-Agent': self._get_random_user_agent(),
                'Accept-Language': 'en-US,en;q=0.5',
                'DNT': '1',  # Do Not Track
                'Upgrade-Insecure-Requests': '1'
            })
        else:
            # Even without Tor, use a modern user agent
            session.headers.update({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            })
        
        return session
    
    def _get_random_user_agent(self):
        """Get a random user agent string to avoid fingerprinting."""
        user_agents = [
            # Windows Chrome
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            # Windows Firefox
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:89.0) Gecko/20100101 Firefox/89.0',
            # Mac Safari
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15',
            # Linux Firefox
            'Mozilla/5.0 (X11; Linux x86_64; rv:89.0) Gecko/20100101 Firefox/89.0',
            # Edge
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36 Edg/91.0.864.59'
        ]
        
        import random
        return random.choice(user_agents)
    
    def _print_tor_bootstrap_line(self, line):
        """Print Tor bootstrap progress."""
        if "Bootstrapped " in line:
            print(term.format(line, term.Color.BLUE))

@contextmanager
def anonymous_connection(use_tor=False, launch_tor=False):
    """
    Context manager for anonymous connections.
    
    Args:
        use_tor (bool): Whether to use Tor for connections
        launch_tor (bool): Whether to launch a new Tor process
    
    Yields:
        AnonymousConnection: The anonymous connection handler
    """
    conn = AnonymousConnection(use_tor=use_tor)
    try:
        conn.start_tor(launch=launch_tor)
        yield conn
    finally:
        conn.stop_tor() 