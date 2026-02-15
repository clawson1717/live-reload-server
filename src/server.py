#!/usr/bin/env python3
"""
Live Reload Server - A simple HTTP server with auto-reload for static web development.
"""

import argparse
import asyncio
import os
import sys
import mimetypes
from http.server import HTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from threading import Thread

from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import websockets

# WebSocket clients (browsers to notify)
clients = set()
ws_port = None

# Live reload script to inject into HTML
LIVE_RELOAD_SCRIPT = '''
<script>
(function() {
    const ws = new WebSocket('ws://localhost:PORT_PLACEHOLDER');
    ws.onopen = () => console.log('[Live Reload] Connected');
    ws.onmessage = () => {
        console.log('[Live Reload] Reloading...');
        window.location.reload();
    };
    ws.onclose = () => console.log('[Live Reload] Disconnected');
})();
</script>
'''


class ReloadHandler(FileSystemEventHandler):
    """Watchdog handler that triggers browser reload on file changes."""
    
    def __init__(self, loop):
        self.loop = loop
        self.debounce_timer = None
    
    def on_modified(self, event):
        if event.is_directory:
            return
        if event.src_path.endswith(('.html', '.htm', '.css', '.js', '.json')):
            print(f"[Watch] File changed: {event.src_path}")
            self._trigger_reload()
    
    def on_created(self, event):
        if event.is_directory:
            return
        if event.src_path.endswith(('.html', '.htm', '.css', '.js', '.json')):
            print(f"[Watch] File created: {event.src_path}")
            self._trigger_reload()
    
    def _trigger_reload(self):
        # Debounce to avoid multiple rapid reloads
        if self.debounce_timer:
            self.debounce_timer.cancel()
        self.debounce_timer = asyncio.run_coroutine_threadsafe(
            self._notify_clients(), self.loop
        )
    
    async def _notify_clients(self):
        await asyncio.sleep(0.1)  # Small debounce delay
        if clients:
            print(f"[Live Reload] Notifying {len(clients)} client(s) to reload...")
            disconnected = set()
            for ws in clients:
                try:
                    await ws.send("reload")
                except:
                    disconnected.add(ws)
            clients.difference_update(disconnected)


class LiveReloadRequestHandler(SimpleHTTPRequestHandler):
    """HTTP handler that injects live-reload script into HTML responses."""
    
    def __init__(self, *args, ws_port=None, **kwargs):
        self.ws_port = ws_port
        super().__init__(*args, **kwargs)
    
    def do_GET(self):
        # Get the file path
        path = self.translate_path(self.path)
        
        # Check if it's an HTML file
        if path.endswith('.html') or path.endswith('.htm'):
            if os.path.exists(path):
                self._serve_html_with_reload(path)
                return
        
        # Fall back to default handler
        super().do_GET()
    
    def _serve_html_with_reload(self, path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Inject the live reload script before </body> or </head>
            script = LIVE_RELOAD_SCRIPT.replace('PORT_PLACEHOLDER', str(self.ws_port))
            
            if '</body>' in content:
                content = content.replace('</body>', script + '</body>')
            elif '</head>' in content:
                content = content.replace('</head>', script + '</head>')
            else:
                # Just append if no body/head closing tag
                content += script
            
            # Send response
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.send_header('Content-Length', len(content.encode('utf-8')))
            self.end_headers()
            self.wfile.write(content.encode('utf-8'))
            
        except Exception as e:
            self.send_error(500, str(e))
    
    def log_message(self, format, *args):
        # Custom logging
        print(f"[HTTP] {self.address_string()} - {format % args}")


class CustomHTTPServer(HTTPServer):
    """Custom HTTP server that passes ws_port to handler."""
    
    def __init__(self, *args, ws_port=None, **kwargs):
        self.ws_port = ws_port
        super().__init__(*args, **kwargs)
    
    def finish_request(self, request, client_address):
        self.RequestHandlerClass(request, client_address, self, ws_port=self.ws_port)


async def websocket_server(port):
    """WebSocket server to notify browsers to reload."""
    
    async def handler(websocket, path):
        clients.add(websocket)
        print(f"[WebSocket] Client connected (total: {len(clients)})")
        try:
            await websocket.wait_closed()
        finally:
            clients.discard(websocket)
            print(f"[WebSocket] Client disconnected (total: {len(clients)})")
    
    async with websockets.serve(handler, "localhost", port):
        print(f"[WebSocket] Server running on ws://localhost:{port}")
        await asyncio.Future()  # Run forever


def start_websocket_server(port):
    """Start WebSocket server in a separate thread."""
    asyncio.run(websocket_server(port))


def start_file_watcher(directory, loop):
    """Start file watcher in a separate thread."""
    event_handler = ReloadHandler(loop)
    observer = Observer()
    observer.schedule(event_handler, directory, recursive=True)
    observer.start()
    print(f"[Watch] Monitoring files in: {directory}")
    return observer


def main():
    parser = argparse.ArgumentParser(
        description='Live Reload Server - Static file server with auto-reload'
    )
    parser.add_argument(
        '--port', '-p',
        type=int,
        default=8000,
        help='HTTP server port (default: 8000)'
    )
    parser.add_argument(
        '--host',
        default='localhost',
        help='Host to bind to (default: localhost)'
    )
    parser.add_argument(
        '--directory', '-d',
        default='.',
        help='Directory to serve (default: current directory)'
    )
    parser.add_argument(
        '--ws-port',
        type=int,
        default=None,
        help='WebSocket port (default: HTTP port + 1)'
    )
    
    args = parser.parse_args()
    
    # Resolve directory
    serve_directory = os.path.abspath(args.directory)
    if not os.path.isdir(serve_directory):
        print(f"Error: Directory not found: {serve_directory}")
        sys.exit(1)
    
    os.chdir(serve_directory)
    
    # Determine WebSocket port
    ws_port = args.ws_port or args.port + 1
    global ws_port_global
    ws_port_global = ws_port
    
    print("=" * 50)
    print("  Live Reload Server")
    print("=" * 50)
    print(f"  Serving:    {serve_directory}")
    print(f"  HTTP:       http://{args.host}:{args.port}")
    print(f"  WebSocket:  ws://localhost:{ws_port}")
    print("=" * 50)
    print("  Press Ctrl+C to stop")
    print("")
    
    # Get the event loop for the main thread
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    # Start file watcher
    observer = start_file_watcher(serve_directory, loop)
    
    # Start WebSocket server in a thread
    ws_thread = Thread(target=start_websocket_server, args=(ws_port,), daemon=True)
    ws_thread.start()
    
    # Create HTTP server
    def handler_factory(*args, **kwargs):
        return LiveReloadRequestHandler(*args, ws_port=ws_port, **kwargs)
    
    httpd = CustomHTTPServer((args.host, args.port), handler_factory, ws_port=ws_port)
    
    try:
        print(f"[HTTP] Server running on http://{args.host}:{args.port}")
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n[Server] Shutting down...")
    finally:
        observer.stop()
        observer.join()
        httpd.server_close()
        print("[Server] Goodbye!")


if __name__ == '__main__':
    main()
