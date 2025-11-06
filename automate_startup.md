# Automating Server Monitor Dashboard Startup

This document outlines the steps to automatically start the Server Monitor Dashboard and its dependencies when the system boots up. This ensures that the monitoring page is always available in your browser upon startup.

## Overview of Services to Start

We need to start two main services:

1.  **Admin Dashboard Backend**: This is the core backend service that monitors other servers, manages processes, and provides API endpoints.
    *   **Location**: `/home/adamsl/planner/dashboard`
    *   **Start Command**: `npm start`
    *   **Port**: `3030`

2.  **Server Monitor App (Frontend & Proxy)**: This is the web application that you interact with in your browser. It serves the HTML/CSS/JS and proxies requests to the Admin Dashboard Backend.
    *   **Location**: `/home/adamsl/planner/server-monitor-app`
    *   **Start Command**: `npm start`
    *   **Port**: `3000`

## Creating a Startup Script (Linux/systemd)

For Linux systems, `systemd` is the standard way to manage services. We will create two `systemd` service files.

### Step 1: Create Admin Dashboard Service File

Create a new file named `admin-dashboard.service` in `/etc/systemd/system/`:

```bash
sudo nano /etc/systemd/system/admin-dashboard.service
```

Add the following content to the file:

```ini
[Unit]
Description=Admin Dashboard Backend Service
After=network.target

[Service]
ExecStart=/usr/bin/npm start
WorkingDirectory=/home/adamsl/planner/dashboard
StandardOutput=inherit
StandardError=inherit
Restart=always
User=adamsl  # Replace with your username
Environment=PATH=/usr/bin:/usr/local/bin:/usr/bin/npm # Adjust PATH if npm is not found

[Install]
WantedBy=multi-user.target
```

**Important**: Replace `adamsl` with your actual username.

### Step 2: Create Server Monitor App Service File

Create a new file named `server-monitor-app.service` in `/etc/systemd/system/`:

```bash
sudo nano /etc/systemd/system/server-monitor-app.service
```

Add the following content to the file:

```ini
[Unit]
Description=Server Monitor Frontend App
After=network.target admin-dashboard.service # Ensure dashboard backend starts first

[Service]
ExecStart=/usr/bin/npm start
WorkingDirectory=/home/adamsl/planner/server-monitor-app
StandardOutput=inherit
StandardError=inherit
Restart=always
User=adamsl # Replace with your username
Environment=PATH=/usr/bin:/usr/local/bin:/usr/bin/npm # Adjust PATH if npm is not found

[Install]
WantedBy=multi-user.target
```

**Important**: Replace `adamsl` with your actual username.

### Step 3: Reload systemd and Enable Services

After creating the service files, you need to reload `systemd` to recognize the new services and then enable them to start on boot:

```bash
sudo systemctl daemon-reload
sudo systemctl enable admin-dashboard.service
sudo systemctl enable server-monitor-app.service
```

### Step 4: Start the Services (and Test)

You can start the services immediately without rebooting to test them:

```bash
sudo systemctl start admin-dashboard.service
sudo systemctl start server-monitor-app.service
```

To check their status:

```bash
sudo systemctl status admin-dashboard.service
sudo systemctl status server-monitor-app.service
```

### Step 5: Configure Browser to Open on Startup (Optional)

Most desktop environments allow you to configure applications to launch on startup. You can add your preferred web browser to open `http://localhost:3000` automatically.

**Example (GNOME):**
1.  Open "Startup Applications" (search in activities).
2.  Click "Add".
3.  **Name**: Server Monitor Dashboard
4.  **Command**: `firefox http://localhost:3000` (or `google-chrome`, `chromium`, etc.)
5.  **Comment**: Automatically open server monitoring page.

## Troubleshooting

*   **Services not starting**: Check the logs using `journalctl -u admin-dashboard.service` or `journalctl -u server-monitor-app.service`.
*   **`npm` not found**: Ensure `npm` is in the `PATH` specified in the service file. You might need to find the full path to your `npm` executable (e.g., `which npm`).
*   **Permissions**: Ensure the `User` in the service file has the necessary permissions to run `npm start` in the specified directories.

This setup will ensure your server monitoring dashboard is ready to go every time you start your PC!