# Systemd Auto-Start Setup (Optional)

This guide shows how to configure services to start automatically on boot using systemd.

## Service Files

### 1. LiveKit Server Service

Create `/etc/systemd/system/livekit.service`:

```ini
[Unit]
Description=LiveKit Server (Dev Mode)
After=network.target

[Service]
Type=simple
User=adamsl
WorkingDirectory=/home/adamsl/ottomator-agents/livekit-agent
ExecStart=/home/adamsl/ottomator-agents/livekit-agent/livekit-server --dev --bind 0.0.0.0
Restart=on-failure
RestartSec=5s
StandardOutput=append:/tmp/livekit.log
StandardError=append:/tmp/livekit.log

[Install]
WantedBy=multi-user.target
```

### 2. Letta Server Service

Create `/etc/systemd/system/letta-server.service`:

```ini
[Unit]
Description=Letta Server with PostgreSQL Backend
After=network.target postgresql.service
Requires=postgresql.service

[Service]
Type=simple
User=adamsl
WorkingDirectory=/home/adamsl/planner/a2a_communicating_agents/hybrid_letta_agents
Environment="PATH=/home/adamsl/planner/.venv/bin:/usr/bin:/bin"
Environment="LETTA_PG_URI=postgresql+pg8000://letta:letta@localhost:5432/letta"
EnvironmentFile=/home/adamsl/.env
ExecStart=/home/adamsl/planner/.venv/bin/letta server
Restart=on-failure
RestartSec=10s
StandardOutput=append:/tmp/letta_server.log
StandardError=append:/tmp/letta_server.log

[Install]
WantedBy=multi-user.target
```

### 3. Voice Agent Service

Create `/etc/systemd/system/letta-voice-agent.service`:

```ini
[Unit]
Description=Letta Voice Agent (LiveKit Integration)
After=network.target livekit.service letta-server.service
Requires=livekit.service letta-server.service

[Service]
Type=simple
User=adamsl
WorkingDirectory=/home/adamsl/planner/a2a_communicating_agents/hybrid_letta_agents
Environment="PATH=/home/adamsl/planner/.venv/bin:/usr/bin:/bin"
EnvironmentFile=/home/adamsl/.env
ExecStart=/home/adamsl/planner/.venv/bin/python letta_voice_agent.py dev
Restart=on-failure
RestartSec=10s
StandardOutput=append:/tmp/voice_agent.log
StandardError=append:/tmp/voice_agent.log

[Install]
WantedBy=multi-user.target
```

### 4. Demo Web Server Service

Create `/etc/systemd/system/letta-demo-server.service`:

```ini
[Unit]
Description=Letta Voice Demo Web Server
After=network.target

[Service]
Type=simple
User=adamsl
WorkingDirectory=/home/adamsl/ottomator-agents/livekit-agent
ExecStart=/usr/bin/python3 -m http.server 8888
Restart=on-failure
RestartSec=5s
StandardOutput=append:/tmp/demo_server.log
StandardError=append:/tmp/demo_server.log

[Install]
WantedBy=multi-user.target
```

## Installation

### Option A: Install All Services (Recommended)

```bash
# Copy service files (requires sudo)
sudo cp systemd/*.service /etc/systemd/system/

# Reload systemd
sudo systemctl daemon-reload

# Enable services to start on boot
sudo systemctl enable livekit.service
sudo systemctl enable letta-server.service
sudo systemctl enable letta-voice-agent.service
sudo systemctl enable letta-demo-server.service

# Start services now
sudo systemctl start livekit.service
sudo systemctl start letta-server.service
sudo systemctl start letta-voice-agent.service
sudo systemctl start letta-demo-server.service
```

### Option B: Just Create the Service Files (Don't Auto-Start)

Create the service files but don't enable auto-start:

```bash
# Copy service files
sudo cp systemd/*.service /etc/systemd/system/
sudo systemctl daemon-reload

# Start manually when needed
sudo systemctl start livekit.service
sudo systemctl start letta-server.service
sudo systemctl start letta-voice-agent.service
sudo systemctl start letta-demo-server.service
```

## Managing Services

```bash
# Check status
sudo systemctl status letta-voice-agent.service

# View logs
sudo journalctl -u letta-voice-agent.service -f

# Restart a service
sudo systemctl restart letta-voice-agent.service

# Stop a service
sudo systemctl stop letta-voice-agent.service

# Disable auto-start
sudo systemctl disable letta-voice-agent.service
```

## Create .env File

Make sure your environment variables are in `/home/adamsl/.env`:

```bash
cat >> ~/.env << 'EOF'
OPENAI_API_KEY=your_key_here
DEEPGRAM_API_KEY=your_key_here
CARTESIA_API_KEY=your_key_here
LETTA_PG_URI=postgresql+pg8000://letta:letta@localhost:5432/letta
LIVEKIT_URL=ws://localhost:7880
LIVEKIT_API_KEY=devkey
LIVEKIT_API_SECRET=secret
EOF
```

## Verification

After setup, verify all services:

```bash
# Check all services
sudo systemctl status livekit letta-server letta-voice-agent letta-demo-server

# Check ports
ss -tlnp | grep -E ":(8283|7880|8888)"

# Test voice system
# Open http://localhost:8888/test-simple.html
```

---

**Note:** If you don't want auto-start on boot, just use the `start_voice_system.sh` script manually after each reboot.
