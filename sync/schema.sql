-- Wifite2 Mobile Bridge Database Schema
-- Designed for PowerSync local-first synchronization

-- Networks table: stores information about discovered wireless networks
CREATE TABLE IF NOT EXISTS networks (
    id TEXT PRIMARY KEY,
    bssid TEXT NOT NULL,
    essid TEXT NOT NULL,
    channel INTEGER,
    signal_strength INTEGER,
    security TEXT,
    wps BOOLEAN DEFAULT 0,
    first_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_seen TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    packet_count INTEGER DEFAULT 0,
    -- Indexes for query performance
    INDEX idx_essid (essid),
    INDEX idx_bssid (bssid),
    INDEX idx_signal (signal_strength),
    INDEX idx_last_seen (last_seen)
);

-- Handshakes table: stores captured WPA/WPA2 handshakes and PMKIDs
CREATE TABLE IF NOT EXISTS handshakes (
    id TEXT PRIMARY KEY,
    network_id TEXT NOT NULL,
    handshake_type TEXT NOT NULL,  -- 'wpa_handshake', 'pmkid', etc.
    hash TEXT,                     -- The actual hash for cracking
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status TEXT DEFAULT 'captured', -- 'captured', 'cracking', 'cracked', 'failed'
    crack_attempts INTEGER DEFAULT 0,
    crack_progress REAL DEFAULT 0.0, -- 0.0 to 1.0
    crack_start_time TIMESTAMP NULL,
    crack_end_time TIMESTAMP NULL,
    cracked_password TEXT NULL,
    FOREIGN KEY (network_id) REFERENCES networks(id) ON DELETE CASCADE,
    -- Indexes
    INDEX idx_network_id (network_id),
    INDEX idx_status (status),
    INDEX idx_timestamp (timestamp)
);

-- Scan sessions: track each scanning operation
CREATE TABLE IF NOT EXISTS scan_sessions (
    id TEXT PRIMARY KEY,
    start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    end_time TIMESTAMP NULL,
    interface TEXT,
    channels_scanned TEXT, -- JSON array or comma-separated list
    networks_found INTEGER DEFAULT 0,
    handshakes_captured INTEGER DEFAULT 0,
    status TEXT DEFAULT 'active', -- 'active', 'completed', 'stopped', 'error'
    config_snapshot TEXT, -- JSON string of the configuration used
    FOREIGN KEY (interface) REFERENCES networks(interface) -- Note: This is denormalized for simplicity
);

-- Attack attempts: track attacks against networks
CREATE TABLE IF NOT EXISTS attack_attempts (
    id TEXT PRIMARY KEY,
    network_id TEXT NOT NULL,
    handshake_id TEXT NULL, -- NULL if attacking without handshake (e.g., WPS)
    attack_type TEXT NOT NULL, -- 'wpa_dict', 'wps_pin', 'wps_pixiedust', etc.
    start_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    end_time TIMESTAMP NULL,
    status TEXT DEFAULT 'running', -- 'running', 'completed', 'stopped', 'failed'
    progress REAL DEFAULT 0.0, -- 0.0 to 1.0
    guesses_tried INTEGER DEFAULT 0,
    guesses_per_second REAL DEFAULT 0.0,
    cracked_password TEXT NULL,
    FOREIGN KEY (network_id) REFERENCES networks(id) ON DELETE CASCADE,
    FOREIGN KEY (handshake_id) REFERENCES handshakes(id) ON DELETE SET NULL,
    -- Indexes
    INDEX idx_network_id (network_id),
    INDEX idx_handshake_id (handshake_id),
    INDEX idx_status (status),
    INDEX idx_start_time (start_time)
);

-- Device capabilities: store information about the wireless interface
CREATE TABLE IF NOT EXISTS device_capabilities (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    interface TEXT NOT NULL UNIQUE,
    supports_monitor_mode BOOLEAN DEFAULT 0,
    supports_packet_injection BOOLEAN DEFAULT 0,
    supported_bands TEXT, -- JSON array: ['2.4GHz', '5GHz']
    supported_channels TEXT, -- JSON array of channels
    max_tx_power INTEGER,
    driver TEXT,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Views for common queries

-- View: Networks with their latest handshake status
CREATE VIEW IF NOT EXISTS network_handshake_status AS
SELECT 
    n.*,
    COUNT(h.id) AS handshake_count,
    SUM(CASE WHEN h.status = 'cracked' THEN 1 ELSE 0 END) AS cracked_handshakes,
    SUM(CASE WHEN h.status = 'cracking' THEN 1 ELSE 0 END) AS cracking_handshakes,
    MAX(h.timestamp) AS latest_handshake_time
FROM networks n
LEFT JOIN handshakes h ON n.id = h.network_id
GROUP BY n.id;

-- View: Active scan sessions
CREATE VIEW IF NOT EXISTS active_scan_sessions AS
SELECT * FROM scan_sessions WHERE status = 'active';

-- View: Recent handshakes (last 24 hours)
CREATE VIEW IF NOT EXISTS recent_handshakes AS
SELECT h.*, n.essid, n.bssid
FROM handshakes h
JOIN networks n ON h.network_id = n.id
WHERE h.timestamp >= datetime('now', '-1 day');

-- Triggers to automatically update timestamps

-- Update networks.last_seen when a network is updated
CREATE TRIGGER IF NOT EXISTS update_networks_timestamp
AFTER UPDATE ON networks
FOR EACH ROW
BEGIN
    UPDATE networks SET last_seen = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

-- Update handshakes timestamps on status change
CREATE TRIGGER IF NOT EXISTS update_handshake_status_timestamp
AFTER UPDATE OF status ON handshakes
FOR EACH ROW
BEGIN
    UPDATE handshakes SET 
        status = NEW.status,
        crack_end_time = CASE 
            WHEN NEW.status IN ('cracked', 'failed') THEN CURRENT_TIMESTAMP 
            ELSE crack_end_time 
        END
    WHERE id = NEW.id;
END;