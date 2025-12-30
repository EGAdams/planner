#!/bin/bash
# Quick fix for WSL/Windows network connectivity issues
# This script updates service bindings to allow Windows browser access

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
CORS_PROXY_FILE="$SCRIPT_DIR/cors_proxy_server.py"
BACKUP_FILE="$CORS_PROXY_FILE.backup"

echo "=========================================================================="
echo "WSL/Windows Network Connectivity Fix"
echo "=========================================================================="
echo ""

# Step 1: Backup CORS proxy script
echo "1. Creating backup of CORS proxy script..."
cp "$CORS_PROXY_FILE" "$BACKUP_FILE"
echo "   ✅ Backup created: $BACKUP_FILE"
echo ""

# Step 2: Update CORS proxy binding
echo "2. Updating CORS proxy to bind to 0.0.0.0..."
sed -i "s/server = http.server.HTTPServer(('localhost', 9000)/server = http.server.HTTPServer(('0.0.0.0', 9000)/" "$CORS_PROXY_FILE"
echo "   ✅ Updated line 297: localhost → 0.0.0.0"
echo ""

# Step 3: Show the change
echo "3. Verifying change..."
grep -n "HTTPServer.*9000" "$CORS_PROXY_FILE" || echo "   ⚠️  Could not find changed line"
echo ""

# Step 4: Kill existing services
echo "4. Stopping existing services..."
pkill -f cors_proxy_server.py || echo "   (CORS proxy not running)"
pkill -f "letta server" || echo "   (Letta server not running)"
echo "   ✅ Services stopped"
echo ""

# Step 5: Restart services
echo "5. Starting services with new configuration..."
echo "   Starting CORS proxy on 0.0.0.0:9000..."
cd "$SCRIPT_DIR"
python3 cors_proxy_server.py > /tmp/cors_proxy.log 2>&1 &
CORS_PID=$!
echo "   ✅ CORS proxy started (PID: $CORS_PID)"

sleep 2

echo "   Starting Letta server on 0.0.0.0:8283..."
letta server --host 0.0.0.0 --port 8283 > /tmp/letta_server.log 2>&1 &
LETTA_PID=$!
echo "   ✅ Letta server started (PID: $LETTA_PID)"
echo ""

# Step 6: Wait for services to start
echo "6. Waiting for services to initialize..."
sleep 5
echo ""

# Step 7: Verify services are listening
echo "7. Verifying service bindings..."
echo ""
netstat -tuln | grep -E "(9000|8283|7880)" | while read line; do
    echo "   $line"
done
echo ""

# Step 8: Test connectivity
echo "8. Testing connectivity..."
WSL_IP=$(hostname -I | awk '{print $1}')
echo "   WSL IP: $WSL_IP"
echo ""

# Test CORS proxy on WSL IP
echo "   Testing CORS proxy on WSL IP..."
if curl -s -o /dev/null -w "%{http_code}" "http://$WSL_IP:9000" | grep -q "200"; then
    echo "   ✅ CORS proxy accessible from Windows at http://$WSL_IP:9000"
else
    echo "   ❌ CORS proxy NOT accessible (may need Windows Firewall rules)"
fi

# Test Letta server on WSL IP
echo "   Testing Letta server on WSL IP..."
if curl -s -o /dev/null -w "%{http_code}" "http://$WSL_IP:8283/v1/health" | grep -q "200"; then
    echo "   ✅ Letta server accessible from Windows at http://$WSL_IP:8283"
else
    echo "   ⚠️  Letta server NOT accessible yet (may still be starting)"
fi

# Test LiveKit server
echo "   Testing LiveKit server on WSL IP..."
if curl -s -o /dev/null -w "%{http_code}" "http://$WSL_IP:7880" 2>&1 | grep -qE "(200|404)"; then
    echo "   ✅ LiveKit server accessible from Windows at ws://$WSL_IP:7880"
else
    echo "   ⚠️  LiveKit server not responding"
fi

echo ""
echo "=========================================================================="
echo "Fix Complete!"
echo "=========================================================================="
echo ""
echo "Next Steps:"
echo "1. Open Windows browser"
echo "2. Navigate to: http://$WSL_IP:9000/debug"
echo "3. Click 'Connect' and verify all LEDs turn green"
echo ""
echo "If services are still unreachable, you may need to configure Windows Firewall:"
echo ""
echo "  Run in PowerShell (as Administrator):"
echo "  New-NetFirewallRule -DisplayName \"WSL - CORS Proxy\" -Direction Inbound -LocalPort 9000 -Protocol TCP -Action Allow"
echo "  New-NetFirewallRule -DisplayName \"WSL - Letta Server\" -Direction Inbound -LocalPort 8283 -Protocol TCP -Action Allow"
echo ""
echo "Logs:"
echo "  CORS Proxy: /tmp/cors_proxy.log"
echo "  Letta Server: /tmp/letta_server.log"
echo ""
echo "To revert changes:"
echo "  cp $BACKUP_FILE $CORS_PROXY_FILE"
echo "=========================================================================="
