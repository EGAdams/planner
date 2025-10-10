/**
 * EventBus Module
 * Responsibility: Provide global pub/sub event communication between components
 *
 * This is implemented as an ES module singleton - the simplest and most modern approach.
 * ES modules are singletons by default (only executed once), so we can export a single instance.
 */

type EventCallback = (data?: any) => void;

class EventBus {
  private subscribers: Map<string, Set<EventCallback>> = new Map();

  /**
   * Subscribe to an event
   * @param event - Event name to listen for
   * @param callback - Function to call when event is emitted
   * @returns Unsubscribe function
   */
  public on(event: string, callback: EventCallback): () => void {
    if (!this.subscribers.has(event)) {
      this.subscribers.set(event, new Set());
    }

    this.subscribers.get(event)!.add(callback);

    // Return unsubscribe function
    return () => this.off(event, callback);
  }

  /**
   * Emit an event with optional data
   * @param event - Event name to emit
   * @param data - Optional data to pass to subscribers
   */
  public emit(event: string, data?: any): void {
    const callbacks = this.subscribers.get(event);
    if (callbacks) {
      callbacks.forEach(callback => {
        try {
          callback(data);
        } catch (error) {
          console.error(`Error in event handler for "${event}":`, error);
        }
      });
    }
  }

  /**
   * Unsubscribe from an event
   * @param event - Event name
   * @param callback - Callback to remove
   */
  public off(event: string, callback: EventCallback): void {
    const callbacks = this.subscribers.get(event);
    if (callbacks) {
      callbacks.delete(callback);

      // Clean up empty event sets
      if (callbacks.size === 0) {
        this.subscribers.delete(event);
      }
    }
  }

  /**
   * Subscribe to an event that will only fire once
   * @param event - Event name to listen for
   * @param callback - Function to call when event is emitted
   */
  public once(event: string, callback: EventCallback): void {
    const onceCallback = (data?: any) => {
      callback(data);
      this.off(event, onceCallback);
    };
    this.on(event, onceCallback);
  }

  /**
   * Clear all subscribers for an event, or all events if no event specified
   * @param event - Optional event name to clear
   */
  public clear(event?: string): void {
    if (event) {
      this.subscribers.delete(event);
    } else {
      this.subscribers.clear();
    }
  }

  /**
   * Get the number of subscribers for an event
   * @param event - Event name
   * @returns Number of subscribers
   */
  public listenerCount(event: string): number {
    return this.subscribers.get(event)?.size || 0;
  }
}

// Export single instance - ES modules are singletons by default
export const eventBus = new EventBus();

// Also export the class for testing purposes
export { EventBus };
