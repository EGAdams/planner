
import * as path from 'path';
import { AgentDiscoveryService } from './services/agentDiscovery';

async function runDebug() {
    const service = new AgentDiscoveryService();

    // mimic the paths used in server.ts
    // Note: In the compiled JS, __dirname is .../dashboard/backend/dist
    // In this TS script (if run via ts-node from dashboard/), we need to be careful.
    // Let's assume we run this from dashboard/ directory.

    const workspaceRoot = path.resolve(__dirname, '../..'); // Assuming this file is in dashboard/backend/
    const ottomatorRoot = path.resolve(workspaceRoot, '../ottomator-agents');

    console.log('Debug: Workspace Root:', workspaceRoot);
    console.log('Debug: Ottomator Root:', ottomatorRoot);

    console.log('--- Starting Discovery ---');
    const agents = await service.discover([workspaceRoot, ottomatorRoot]);
    console.log('--- Discovery Complete ---');

    console.log('Found Agents:', Object.keys(agents).length);
    console.log(JSON.stringify(agents, null, 2));
}

runDebug().catch(console.error);
