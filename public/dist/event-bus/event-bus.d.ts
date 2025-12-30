/**
 * EventBus Module
 * Responsibility: Provide global pub/sub event communication between components
 *
 * This is implemented as an ES module singleton - the simplest and most modern approach.
 * ES modules are singletons by default (only executed once), so we can export a single instance.
 */
type EventCallback = (data?: any) => void;
declare class EventBus {
    private subscribers;
    /**
     * Subscribe to an event
     * @param event - Event name to listen for
     * @param callback - Function to call when event is emitted
     * @returns Unsubscribe function
     */
    on(event: string, callback: EventCallback): () => void;
    /**
     * Emit an event with optional data
     * @param event - Event name to emit
     * @param data - Optional data to pass to subscribers
     */
    emit(event: string, data?: any): void;
    /**
     * Unsubscribe from an event
     * @param event - Event name
     * @param callback - Callback to remove
     */
    off(event: string, callback: EventCallback): void;
    /**
     * Subscribe to an event that will only fire once
     * @param event - Event name to listen for
     * @param callback - Function to call when event is emitted
     */
    once(event: string, callback: EventCallback): void;
    /**
     * Clear all subscribers for an event, or all events if no event specified
     * @param event - Optional event name to clear
     */
    clear(event?: string): void;
    /**
     * Get the number of subscribers for an event
     * @param event - Event name
     * @returns Number of subscribers
     */
    listenerCount(event: string): number;
}
export declare const eventBus: EventBus;
export { EventBus };
//# sourceMappingURL=event-bus.d.ts.map