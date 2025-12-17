# Voice System Quick Start Guide

## After Reboot - Manual Start

```bash
cd /home/adamsl/planner/a2a_communicating_agents/hybrid_letta_agents
./start_voice_system.sh
```

Then open browser to: **http://localhost:8888/test-simple.html**

## Stop Services

```bash
./stop_voice_system.sh
```

## Check Status

```bash
# Check all services
ps aux | grep -E "letta server|livekit-server|letta_voice|http.server 8888" | grep -v grep

# Check ports
ss -tlnp | grep -E ":(8283|7880|8888)"

# Check Letta health
curl http://localhost:8283/

# Check PostgreSQL
pg_isready
```

## View Logs

```bash
# Voice agent
tail -f /tmp/voice_agent.log

# LiveKit server
tail -f /tmp/livekit.log

# Letta server
tail -f /tmp/letta_server.log

# Demo server
tail -f /tmp/demo_server.log
```

## Troubleshooting

### No audio response
1. Check browser console (F12) for errors
2. Verify all services running: `ps aux | grep -E "letta|livekit|8888"`
3. Check voice agent logs: `tail -100 /tmp/voice_agent.log`
4. Restart services: `./stop_voice_system.sh && ./start_voice_system.sh`

### "Connection failed"
1. Verify LiveKit server: `ss -tlnp | grep 7880`
2. Check LiveKit logs: `tail -50 /tmp/livekit.log`
3. Refresh browser page

### Letta not responding
1. Check Letta server: `curl http://localhost:8283/`
2. Check PostgreSQL: `pg_isready`
3. Restart Letta: `pkill -f "letta server" && cd agents && ./start_letta_postgres.sh`

---

## Optional: Auto-Start on Boot

If you want services to start automatically on boot, see `SYSTEMD_SETUP.md`.
