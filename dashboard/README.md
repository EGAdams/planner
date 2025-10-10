# Admin Dashboard

A TypeScript-based administrative dashboard for managing servers and monitoring system processes.

## Features

- **Real-time Port Monitoring**: View all listening ports and their associated processes
- **Process Management**: Kill processes that are hogging ports
- **Server Control**: Start and stop registered servers
- **Live Updates**: SSE-based real-time updates without page refresh
- **Responsive UI**: Tailwind CSS-styled components

## Architecture

The dashboard follows Single Responsibility Principle with clean separation of concerns:

**Core Modules (ES Module Singletons):**
- `event-bus/event-bus.ts`: Pure pub/sub event bus for component communication
- `event-bus/sse-manager.ts`: Server-Sent Events connection manager

**Web Components:**
- `port-monitor`: Display listening ports and processes
- `process-killer`: Handle process termination with notifications
- `server-controller`: Individual server start/stop controls
- `server-list`: Display all registered servers

**Backend:**
- `backend/server.ts`: Node.js HTTP server with SSE endpoint

> **Note:** The EventBus uses modern ES Module singleton pattern (not HTMLElement) following industry best practices. See `REFACTORING_NOTES.md` for details.

## Setup

### 1. Install Dependencies

```bash
cd dashboard
npm install
```

### 2. Configure Environment

```bash
cp .env.example .env
```

Edit `.env` and set:
- `SUDO_PASSWORD`: Your sudo password for killing privileged processes
- `ADMIN_PORT`: Port for the dashboard (default: 3030)

### 3. Register Your Servers

Edit `backend/server.ts` and add your servers to `SERVER_REGISTRY`:

```typescript
const SERVER_REGISTRY: Record<string, ServerConfig> = {
  'my-api': {
    name: 'My API Server',
    command: 'npm run dev',
    cwd: '/home/adamsl/my-project',
  },
  // Add more servers here...
};
```

### 4. Build the Project

```bash
npm run build
```

This will:
- Compile TypeScript components
- Compile backend server
- Build Tailwind CSS

### 5. Start the Dashboard

```bash
npm start
```

Access the dashboard at `http://localhost:3030`

## Development

### Watch Mode

For CSS changes:
```bash
npm run dev:css
```

For TypeScript changes, rebuild after changes:
```bash
npm run build:components
npm run build:backend
```

### Adding a New Component

1. Create a new directory: `dashboard/my-component/`
2. Create `my-component.ts` with a web component class
3. Update `tsconfig.json` to include the new directory
4. Import in `public/index.html`

## Windows Startup

To configure the dashboard to start automatically on Windows boot, see `setup-windows-startup.md`.

## Project Structure

```
dashboard/
├── backend/              # Node.js API server
│   ├── server.ts        # Main server file
│   └── dist/            # Compiled backend (generated)
├── event-bus/           # Event bus component
├── port-monitor/        # Port monitoring component
├── process-killer/      # Process management component
├── server-controller/   # Server control component
├── server-list/         # Server list component
├── public/              # Static files
│   ├── index.html      # Main HTML file
│   ├── styles/         # CSS files
│   └── dist/           # Compiled components (generated)
├── main.ts             # Main app entry point
├── package.json        # NPM configuration
├── tsconfig.json       # TypeScript config for components
└── tsconfig.backend.json # TypeScript config for backend
```

## API Endpoints

- `GET /api/ports` - List all listening ports
- `GET /api/servers` - List all registered servers
- `POST /api/servers/:id?action=start|stop` - Start/stop a server
- `DELETE /api/kill` - Kill a process by PID or port
- `GET /api/events` - SSE endpoint for real-time updates

## Security Notes

- The `.env` file contains sensitive information (sudo password). Never commit it to git.
- The dashboard uses sudo for killing privileged processes. Use with caution.
- Consider restricting access to localhost only in production environments.

## Troubleshooting

### Dashboard won't start
- Check that port 3030 is available
- Verify Node.js is installed in WSL
- Check logs at `/tmp/admin-dashboard.log`

### Can't kill processes
- Verify `SUDO_PASSWORD` is set correctly in `.env`
- Check that your user has sudo privileges
- Some system processes cannot be killed

### Components not loading
- Ensure `npm run build` completed successfully
- Check browser console for errors
- Verify all component files exist in `public/dist/`
