/**
 * Agent Discovery Service
 * Responsibility: Scan directories for agent.json files and register them as managed agents.
 */

import * as fs from 'fs/promises';
import * as path from 'path';
import { ServerConfig } from './serverOrchestrator';

interface AgentMetadata {
    name: string;
    description?: string;
    version?: string;
    // Add other A2A fields as needed
}

export class AgentDiscoveryService {
    private discoveredAgents: Map<string, ServerConfig> = new Map();

    /**
     * Discover agents in the given root directories
     */
    async discover(rootPaths: string[]): Promise<Record<string, ServerConfig>> {
        this.discoveredAgents.clear();

        for (const rootPath of rootPaths) {
            try {
                const absolutePath = path.resolve(rootPath);
                await this.scanDirectory(absolutePath);
            } catch (error) {
                console.error(`Failed to scan directory ${rootPath}:`, error);
            }
        }

        return Object.fromEntries(this.discoveredAgents);
    }

    /**
     * Recursively scan directory for agent.json
     */
    private async scanDirectory(dir: string, depth: number = 0): Promise<void> {
        // Limit recursion depth to avoid performance issues or infinite loops
        if (depth > 5) return;

        try {
            const entries = await fs.readdir(dir, { withFileTypes: true });

            for (const entry of entries) {
                const fullPath = path.join(dir, entry.name);

                if (entry.isDirectory()) {
                    // Skip node_modules, .git, etc.
                    if (entry.name.startsWith('.') || entry.name === 'node_modules' || entry.name === 'dist') {
                        continue;
                    }
                    await this.scanDirectory(fullPath, depth + 1);
                } else if (entry.name === 'agent.json') {
                    await this.processAgentConfig(dir, fullPath);
                }
            }
        } catch (error) {
            // Ignore access errors, etc.
            // console.warn(`Error scanning ${dir}:`, error);
        }
    }

    /**
     * Process an agent.json file and create a ServerConfig
     */
    private async processAgentConfig(dir: string, configPath: string): Promise<void> {
        try {
            const content = await fs.readFile(configPath, 'utf-8');
            const metadata: AgentMetadata = JSON.parse(content);

            // Use directory name as ID if name is missing, or sanitize the name
            const id = metadata.name ? metadata.name.toLowerCase().replace(/\s+/g, '-') : path.basename(dir);

            // Infer command
            const command = await this.inferCommand(dir);

            if (command) {
                const config: ServerConfig = {
                    name: metadata.name || id,
                    command: command,
                    cwd: dir,
                    color: this.generateColor(id),
                    ports: [], // Agents might not have ports, or we'd need to parse them from somewhere else
                    type: 'agent'
                };

                this.discoveredAgents.set(id, config);
                console.log(`Discovered agent: ${id} in ${dir}`);
            } else {
                console.warn(`Could not infer run command for agent in ${dir}`);
            }

        } catch (error) {
            console.error(`Failed to process agent config at ${configPath}:`, error);
        }
    }

    /**
     * Infer the run command for an agent based on file structure
     */
    private async inferCommand(dir: string): Promise<string | null> {
        try {
            const files = await fs.readdir(dir);

            // Python Agent
            if (files.includes('main.py')) {
                // Check for virtualenv
                const venvPath = path.join(dir, '.venv');
                const hasVenv = await this.fileExists(venvPath);

                if (hasVenv) {
                    return `${path.join(dir, '.venv/bin/python')} main.py`;
                } else {
                    // Fallback to system python or a shared venv if we knew where it was
                    // For now, assume 'python3' is available or use the workspace venv
                    return `/home/adamsl/planner/.venv/bin/python main.py`;
                }
            }

            // Node.js Agent
            if (files.includes('package.json')) {
                const pkgContent = await fs.readFile(path.join(dir, 'package.json'), 'utf-8');
                const pkg = JSON.parse(pkgContent);

                if (pkg.scripts && pkg.scripts.start) {
                    return `npm start`;
                }
                if (files.includes('index.js')) {
                    return `node index.js`;
                }
                if (files.includes('main.js')) {
                    return `node main.js`;
                }
                if (files.includes('dist/index.js')) {
                    return `node dist/index.js`;
                }
            }

            return null;
        } catch (error) {
            return null;
        }
    }

    private async fileExists(path: string): Promise<boolean> {
        try {
            await fs.access(path);
            return true;
        } catch {
            return false;
        }
    }

    /**
     * Generate a consistent pastel color from a string
     */
    private generateColor(str: string): string {
        let hash = 0;
        for (let i = 0; i < str.length; i++) {
            hash = str.charCodeAt(i) + ((hash << 5) - hash);
        }

        // Generate pastel color
        const h = Math.abs(hash) % 360;
        return `hsl(${h}, 70%, 90%)`;
    }
}
