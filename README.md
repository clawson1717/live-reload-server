# 🚀 Live Reload Server

A simple, lightweight HTTP server with auto-reload for static web development. Perfect for quickly prototyping HTML, CSS, and JavaScript without the hassle of manual browser refreshes.

## Features

- **Auto-reload**: Automatically refreshes the browser when files change
- **WebSocket-based**: Uses WebSockets for instant, reliable reloads
- **HTML injection**: Automatically injects the reload script into your pages
- **File watching**: Monitors `.html`, `.css`, `.js`, and `.json` files
- **Lightweight**: Minimal dependencies, simple to use
- **Configurable**: Customize host, port, and directory

## Installation

1. Clone or download this repository
2. Install dependencies:

```bash
pip install -r requirements.txt
```

## Usage

### Basic usage

```bash
python src/server.py
```

This starts the server on `http://localhost:8000` serving files from the current directory.

### With options

```bash
python src/server.py --port 8080 --host 0.0.0.0 --directory ./my-site
```

### CLI Options

| Option | Short | Description | Default |
|--------|-------|-------------|---------|
| `--port` | `-p` | HTTP server port | `8000` |
| `--host` | | Host to bind to | `localhost` |
| `--directory` | `-d` | Directory to serve | `.` (current directory) |
| `--ws-port` | | WebSocket port (for reload) | HTTP port + 1 |

## How It Works

1. The server starts an HTTP server to serve your static files
2. A WebSocket server runs on a separate port (default: HTTP port + 1)
3. When serving HTML files, the server automatically injects a small script that connects to the WebSocket
4. A file watcher monitors your project for changes
5. When a file changes, the server notifies all connected browsers to reload

## Example

Try the included example:

```bash
python src/server.py --directory examples
```

Then open `http://localhost:8000` in your browser. Edit `examples/index.html` and watch the browser automatically reload!

## Project Structure

```
live-reload-server/
├── src/
│   └── server.py          # Main server script
├── examples/
│   └── index.html         # Demo page
├── requirements.txt       # Python dependencies
├── .gitignore            # Git ignore file
└── README.md             # This file
```

## Requirements

- Python 3.7+
- `watchdog` - for file system watching
- `websockets` - for WebSocket communication

## Development

To contribute or modify:

1. Fork the repository
2. Make your changes
3. Test thoroughly
4. Submit a pull request

## License

MIT License - feel free to use this in your projects!

## Credits

Built with ❤️ for Corbin
