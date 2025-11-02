# Web Server Setup Guide

## Quick Start

### 1. Start the Server

```bash
cd /home/adamsl/planner/nonprofit_finance_db
source venv/bin/activate
export NON_PROFIT_PASSWORD=tinman  # Or your MySQL root password
python api_server.py
```

You should see:
```
🚀 Starting Daily Expense Categorizer on http://localhost:8080
   Main App:         http://localhost:8080/
   API Documentation: http://localhost:8080/docs
```

### 2. Access from Windows Browser

**IMPORTANT**: Since you're running in WSL2, you **cannot** use `localhost:8080` from Windows.

#### Get Your WSL2 IP Address

```bash
hostname -I | awk '{print $1}'
```

Example output: `172.30.171.179`

#### Open in Browser

```
http://172.30.171.179:8080
```

Replace `172.30.171.179` with your actual WSL2 IP address.

## Available Endpoints

- **Main App**: `http://[WSL2_IP]:8080/` - Daily Expense Categorizer
- **API Documentation**: `http://[WSL2_IP]:8080/docs` - Swagger/OpenAPI docs
- **Category Picker**: `http://[WSL2_IP]:8080/ui` - Category management
- **Office Assistant**: `http://[WSL2_IP]:8080/office` - Office integration

## Troubleshooting

### "Page is not working" or "Cannot connect"

**Cause**: Trying to access `localhost:8080` from Windows browser

**Solution**: Use WSL2 IP address instead:
```bash
# Get IP in WSL2
hostname -I | awk '{print $1}'

# Use that IP in Windows browser
http://[IP_ADDRESS]:8080
```

### "Error loading data: Failed to fetch"

**Cause**: JavaScript trying to connect to `localhost` API

**Solution**: The frontend should auto-detect the correct API endpoint. If not:
1. Make sure you're accessing via WSL2 IP (not localhost)
2. Check server logs for errors: `tail -f api_server.log`
3. Verify database password is set: `echo $NON_PROFIT_PASSWORD`

### "Access denied for user 'root'@'localhost'"

**Cause**: Database password not set or incorrect

**Solution**:
```bash
# Set password in environment
export NON_PROFIT_PASSWORD=tinman

# Or update .env file
echo "NON_PROFIT_PASSWORD=tinman" >> .env

# Restart server
pkill -f api_server.py
python api_server.py
```

### Server Already Running

**Check if running:**
```bash
ps aux | grep api_server.py | grep -v grep
```

**Kill existing server:**
```bash
pkill -f api_server.py
```

**Restart:**
```bash
python api_server.py
```

### Port 8080 Already in Use

**Find process using port 8080:**
```bash
sudo lsof -i :8080
# or
ss -tlnp | grep :8080
```

**Kill the process:**
```bash
kill -9 [PID]
```

## Making localhost Work (Optional)

If you want to use `localhost:8080` from Windows, set up port forwarding.

### Step 1: Get WSL2 IP

In WSL2 terminal:
```bash
hostname -I | awk '{print $1}'
```
Example: `172.30.171.179`

### Step 2: Add Port Forwarding

In **Windows PowerShell (Administrator)**:
```powershell
netsh interface portproxy add v4tov4 listenport=8080 listenaddress=0.0.0.0 connectport=8080 connectaddress=172.30.171.179
```

Replace `172.30.171.179` with your actual WSL2 IP.

### Step 3: Test

From Windows browser: `http://localhost:8080`

### Managing Port Forwards

**View all forwards:**
```powershell
netsh interface portproxy show all
```

**Remove a forward:**
```powershell
netsh interface portproxy delete v4tov4 listenport=8080 listenaddress=0.0.0.0
```

**Important**: WSL2 IP can change after restarting WSL2. You'll need to:
1. Get new IP: `hostname -I | awk '{print $1}'`
2. Delete old forward
3. Add new forward with updated IP

## Running in Background

### Option 1: nohup

```bash
export NON_PROFIT_PASSWORD=tinman
nohup python api_server.py > api_server.log 2>&1 &
```

View logs:
```bash
tail -f api_server.log
```

### Option 2: tmux/screen

```bash
# Start tmux session
tmux new -s server

# Run server
export NON_PROFIT_PASSWORD=tinman
python api_server.py

# Detach: Ctrl+B, then D
# Reattach: tmux attach -t server
```

## Stopping the Server

### Graceful Stop

```bash
# Find process
ps aux | grep api_server.py | grep -v grep

# Kill by name
pkill -f api_server.py
```

### Force Stop

```bash
pkill -9 -f api_server.py
```

## Server Configuration

### Environment Variables

The server uses these environment variables:

```bash
# Database
DB_HOST=127.0.0.1
DB_PORT=3306
NON_PROFIT_USER=root
NON_PROFIT_PASSWORD=tinman
NON_PROFIT_DB_NAME=nonprofit_finance

# Server (optional)
PORT=8080
HOST=0.0.0.0
```

Set via `.env` file or export before running server.

### File Locations

- **Main Server**: `api_server.py`
- **Server Logs**: `api_server.log`
- **Frontend**: `../category-picker/public/`
- **Office UI**: `../office-assistant/`
- **Configuration**: `.env`

## Features

### Daily Expense Categorizer (Main App)

- View all transactions by month
- Categorize expenses using 115 hierarchical categories
- Track running totals
- Navigate through months
- Real-time updates

### API Documentation

Interactive Swagger UI at: `http://[WSL2_IP]:8080/docs`

Endpoints:
- `GET /api/transactions` - Get all transactions
- `GET /api/categories` - Get category hierarchy
- `PUT /api/transactions/{id}/category` - Update transaction category
- `POST /api/import-pdf` - Import PDF bank statements
- `GET /api/recent-downloads` - View recent imports

## Performance

- **192 transactions** currently in database
- **115 categories** in hierarchy
- **Sub-second response times** for API calls
- **Real-time updates** with server-sent events (SSE)

## Security Notes

- Server binds to `0.0.0.0:8080` (accessible from network)
- CORS enabled for all origins (development only)
- Database password should be kept secure
- Consider firewall rules for production use

## Next Steps

After server is running:
1. Open web interface at `http://[WSL2_IP]:8080`
2. Explore API docs at `http://[WSL2_IP]:8080/docs`
3. Import bank statements via PDF upload
4. Categorize transactions using the UI
5. View reports and summaries

For CLI tools and database views, see [DATA_VIEWING_GUIDE.md](DATA_VIEWING_GUIDE.md)
