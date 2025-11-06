# WSL2 Auto-Start Guide for Server Monitor Dashboard

## 🎯 Better Approach for WSL2

This guide provides a **WSL2-optimized solution** that's more reliable than systemd services in WSL2 environments.

## 📁 Files Created

1. **`start-dashboard.sh`** - Linux bash script that starts both services
2. **`start-dashboard.bat`** - Windows batch file for startup automation

## 🚀 Quick Setup (3 Steps)

### Step 1: Test the Script Manually

```bash
# From WSL2 terminal
cd /home/adamsl/planner
./start-dashboard.sh
```

Check the log:
```bash
cat /home/adamsl/planner/dashboard-startup.log
```

Verify services are running:
```bash
lsof -i :3030  # Admin Dashboard Backend
lsof -i :3000  # Server Monitor App
```

### Step 2: Add to Windows Startup (Option A - Recommended)

**For automatic startup when Windows boots:**

1. **Copy the batch file to Windows:**
   ```bash
   # From WSL2, copy to Windows clipboard
   cat /home/adamsl/planner/start-dashboard.bat
   ```

2. **Create batch file in Windows:**
   - Press `Win + R`, type `shell:startup`, press Enter
   - Right-click → New → Text Document
   - Name it `StartDashboard.bat`
   - Paste the content from clipboard
   - Save and close

3. **Test it:**
   - Double-click `StartDashboard.bat` in the Startup folder
   - Browser should open to http://localhost:3000 after ~10 seconds

### Step 2: Add to WSL2 Profile (Option B - Alternative)

**For automatic startup when opening WSL2 terminal:**

Add to your `~/.bashrc`:
```bash
echo "" >> ~/.bashrc
echo "# Auto-start Dashboard on WSL2 startup" >> ~/.bashrc
echo "/home/adamsl/planner/start-dashboard.sh" >> ~/.bashrc
```

## 🛠️ Manual Control Commands

### Start Services
```bash
/home/adamsl/planner/start-dashboard.sh
```

### Stop Services
```bash
# Kill by port
kill $(lsof -t -i:3030)  # Stop Admin Dashboard Backend
kill $(lsof -t -i:3000)  # Stop Server Monitor App
```

### Check Status
```bash
# Check if running
lsof -i :3030 && echo "✓ Backend running" || echo "✗ Backend stopped"
lsof -i :3000 && echo "✓ Frontend running" || echo "✗ Frontend stopped"

# View logs
tail -f /home/adamsl/planner/dashboard-startup.log
```

### Restart Services
```bash
# Stop both
kill $(lsof -t -i:3030) 2>/dev/null
kill $(lsof -t -i:3000) 2>/dev/null

# Wait 2 seconds
sleep 2

# Start again
/home/adamsl/planner/start-dashboard.sh
```

## 🔧 Advanced: Using systemd in WSL2 (Optional)

If you still want to use systemd (from your original guide), you can, but note:

**Limitations:**
- systemd in WSL2 doesn't auto-start on Windows boot
- Requires WSL2 to be configured with systemd support
- Less reliable than the script approach above

**If you still want systemd**, follow the original `automate_startup.md` guide, but add this to start systemd services on WSL2 launch:

```bash
# Add to ~/.bashrc
if ! systemctl is-active --quiet admin-dashboard.service; then
    sudo systemctl start admin-dashboard.service
fi

if ! systemctl is-active --quiet server-monitor-app.service; then
    sudo systemctl start server-monitor-app.service
fi
```

## 📊 Comparison: Script vs systemd

| Feature | Bash Script | systemd |
|---------|-------------|---------|
| WSL2 Compatibility | ✓✓✓ Excellent | ✓✓ Good |
| Windows Startup Integration | ✓✓✓ Native | ✓ Requires workaround |
| Setup Complexity | ✓✓✓ Simple | ✓ Complex |
| Service Management | ✓✓ Manual | ✓✓✓ Full featured |
| Auto-restart on Crash | ✗ No | ✓✓✓ Yes |

**Recommendation**: Use the **Bash Script approach** for simplicity and reliability in WSL2.

## 🎯 Next Steps

1. Test the script: `./start-dashboard.sh`
2. Add to Windows Startup folder (Option A above)
3. Restart Windows to verify auto-start works
4. Bookmark http://localhost:3000 in your browser

## 🐛 Troubleshooting

**Services don't start:**
- Check logs: `cat dashboard-startup.log`
- Verify npm is installed: `npm --version`
- Check port conflicts: `lsof -i :3000 -i :3030`

**Windows batch file doesn't work:**
- Verify WSL distribution name: `wsl -l -v` (from Windows cmd)
- Update batch file if distribution name isn't "Ubuntu"
- Run batch file manually first to test

**Browser doesn't open automatically:**
- Services may need more time to start
- Increase timeout in batch file: `timeout /t 20 /nobreak`

---

**You now have a robust, WSL2-optimized auto-start solution! 🚀**
