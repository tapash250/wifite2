# PowerSync Configuration for Wifite2 Mobile Bridge

This directory contains the database schema and PowerSync configuration for the Wifite2 Mobile Bridge application.

## Database Schema (`schema.sql`)

The schema defines tables for storing wireless network scan results, handshakes, scan sessions, attack attempts, and device capabilities.

### Tables

1. **networks** - Stores discovered wireless networks
   - BSSID, ESSID, channel, signal strength, security type, WPS flag
   - Timestamps for first/last seen and packet count

2. **handshakes** - Stores captured WPA/WPA2 handshakes and PMKIDs
   - Linked to networks via foreign key
   - Hash storage, crack status, progress tracking

3. **scan_sessions** - Tracks each scanning operation
   - Start/end times, interface used, channels scanned
   - Counts of networks found and handshakes captured

4. **attack_attempts** - Records attacks against networks
   - Attack type, start/end times, status, progress
   - Linked to networks and handshakes

5. **device_capabilities** - Stores wireless interface capabilities
   - Monitor mode support, packet injection, supported bands/channels
   - Driver information and max TX power

### Views

- `network_handshake_status`: Networks with handshake counts and crack status
- `active_scan_sessions`: Currently active scanning sessions
- `recent_handshakes`: Handshakes captured in the last 24 hours

### Triggers

- Automatic timestamp updates for networks and handshakes tables

## PowerSync Configuration (`powersync-config.yaml`)

This file configures PowerSync for local-first synchronization between the Flutter frontend and the backend.

### Key Settings

- **database**: Points to the local SQLite database (`./tool.db`)
- **sync.backend_url**: URL of the PowerSync backend service (defaults to localhost)
- **sync.auth_token**: Authentication token for secure sync (set via environment variable)
- **sync.tables**: List of tables to synchronize
- **sync.interval**: Sync interval in seconds (5 seconds)
- **sync.conflict_resolution**: Strategy for handling conflicts (`latest_wins`)
- **table_configs**: Bidirectional sync configuration for each table

### Usage

1. Copy this configuration to your Flutter app's assets directory
2. Initialize PowerSync in your Flutter app using this YAML file
3. Set the `POWERSYNC_BACKEND_URL` and `POWERSYNC_AUTH_TOKEN` environment variables in production

### Backend Endpoint

The PowerSync backend endpoint is expected to be available at:
`{backend_url}/powersync`

Note: This project currently implements a FastAPI backend that serves as the tool bridge.
A separate PowerSync backend service would need to be implemented or integrated
to handle the synchronization protocol. For initial development, you can use
PowerSync's Firebase or custom backend options.

## Environment Variables

- `POWERSYNC_BACKEND_URL`: URL of the PowerSync backend (default: http://localhost:8000/powersync)
- `POWERSYNC_AUTH_TOKEN`: Authentication token for PowerSync
- `POWERSYNC_ENABLED`: Set to "false" to disable sync (useful for offline testing)

## Development Notes

For initial development and testing, you can:
1. Use the local SQLite database without PowerSync enabled
2. Implement a simple PowerSync backend using the FastAPI framework
3. Use PowerSync's official server or Firebase extension when ready for production

The schema is designed to be extensible - additional columns or tables can be added
as needed for specific wifite2 output parsing or additional features.