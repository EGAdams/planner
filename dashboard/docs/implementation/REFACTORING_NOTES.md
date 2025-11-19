# EventBus Refactoring - Best Practices Implementation

## What Changed

The EventBus has been refactored from an HTMLElement web component to a plain TypeScript class following industry best practices.

## Why This Is Better

### Before (Anti-Pattern)
```typescript
// event-bus component extended HTMLElement unnecessarily
export class EventBus extends HTMLElement {
  private eventSource: EventSource | null = null;
  // Mixed concerns: SSE connection + event bus + web component
}
```

**Problems:**
- ❌ Unnecessary DOM overhead (Shadow DOM, lifecycle callbacks, rendering)
- ❌ Mixed responsibilities (SSE connection + event distribution)
- ❌ Required adding invisible element to HTML
- ❌ Not following standard pub/sub patterns
- ❌ Harder to test and maintain

### After (Best Practice)
```typescript
// Pure EventBus class - ES Module Singleton
class EventBus {
  private subscribers: Map<string, Set<EventCallback>> = new Map();
  on(event, callback) { /* ... */ }
  emit(event, data) { /* ... */ }
  off(event, callback) { /* ... */ }
}
export const eventBus = new EventBus();

// Separate SSEManager class for server connection
export class SSEManager {
  connect() { /* handles SSE and emits to EventBus */ }
}
export const sseManager = new SSEManager();
```

**Benefits:**
- ✅ Single Responsibility Principle - each class has one job
- ✅ ES Module Singleton - simplest modern approach
- ✅ No DOM overhead - pure JavaScript
- ✅ Standard pub/sub pattern used by industry
- ✅ Easy to test and maintain
- ✅ Better memory management with cleanup

## Changes Made

### 1. EventBus (`event-bus/event-bus.ts`)
- **Changed from:** HTMLElement web component
- **Changed to:** Plain TypeScript class with pub/sub pattern
- **Features:**
  - `on(event, callback)` - Subscribe to events
  - `emit(event, data)` - Emit events
  - `off(event, callback)` - Unsubscribe
  - `once(event, callback)` - Subscribe once
  - `clear(event?)` - Clear subscriptions
  - `listenerCount(event)` - Get subscriber count

### 2. SSEManager (`event-bus/sse-manager.ts`)
- **New separate class** for Server-Sent Events
- **Responsibilities:**
  - Connect to SSE endpoint
  - Parse server events
  - Emit to EventBus
  - Handle reconnection logic
- **Exports:** Singleton instance `sseManager`

### 3. Web Components Updates
All web components now:
- Import `eventBus` directly
- Use `eventBus.on()` instead of `window.addEventListener('bus-event')`
- Store unsubscribe functions
- Clean up in `disconnectedCallback()`

**Updated components:**
- `port-monitor/port-monitor.ts`
- `server-list/server-list.ts`
- `server-controller/server-controller.ts`
- `process-killer/process-killer.ts`

### 4. Main Application (`main.ts`)
- Imports `eventBus` and `sseManager`
- Initializes SSE connection: `sseManager.connect()`
- Subscribes to connection status events

### 5. HTML (`public/index.html`)
- Removed `<event-bus>` web component element
- Removed event-bus script tag (loaded via imports)
- Kept other component script tags

## Research Sources

This refactoring was based on:
- **This Dot Labs**: Web Components Communication Using an Event Bus
- **Stack Overflow**: Best practices for web component communication
- **Luis Aviles Blog**: How to Implement an Event Bus in TypeScript
- **Frontend Masters**: Event-driven patterns in vanilla JavaScript

## Usage Example

### Before
```typescript
// Had to use window events
window.addEventListener('bus-event', (e: CustomEvent) => {
  if (e.detail.type === 'ports-updated') {
    // handle data
  }
});
```

### After
```typescript
// Clean, direct subscription
import { eventBus } from '../event-bus/event-bus.js';

const unsubscribe = eventBus.on('ports-updated', (data) => {
  // handle data
});

// Clean up when done
unsubscribe();
```

## Testing the Refactored Dashboard

1. Build: `npm run build`
2. Start: `npm start`
3. Open: http://localhost:3030

All functionality works the same, but with:
- Better separation of concerns
- Cleaner code structure
- Easier to maintain and extend
- Following industry best practices

## Architecture Diagram

```
┌─────────────┐
│   main.ts   │  (Initializes sseManager)
└──────┬──────┘
       │
       ├──────────────────┬──────────────┐
       │                  │              │
┌──────▼─────┐    ┌──────▼──────┐  ┌───▼────────┐
│ SSEManager │───>│  EventBus   │<─│ Components │
│ (SSE conn) │    │ (pub/sub)   │  │ (UI logic) │
└────────────┘    └─────────────┘  └────────────┘
                         ▲
                         │
                    emit/on/off
```

## Future Improvements

- Add TypeScript event types for type-safe events
- Add event debugging/logging in development mode
- Consider using RxJS for advanced reactive patterns
- Add unit tests for EventBus and SSEManager
