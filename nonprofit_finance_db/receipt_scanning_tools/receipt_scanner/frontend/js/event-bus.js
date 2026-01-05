export function emit(name, detail) {
    // Use the global window as our event bus
    window.dispatchEvent(new CustomEvent(name, { detail }));
}
export function on(name, handler) {
    const wrapped = (ev) => handler(ev);
    window.addEventListener(name, wrapped);
    return () => window.removeEventListener(name, wrapped);
}
//# sourceMappingURL=event-bus.js.map