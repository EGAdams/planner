/**
 * ProcessKiller Web Component
 * Responsibility: Handle process termination requests and display status
 */
export declare class ProcessKiller extends HTMLElement {
    private apiUrl;
    private isKilling;
    private lastMessage;
    private lastMessageType;
    private unsubscribe;
    constructor();
    connectedCallback(): void;
    disconnectedCallback(): void;
    private setupEventListeners;
    private killProcess;
    private render;
}
//# sourceMappingURL=process-killer.d.ts.map