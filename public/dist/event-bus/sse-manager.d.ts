/**yyy
 * SSEManager Module
 * Responsibility: Manage Server-Sent Events connection and emit events to EventBus
 */
export declare class SSEManager {
    private eventSource;
    private apiUrl;
    private reconnectTimeout;
    private reconnectTimer;
    constructor(apiUrl?: string);
    /**
     * Connect to the SSE endpoint
     */
    connect(): void;
    /**
     * Disconnect from the SSE endpoint
     */
    disconnect(): void;
    /**
     * Schedule a reconnection attempt
     */
    private scheduleReconnect;
    /**
     * Check if connected
     */
    isConnected(): boolean;
    /**
     * Set reconnect timeout
     */
    setReconnectTimeout(timeout: number): void;
}
export declare const sseManager: SSEManager;
//# sourceMappingURL=sse-manager.d.ts.map