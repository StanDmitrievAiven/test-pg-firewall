# PostgreSQL Firewall Test App

A simple web application to test PostgreSQL database connectivity and detect firewall blocking.

## Features

- **Interactive UI**: Enter PostgreSQL credentials directly in the web interface
- **TCP Socket Test**: Checks if the PostgreSQL port is reachable
- **PostgreSQL Authentication Test**: Attempts to connect and authenticate with the database
- **Real-time Status**: Shows connection status with visual indicators
- **Detailed Results**: Displays test duration and error messages

## Usage

### Using Docker

1. Build the Docker image:
```bash
docker build -t pg-firewall-test .
```

2. Run the container:
```bash
docker run -p 5000:5000 \
  -e PG_HOST=pg-1e8c0fd-stan-dmitriev-test.h.aivencloud.com \
  -e PG_PORT=19030 \
  -e PG_USER=avnadmin \
  -e PG_PASSWORD=your_password \
  -e PG_DATABASE=defaultdb \
  pg-firewall-test
```

3. Open your browser and navigate to `http://localhost:5000`

4. Enter your PostgreSQL credentials in the form and click "Test Connection"

### Environment Variables (Optional - defaults are pre-filled in the UI)

- `PG_HOST`: PostgreSQL host (default: `pg-1e8c0fd-stan-dmitriev-test.h.aivencloud.com`)
- `PG_PORT`: PostgreSQL port (default: `19030`)
- `PG_DATABASE`: Database name (default: `defaultdb`)
- `PG_USER`: Database user (default: `avnadmin`)
- `PG_PASSWORD`: Database password (required)

### Local Development

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set environment variables (optional):
```bash
export PG_HOST=pg-1e8c0fd-stan-dmitriev-test.h.aivencloud.com
export PG_PORT=19030
export PG_USER=avnadmin
export PG_PASSWORD=your_password
export PG_DATABASE=defaultdb
```

3. Run the application:
```bash
python app.py
```

4. Open your browser and navigate to `http://localhost:5000`

## Status Indicators

- ✅ **Success**: Connection successful
- 🚫 **Blocked**: Firewall is blocking the connection
- ⚠️ **Partial**: Port is reachable but PostgreSQL connection failed
- ❌ **Error**: Connection test failed

## API Endpoint

The app provides a REST API endpoint:

- `GET /api/check`: Returns JSON with connection test results

Example response:
```json
{
  "timestamp": "2026-01-29T12:00:00",
  "host": "pg-1e8c0fd-stan-dmitriev-test.h.aivencloud.com",
  "port": 19030,
  "overall_status": "success",
  "overall_message": "Connection successful",
  "tests": [
    {
      "name": "TCP Socket Connection",
      "status": "success",
      "message": "Port 19030 is reachable",
      "duration_ms": 45.2
    },
    {
      "name": "PostgreSQL Authentication",
      "status": "success",
      "message": "Successfully connected to PostgreSQL...",
      "duration_ms": 120.5
    }
  ]
}
```
