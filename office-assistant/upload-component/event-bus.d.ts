declare module "../js/event-bus.js" {
  export function emit(name: string, detail: any): void;
  export function on(name: string, handler: (event: CustomEvent) => void): () => void;
}
