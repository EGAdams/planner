/**
 * PortMonitor Web Component
 * Responsibility: Display all listening ports and associated processes
 */
export declare class PortMonitor extends HTMLElement {
    private processes;
    private unsubscribe;
    constructor();
    connectedCallback(): void;
    disconnectedCallback(): void;
    private setupEventListeners;
    private emitKillRequest;
    private render;
}
//# sourceMappingURL=port-monitor.d.ts.map