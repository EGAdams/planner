/**
 * ServerList Web Component
 * Responsibility: Display list of registered servers with their status
 */
export declare class ServerList extends HTMLElement {
    private servers;
    private unsubscribe;
    constructor();
    connectedCallback(): void;
    disconnectedCallback(): void;
    private setupEventListeners;
    private normalizeServerData;
    private render;
}
//# sourceMappingURL=server-list.d.ts.map