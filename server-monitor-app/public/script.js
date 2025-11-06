const serverListElement = document.getElementById('server-list');
const portListElement = document.getElementById('port-list');
const connectionStatusElement = document.getElementById('connection-status');

console.log('[INIT] DOM Elements:', { serverListElement, portListElement, connectionStatusElement });

const eventSource = new EventSource('/api/events');
console.log('[INIT] EventSource created');

eventSource.onopen = () => {
    showConnectionStatus('Connected', 'success');
};

eventSource.onerror = (err) => {
    console.error('EventSource failed:', err);
    showConnectionStatus('Disconnected', 'error');
    eventSource.close();
};

eventSource.addEventListener('ports', (event) => {
    console.log('[EVENT] Received ports event');
    const ports = JSON.parse(event.data);
    console.log('[EVENT] Parsed ports:', ports);
    renderPorts(ports);
});

eventSource.addEventListener('servers', (event) => {
    console.log('[EVENT] Received servers event');
    const servers = JSON.parse(event.data);
    console.log('[EVENT] Parsed servers:', servers);
    renderServers(servers);
});

function showConnectionStatus(message, type) {
    if (!connectionStatusElement) return;

    connectionStatusElement.textContent = message;
    connectionStatusElement.className = 'fixed top-4 right-4 px-4 py-2 rounded-md shadow-lg text-sm font-medium';

    if (type === 'success') {
        connectionStatusElement.classList.add('bg-green-500', 'text-white');
        connectionStatusElement.classList.remove('bg-red-500');
    } else {
        connectionStatusElement.classList.add('bg-red-500', 'text-white');
        connectionStatusElement.classList.remove('bg-green-500');
    }

    connectionStatusElement.classList.remove('hidden');

    if (type === 'success') {
        setTimeout(() => {
            connectionStatusElement.classList.add('hidden');
        }, 3000);
    }
}

async function renderServers(servers) {
    console.log('[RENDER] renderServers called with:', servers);
    console.log('[RENDER] serverListElement:', serverListElement);

    if (!serverListElement) {
        console.error('[ERROR] serverListElement is null!');
        return;
    }

    serverListElement.innerHTML = '';
    for (const serverId in servers) {
        const server = servers[serverId];
        console.log(`[RENDER] Processing server: ${serverId}`, server);

        const isRunning = server.running;
        const status = isRunning ? 'running' : 'stopped';
        const statusColor = isRunning ? 'text-green-600' : 'text-red-600';

        const serverCard = document.createElement('div');
        serverCard.className = 'bg-white p-4 rounded-lg shadow-md border-l-4';
        serverCard.style.borderLeftColor = server.color || '#ccc';
        serverCard.innerHTML = `
            <h3 class="text-lg font-semibold">${server.name}</h3>
            <p>Status: <span class="font-medium ${statusColor}">${status}</span></p>
            <p>PID: ${server.orphanedPid || 'N/A'}</p>
            <p>Orphaned: ${server.orphaned ? 'Yes' : 'No'}</p>
            <p>Healthy: ${server.healthy !== undefined ? (server.healthy ? 'Yes' : 'No') : 'Unknown'}</p>
            <div class="mt-4 space-x-2">
                <button data-id="${serverId}" data-action="start" class="bg-green-500 text-white px-3 py-1 rounded hover:bg-green-600 disabled:opacity-50" ${isRunning ? 'disabled' : ''}>Start</button>
                <button data-id="${serverId}" data-action="stop" class="bg-red-500 text-white px-3 py-1 rounded hover:bg-red-600 disabled:opacity-50" ${!isRunning ? 'disabled' : ''}>Stop</button>
            </div>
        `;
        serverListElement.appendChild(serverCard);
    }

    serverListElement.querySelectorAll('button').forEach(button => {
        button.onclick = handleServerAction;
    });
}

async function renderPorts(ports) {
    portListElement.innerHTML = '';
    if (ports.length === 0) {
        portListElement.innerHTML = '<p>No listening ports found.</p>';
        return;
    }

    ports.forEach(port => {
        const portCard = document.createElement('div');
        portCard.className = 'bg-white p-4 rounded-lg shadow-md border-l-4';
        if (port.color) {
            portCard.style.borderLeftColor = port.color;
        }
        portCard.innerHTML = `
            <h3 class="text-lg font-semibold">Port: ${port.port}</h3>
            <p>PID: ${port.pid}</p>
            <p>Program: ${port.program}</p>
            <p>Command: ${port.command}</p>
            ${port.serverId ? `<p>Server: ${port.serverId}</p>` : ''}
            <div class="mt-4">
                <button data-pid="${port.pid}" class="bg-red-500 text-white px-3 py-1 rounded hover:bg-red-600">Kill Process</button>
            </div>
        `;
        portListElement.appendChild(portCard);
    });

    portListElement.querySelectorAll('button').forEach(button => {
        button.onclick = handleKillProcess;
    });
}

async function handleServerAction(event) {
    const button = event.target;
    const serverId = button.dataset.id;
    const action = button.dataset.action;

    try {
        const response = await fetch(`/api/servers/${serverId}?action=${action}`, {
            method: 'POST',
        });
        const result = await response.json();
        if (result.success) {
            showConnectionStatus(`${serverId} ${action}ed successfully!`, 'success');
        } else {
            showConnectionStatus(`Failed to ${action} ${serverId}: ${result.message}`, 'error');
        }
    } catch (error) {
        console.error('Error performing server action:', error);
        showConnectionStatus(`Error performing ${action} on ${serverId}`, 'error');
    }
}

async function handleKillProcess(event) {
    const button = event.target;
    const pid = button.dataset.pid;

    if (!confirm(`Are you sure you want to kill process ${pid}?`)) {
        return;
    }

    try {
        const response = await fetch('/api/kill', {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ pid }),
        });
        const result = await response.json();
        if (result.success) {
            showConnectionStatus(`Process ${pid} killed successfully!`, 'success');
        } else {
            showConnectionStatus(`Failed to kill process ${pid}: ${result.message}`, 'error');
        }
    } catch (error) {
        console.error('Error killing process:', error);
        showConnectionStatus(`Error killing process ${pid}`, 'error');
    }
}
