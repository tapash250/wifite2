# Wifite2 Mobile Bridge & Dashboard
# Initial Project Structure

## Architecture Overview

### Backend (FastAPI Python)
```
wifite2-mobile-bridge/
├── README.md
├── requirements.txt
├── pyproject.toml
├── docker-compose.yml
├── .env.example
├── main.py                    # FastAPI entry point
├── api/
│   ├── __init__.py
│   ├── websocket.py          # WebSocket broadcast manager
│   ├── endpoints.py          # REST endpoints
│   ├── wifite_bridge.py      # Main bridge service
│   └── models.py             # Pydantic models
├── core/
│   ├── __init__.py
│   ├── process_stream.py     # Extended Process class with WebSocket
│   ├── scanner_stream.py     # Scanner wrapper for real-time updates
│   ├── attack_stream.py      # Attack progress streaming
│   └── wifite_service.py     # Service layer
├── database/
│   ├── __init__.py
│   ├── models.py             # SQLAlchemy models
│   ├── schema.py             # SQLite schema
│   ├── powersync.py          # PowerSync integration
│   └── operations.py         # Database operations
├── mobile_adapter/
│   ├── __init__.py
│   ├── android_verification.py  # Monitor Mode/OTG checks
│   └── hardware_monitor.py      # Android hardware checks
└── utils/
    ├── __init__.py
    ├── logging.py            # Structured logging
    ├── config.py             # Configuration manager
    └── security.py           # Security utilities
```

### Frontend (Flutter)
```
wifite2_mobile_flutter/
├── pubspec.yaml
├── lib/
│   ├── main.dart
│   ├── models/
│   │   ├── network.dart
│   │   ├── handshake.dart
│   │   └── scan_result.dart
│   ├── services/
│   │   ├── api_service.dart
│   │   ├── websocket_service.dart
│   │   ├── database_service.dart
│   │   └── hardware_service.dart
│   ├── ui/
│   │   ├── screens/
│   │   │   ├── dashboard/
│   │   │   │   ├── dashboard_screen.dart
│   │   │   │   └── dashboard_viewmodel.dart
│   │   │   ├── scanning/
│   │   │   ├── attacks/
│   │   │   └── settings/
│   │   ├── components/
│   │   │   ├── network_card.dart
│   │   │   ├── signal_strength_bar.dart
│   │   │   └── glassmorphic_card.dart
│   │   └── themes/
│   │       ├── glassmorphism.dart
│   │       └── colors.dart
│   └── utils/
│       ├── constants.dart
│       ├── extensions.dart
│       └── helpers.dart
├── assets/
│   └── icons/
└── android/                   # Android-specific config
```

### Database Schema (SQLite + PowerSync)
```
Tables:
1. networks
   - id (INTEGER PRIMARY KEY)
   - bssid (TEXT UNIQUE)
   - essid (TEXT)
   - channel (INTEGER)
   - signal_strength (INTEGER)
   - encryption (TEXT)
   - authentication (TEXT)
   - wps_enabled (BOOLEAN)
   - last_seen (TIMESTAMP)
   - created_at (TIMESTAMP)

2. handshakes
   - id (INTEGER PRIMARY KEY)
   - network_id (INTEGER REFERENCES networks(id))
   - file_path (TEXT)
   - capture_method (TEXT)  # PMKID, WPA/WPA2, WPS
   - status (TEXT)          # captured, cracking, cracked, failed
   - cracked_password (TEXT)
   - capture_time (TIMESTAMP)
   - crack_time (TIMESTAMP)
   - hashcat_mode (INTEGER)

3. scan_sessions
   - id (INTEGER PRIMARY KEY)
   - interface (TEXT)
   - channel (TEXT)
   - target_count (INTEGER)
   - start_time (TIMESTAMP)
   - end_time (TIMESTAMP)
   - duration (INTEGER)

4. attack_sessions
   - id (INTEGER PRIMARY KEY)
   - network_id (INTEGER REFERENCES networks(id))
   - attack_type (TEXT)      # WPA, WPS, WEP, PMKID
   - status (TEXT)          # running, completed, failed
   - command_line (TEXT)
   - output_log (TEXT)
   - start_time (TIMESTAMP)
   - end_time (TIMESTAMP)

5. device_stats
   - id (INTEGER PRIMARY KEY)
   - monitor_mode_supported (BOOLEAN)
   - otg_enabled (BOOLEAN)
   - last_check (TIMESTAMP)
   - wifi_chipset (TEXT)
```

## FastAPI WebSocket Bridge Core

### Key Components

1. **WebSocketManager**: Singleton for broadcasting to connected clients
2. **ProcessStream**: Subclass of wifite.util.Process with WebSocket hooks
3. **WifiteService**: Main service coordinating scanning, attacks, and streaming
4. **AndroidHardwareVerifier**: Validates monitor mode/OTG capabilities
5. **SQLiteManager**: Local-first database with PowerSync for cloud sync

## Implementation Priority

### Phase 1: Core Bridge
1. FastAPI server with WebSocket endpoints
2. Process class extension for stdout/stderr streaming
3. Basic SQLite schema for networks/handshakes
4. Scanner integration for real-time updates

### Phase 2: Mobile Integration
1. Flutter dashboard with glassmorphism UI
2. WebSocket client for real-time updates
3. Local SQLite with PowerSync
4. Android hardware verification

### Phase 3: Advanced Features
1. Attack progress streaming
2. Hashcat integration with progress reporting
3. Session management
4. Export/import functionality

## Next Steps
1. Create FastAPI project skeleton
2. Implement ProcessStream with WebSocket integration
3. Create SQLite schema
4. Build WebSocket broadcast system
5. Test with wifite2 process execution