# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Robo-Bridge is a Docker-based REST API service for controlling Ecovacs Deebot vacuum cleaners. It provides a unified interface for managing multiple vacuum cleaners through HTTP requests, designed for integration with AI assistants and home automation systems.

## Technology Stack

- **Python 3.13** - Primary programming language
- **FastAPI** - Web framework for the REST API
- **deebot-client** - Ecovacs Deebot integration library
- **Docker** - Containerization for deployment
- **uvicorn** - ASGI server

## Common Development Commands

### Local Development
```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run development server
python -m uvicorn src.api:app --reload --host 0.0.0.0 --port 8000
```

### Docker Development
```bash
# Build and run with Docker Compose
docker-compose up -d

# View logs
docker-compose logs -f robo-bridge

# Stop services
docker-compose down
```

### Testing and Validation
```bash
# Test API health
curl http://localhost:8000/health

# List devices
curl http://localhost:8000/devices

# View interactive API docs
open http://localhost:8000/docs
```

## Project Architecture

### Core Components

1. **DeebotManager** (`src/deebot_manager.py`)
   - Manages connections to Ecovacs cloud service
   - Handles device discovery and status tracking
   - Provides abstraction layer for vacuum commands

2. **FastAPI Application** (`src/api.py`)
   - REST API endpoints for device control
   - Request/response models with Pydantic
   - Error handling and logging
   - Health checks and service monitoring

3. **Docker Configuration**
   - Multi-stage build for optimized image size
   - Health checks for container monitoring
   - Environment-based configuration

### Data Flow
```
AI Assistant → HTTP Request → FastAPI → DeebotManager → deebot-client → Ecovacs Cloud → Vacuum Devices
```

## Configuration

### Required Environment Variables
- `ECOVACS_EMAIL` - Ecovacs account email
- `ECOVACS_PASSWORD` - Ecovacs account password
- `ECOVACS_COUNTRY` - Country code (default: US)
- `ECOVACS_CONTINENT` - Continent code (default: NA)

### Supported Vacuum Models
- Ecovacs Deebot T8 Pure
- Ecovacs Deebot U2 series
- Other models supported by deebot-client library

## API Endpoints

### Device Management
- `GET /devices` - List all vacuum cleaners
- `GET /devices/{device_id}/status` - Get device status
- `GET /health` - Service health check

### Vacuum Control
- `POST /devices/{device_id}/start` - Start cleaning
- `POST /devices/{device_id}/stop` - Stop cleaning
- `POST /devices/{device_id}/pause` - Pause cleaning
- `POST /devices/{device_id}/dock` - Return to dock
- `POST /devices/{device_id}/locate` - Make vacuum beep/flash

## Development Notes

- Uses async/await patterns throughout for non-blocking operations
- Implements proper error handling and logging
- Follows FastAPI best practices for API design
- Docker health checks ensure service reliability
- Environment-based configuration for different deployment scenarios

### Status Update Architecture

- **Current**: Event-driven status updates via real-time events from Ecovacs cloud
  - BatteryEvent, StateEvent, ErrorEvent, AvailabilityEvent
  - No polling - relies on push notifications
  - Status cached until new events arrive

- **Future Enhancement Consideration**: Add periodic status polling as fallback
  - Could implement 30-60 second polling with `device.request_status()`
  - Would help with initial state population and connection reliability
  - **CAUTION**: Avoid excessive requests to prevent Ecovacs server blocking
  - Only implement if event-driven approach proves insufficient