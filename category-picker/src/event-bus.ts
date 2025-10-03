export type AppEventMap = {
  "expense:progress": { expenseId: string; path: string[] };
  "expense:categorized": { expenseId: string; path: string[]; label: string; nodeId: string };
};

export function emit<K extends keyof AppEventMap>(
  name: K,
  detail: AppEventMap[K]
): void {
  // Use the global window as our event bus
  window.dispatchEvent(new CustomEvent(name, { detail }));
}

export function on<K extends keyof AppEventMap>(
  name: K,
  handler: (ev: CustomEvent<AppEventMap[K]>) => void
): () => void {
  const wrapped = (ev: Event) => handler(ev as CustomEvent<AppEventMap[K]>);
  window.addEventListener(name, wrapped as EventListener);
  return () => window.removeEventListener(name, wrapped as EventListener);
}
