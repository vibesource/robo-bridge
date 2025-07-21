# robo-bridge

A Docker-based REST API service for controlling Ecovacs Deebot vacuum cleaners (T8 Pure and U2 series). Built for integration with AI assistants and home automation systems.

## Features

- **✅ Complete REST API** for vacuum control and status monitoring
- **✅ Docker containerized** with production-ready deployment
- **✅ Multi-device support** - handles multiple vacuum cleaners simultaneously  
- **✅ Real-time status updates** with live battery monitoring and device events
- **✅ Full command support**: start, stop, pause, dock, locate operations
- **✅ Event-driven architecture** with async battery level updates
- **✅ Interactive API documentation** at `/docs` endpoint

## Supported Vacuum Models

- Ecovacs Deebot T8 Pure
- Ecovacs Deebot U2 series
- Other models supported by deebot-client library

## Quick Start

### 1. Clone and Setup

```bash
git clone <repository-url>
cd robo-bridge
cp .env.example .env
```

### 2. Configure Environment

Edit `.env` with your Ecovacs account credentials:

```env
ECOVACS_EMAIL=your_email@example.com
ECOVACS_PASSWORD=your_password_here
ECOVACS_COUNTRY=US
ECOVACS_CONTINENT=NA
```

### 3. Run with Docker

```bash
# Build and start the service
docker-compose up -d

# Check service health
curl http://localhost:8000/health
```

## API Endpoints

### Device Management
- `GET /devices` - List all connected vacuum cleaners
- `GET /devices/{device_id}/status` - Get device status
- `GET /health` - Service health check

### Vacuum Control
- `POST /devices/{device_id}/start` - Start cleaning
- `POST /devices/{device_id}/stop` - Stop cleaning
- `POST /devices/{device_id}/pause` - Pause cleaning
- `POST /devices/{device_id}/dock` - Return to dock
- `POST /devices/{device_id}/locate` - Make vacuum beep/flash

### API Documentation
- Interactive docs: `http://localhost:8000/docs`
- OpenAPI spec: `http://localhost:8000/openapi.json`

## Development

### Local Development

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export ECOVACS_EMAIL="your_email@example.com"
export ECOVACS_PASSWORD="your_password"

# Run the API server
python -m uvicorn src.api:app --reload --host 0.0.0.0 --port 8000
```

### Project Structure

```
robo-bridge/
├── src/
│   ├── __init__.py
│   ├── api.py              # FastAPI application
│   └── deebot_manager.py   # Deebot client wrapper
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── .env.example
└── README.md
```

## Integration Examples

### Python Client

```python
import requests

# Get device list
response = requests.get("http://localhost:8000/devices")
devices = response.json()

# Start cleaning on first device
device_id = devices[0]["device_id"]
requests.post(f"http://localhost:8000/devices/{device_id}/start")
```

### Curl Commands

```bash
# List devices
curl http://localhost:8000/devices

# Start cleaning
curl -X POST http://localhost:8000/devices/{device_id}/start

# Get device status
curl http://localhost:8000/devices/{device_id}/status
```

## Current Status

### ✅ Fully Operational
- **Device Discovery**: Successfully discovers and connects to both T8 Pure and U2 vacuum cleaners
- **Real-time Status**: Live battery level monitoring and device online status
- **All Commands Working**: locate, dock, start/stop/pause cleaning operations fully functional
- **Event System**: Proper async battery event handling with real-time status updates
- **Docker Deployment**: Complete containerized solution ready for production
- **FastAPI REST API**: Full endpoint coverage with interactive documentation
- **Multi-device Support**: Handles multiple vacuum cleaners simultaneously
- **Ecovacs Integration**: Robust authentication and API communication (GB/EU region)

## Production Deployment

The API is production-ready and fully tested with both T8 Pure and U2 models:

```bash
# Start production container
docker-compose up -d

# Verify both devices are connected  
curl http://localhost:8000/health
# Expected: {"status": "healthy", "devices_connected": 2, "message": "Connected to 2 devices"}

# Test device control
curl -X POST http://localhost:8000/devices/{device_id}/locate
# Expected: {"success": true, "message": "Locate command sent successfully"}
```

### 🔧 Troubleshooting

#### Regional Configuration
For optimal compatibility, ensure your `.env` matches your Ecovacs app region:

```env
# United Kingdom/Europe
ECOVACS_COUNTRY=GB
ECOVACS_CONTINENT=EU

# United States  
ECOVACS_COUNTRY=US
ECOVACS_CONTINENT=NA
```

#### Common Setup Issues

1. **Authentication Failed**: Verify your Ecovacs credentials match your app login exactly
2. **No Devices Found**: Ensure vacuums are online and visible in Ecovacs Home app  
3. **Command Execution Errors**: Check that devices are not in cleaning mode or have errors

### Logs

```bash
# View container logs
docker-compose logs -f robo-bridge

# Access container for debugging
docker-compose exec robo-bridge bash
```

## License

This project is licensed under the GNU General Public License v3.0 - see the [LICENSE](LICENSE) file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## Acknowledgments

- Built using [deebot-client](https://github.com/DeebotUniverse/client.py) library
- Powered by [FastAPI](https://fastapi.tiangolo.com/) framework