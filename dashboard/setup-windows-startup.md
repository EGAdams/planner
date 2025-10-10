# Windows Startup Configuration

This guide explains how to configure the Admin Dashboard to start automatically when Windows boots.

## Method 1: Task Scheduler (Recommended)

### Step 1: Create a Task
1. Press `Win + R` and type `taskschd.msc`, then press Enter
2. Click "Create Task" (not "Create Basic Task")

### Step 2: General Tab
- Name: `Admin Dashboard Server`
- Description: `Automatically starts the admin dashboard server`
- Check "Run whether user is logged on or not"
- Check "Run with highest privileges"
- Configure for: Windows 10

### Step 3: Triggers Tab
1. Click "New..."
2. Begin the task: "At startup"
3. Delay task for: 30 seconds (optional, gives system time to initialize)
4. Click "OK"

### Step 4: Actions Tab
1. Click "New..."
2. Action: "Start a program"
3. Program/script: `powershell.exe`
4. Add arguments: `-WindowStyle Hidden -ExecutionPolicy Bypass -File "C:\path\to\dashboard\start-dashboard.ps1"`
   (Replace `C:\path\to\dashboard` with the actual Windows path to your dashboard folder)
5. Click "OK"

### Step 5: Conditions Tab
- Uncheck "Start the task only if the computer is on AC power"
- Check "Wake the computer to run this task" (optional)

### Step 6: Settings Tab
- Check "Allow task to be run on demand"
- Check "Run task as soon as possible after a scheduled start is missed"
- If the task fails, restart every: 1 minute
- Attempt to restart up to: 3 times

### Step 7: Save
1. Click "OK"
2. Enter your Windows password if prompted
3. The task is now created and will run at startup

## Method 2: Startup Folder (Simpler but less reliable)

1. Press `Win + R` and type `shell:startup`, then press Enter
2. Create a shortcut to `start-dashboard.bat` or `start-dashboard.ps1` in this folder
3. The dashboard will start when you log in

## Verifying It Works

1. Restart your computer
2. Wait about 30 seconds after Windows starts
3. Open a browser and navigate to `http://localhost:3030`
4. You should see the Admin Dashboard

## Checking Logs

If the dashboard doesn't start:
1. Open WSL terminal
2. Run: `cat /tmp/admin-dashboard.log`
3. Check for any error messages

## Stopping the Dashboard

To stop the dashboard server:
```bash
# In WSL terminal
ps aux | grep "node backend/dist/server.js"
kill <PID>
```

Or use the Task Scheduler to disable/stop the task.
