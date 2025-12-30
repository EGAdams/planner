/**
 * ServerController Web Component
 * Responsibility: Control individual server start/stop operations
 */
export declare class ServerController extends HTMLElement {
    private apiUrl;
    private serverId;
    private server;
    private isLoading;
    private unsubscribe;
    static get observedAttributes(): string[];
    constructor();
    connectedCallback(): void;
    disconnectedCallback(): void;
    attributeChangedCallback(name: string, oldValue: string, newValue: string): void;
    private setupEventListeners;
    private toggleServer;
    private forceKill;
    private render;
}
//# sourceMappingURL=server-controller.d.ts.map