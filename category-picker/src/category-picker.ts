import { emit } from "./event-bus.js";
import type { CategoryNode } from "./types.js";

type NodePath = CategoryNode[];

const tpl = document.createElement("template");
tpl.innerHTML = `
  <style>
    :host{
      display:inline-block;
      font: 14px/1.4 system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial;
      color:#111;
      border:1px solid #bbb;
      border-radius:8px;
      padding:8px;
      background:#fff;
      transition: background .2s ease, border-color .2s ease;
    }
    :host([data-state="done"]) {
      background: #e6ffe6;
      border-color:#9bd49b;
    }
    :host([data-state="done"][data-category="Personal"]) {
      background: #e8e8e8;
      border-color:#999;
    }
    .row{ display:flex; gap:8px; align-items:center; }
    select, input[type="text"] {
      padding:6px 8px;
      border:1px solid #bbb;
      border-radius:6px;
      min-width: 240px;
    }
    input[readonly]{
      background:#fafafa;
    }
    button.reset{
      border:1px solid #bbb;
      background:#f6f6f6;
      border-radius:6px;
      padding:6px 10px;
      cursor:pointer;
    }
    button.reset:hover{ background:#efefef; }
    .status{ margin-top:6px; }
  </style>
  <div class="row">
    <select id="selector" aria-label="Category selector"></select>
    <button id="reset" class="reset" title="Clear / Re-categorize" hidden>Reset</button>
  </div>
  <div class="status">
    <input id="status" type="text" readonly value=""/>
  </div>
`;

function joinLabels(path: NodePath): string {
  return path.map(n => n.label).join(" / ");
}

function ensureArray<T>(v: T | T[] | undefined): T[] {
  if (!v) return [];
  return Array.isArray(v) ? v : [v];
}

/**
 * <category-picker> — a form-associated custom element that behaves like
 * a cascading category selector. It re-uses a single <select>, repopulating
 * on each step. When a leaf is chosen, it finalizes and turns green.
 *
 * Attributes:
 *  - name: form field name (for <form> submission)
 *  - data-src: URL to a JSON taxonomy (see /public/categories.json)
 *  - expense-id: identifier for the expense row to emit with events
 *  - placeholder: optional placeholder for the initial select
 */
export class CategoryPicker extends HTMLElement {
  static formAssociated = true;
  static get observedAttributes() {
    return ["name", "data-src", "expense-id", "placeholder", "disabled"];
  }

  private internals: ElementInternals;
  private root: ShadowRoot;
  private selectEl!: HTMLSelectElement;
  private statusEl!: HTMLInputElement;
  private resetBtn!: HTMLButtonElement;

  private taxonomy: CategoryNode[] = [];
  private path: NodePath = [];
  private currentOptions: CategoryNode[] = [];
  private expenseId: string = "";
  private placeholder: string = "Select a category…";
  private _value: string = "";

  constructor() {
    super();
    this.root = this.attachShadow({ mode: "open" });
    this.root.appendChild(tpl.content.cloneNode(true));
    // ElementInternals for form association
    this.internals = this.attachInternals();
  }

  connectedCallback() {
    this.selectEl = this.root.getElementById("selector") as HTMLSelectElement;
    this.statusEl = this.root.getElementById("status") as HTMLInputElement;
    this.resetBtn = this.root.getElementById("reset") as HTMLButtonElement;

    this.selectEl.addEventListener("change", () => this.handleChange());
    this.resetBtn.addEventListener("click", () => this.reset());

    if (this.hasAttribute("placeholder")) {
      this.placeholder = this.getAttribute("placeholder") || this.placeholder;
    }
    if (this.hasAttribute("expense-id")) {
      this.expenseId = this.getAttribute("expense-id") || "";
    }
    const ds = this.getAttribute("data-src");
    if (ds) {
      this.loadData(ds);
    } else {
      // Allow inline JSON via <script type="application/json"> child
      const script = this.querySelector('script[type="application/json"]');
      if (script?.textContent?.trim()) {
        try {
          const data = JSON.parse(script.textContent);
          this.setTaxonomy(data);
        } catch (e) {
          console.error("[category-picker] Failed to parse inline JSON:", e);
          const message = e instanceof Error ? e.message : String(e);
          this.notifyTaxonomy(true, message);
        }
      } else {
        // No data provided — still render empty selector
        this.renderOptions([]);
        this.notifyTaxonomy(true);
      }
    }

    this.reflectDisabled();
  }

  attributeChangedCallback(name: string, _old: string | null, val: string | null) {
    switch (name) {
      case "name":
        this.updateCustomState("name", Boolean(val));
        break;
      case "expense-id":
        this.expenseId = val || "";
        break;
      case "placeholder":
        this.placeholder = val || this.placeholder;
        if (this.isConnected && this.selectEl) {
          this.renderOptions(this.currentOptions);
        }
        break;
      case "disabled":
        this.reflectDisabled();
        break;
    }
  }

  private reflectDisabled() {
    const disabled = this.hasAttribute("disabled");
    this.selectEl?.toggleAttribute("disabled", disabled);
    this.resetBtn?.toggleAttribute("disabled", disabled);
  }

  /** Public API: programmatically set taxonomy */
  public setTaxonomy(nodes: CategoryNode[]) {
    this.taxonomy = ensureArray(nodes);
    this.path = [];
    this.renderOptions(this.taxonomy);
    this.updateStatus();
    this.markIncomplete();
    this.notifyTaxonomy(this.taxonomy.length === 0);
  }

  /** Fetch JSON taxonomy from URL */
  private async loadData(url: string) {
    try {
      const res = await fetch(url, { cache: "no-store" });
      if (!res.ok) throw new Error(`${res.status} ${res.statusText}`);
      const data = (await res.json()) as CategoryNode[];
      this.setTaxonomy(data);
    } catch (e) {
      console.error("[category-picker] Failed to load data-src:", e);
      this.renderOptions([]);
      const message = e instanceof Error ? e.message : String(e);
      this.notifyTaxonomy(true, message);
    }
  }

  /** Handle selection step */
  private handleChange() {
    const selectedId = this.selectEl.value;
    const next = this.currentOptions.find(n => n.id === selectedId);
    if (!next) return;

    // Advance path
    this.path.push(next);

    if (next.children && next.children.length) {
      // Show next level
      this.renderOptions(next.children);
      this.updateStatus(/*incomplete*/ true);
      emit("expense:progress", {
        expenseId: this.expenseId,
        path: this.path.map(n => n.label)
      });
    } else {
      // Leaf chosen -> finalize
      this.finalize();
    }
  }

  /** Render options into the single <select> */
  private renderOptions(options: CategoryNode[]) {
    this.currentOptions = options;
    this.selectEl.innerHTML = "";

    const ph = document.createElement("option");
    ph.value = "";
    ph.textContent = this.placeholder;
    ph.disabled = true;
    ph.selected = true;
    this.selectEl.appendChild(ph);

    for (const node of options) {
      const opt = document.createElement("option");
      opt.value = node.id;
      opt.textContent = node.label;
      this.selectEl.appendChild(opt);
    }
  }

  /** Update the status text box */
  private updateStatus(incomplete: boolean = false) {
    const base = joinLabels(this.path);
    this.statusEl.value = incomplete ? (base ? base + " / " : "") : base;
  }

  private finalize() {
    // Remove the selector and show a green state (or grey for Personal)
    const fullLabel = joinLabels(this.path);
    this._value = fullLabel;
    this.internals.setFormValue(fullLabel);
    this.updateStatus(false);

    // Check if the root category is "Personal" and set data-category attribute
    const rootCategory = this.path.length > 0 ? this.path[0].label : "";
    if (rootCategory === "Personal") {
      this.setAttribute("data-category", "Personal");
    }

    this.markComplete();
    // Remove the <select> (as requested), show reset button
    this.selectEl.remove();
    this.resetBtn.hidden = false;

    const leaf = this.path[this.path.length - 1];
    emit("expense:categorized", {
      expenseId: this.expenseId,
      path: this.path.map(n => n.label),
      label: fullLabel,
      nodeId: leaf?.id ?? ""
    });

    // Also fire a DOM event locally for anyone who prefers bubbling events
    this.dispatchEvent(new CustomEvent("completed", {
      detail: { expenseId: this.expenseId, label: fullLabel, path: this.path.map(n => n.label) },
      bubbles: true, composed: true
    }));
  }

  /** Reset back to root */
  public reset() {
    this.path = [];
    this._value = "";
    this.internals.setFormValue(null);
    this.resetBtn.hidden = true;
    // Remove data-category attribute when resetting
    this.removeAttribute("data-category");
    // Recreate the select if it was removed
    if (!this.root.getElementById("selector")) {
      const row = this.root.querySelector(".row")!;
      const sel = document.createElement("select");
      sel.id = "selector";
      sel.setAttribute("aria-label", "Category selector");
      sel.addEventListener("change", () => this.handleChange());
      row.insertBefore(sel, this.resetBtn);
      this.selectEl = sel;
      this.reflectDisabled();
    }
    this.renderOptions(this.taxonomy);
    this.updateStatus(true);
    this.markIncomplete();
  }

  /** Mark done -> light green */
  private markComplete() {
    this.setAttribute("data-state", "done");
  }
  private markIncomplete() {
    this.setAttribute("data-state", "in-progress");
  }

  private updateCustomState(token: string, enabled: boolean) {
    const extendedInternals = this.internals as ElementInternals & {
      states?: { add?: (t: string) => void; delete?: (t: string) => void; remove?: (t: string) => void };
    };
    const states = extendedInternals.states;
    if (!states) return;
    const add = (states as any).add as ((t: string) => void) | undefined;
    const remove = ((states as any).delete ?? (states as any).remove) as ((t: string) => void) | undefined;
    if (enabled) {
      add?.call(states, token);
    } else {
      remove?.call(states, token);
    }
  }

  // Form-associated plumbing
  formAssociatedCallback() {/* noop */}
  formDisabledCallback(disabled: boolean) {
    if (disabled) this.setAttribute("disabled", "");
    else this.removeAttribute("disabled");
  }
  formResetCallback() { this.reset(); }
  formStateRestoreCallback(state: unknown) {
    if (typeof state === "string" && state) {
      // Accept restored value as final label (no rehydration of path tree here)
      this._value = state;
      this.statusEl.value = state;
      this.markComplete();
      this.selectEl.remove();
      this.resetBtn.hidden = false;
    }
  }

  private notifyTaxonomy(empty: boolean, errorMessage?: string) {
    this.toggleAttribute("data-empty", empty);
    const eventName = errorMessage ? "taxonomy-error" : "taxonomy-updated";
    const detail = errorMessage ? { empty, message: errorMessage } : { empty };
    this.dispatchEvent(new CustomEvent(eventName, {
      detail,
      bubbles: true,
      composed: true
    }));
  }

  get value(): string { return this._value; }
  set value(v: string) {
    // Setting value directly marks complete with given label
    this._value = v;
    this.internals.setFormValue(v || null);
    this.statusEl.value = v || "";
    if (v) {
      // Check if value starts with "Personal" to set grey styling
      if (v.startsWith("Personal")) {
        this.setAttribute("data-category", "Personal");
      }
      this.markComplete();
      this.selectEl?.remove();
      this.resetBtn.hidden = false;
    } else {
      this.reset();
    }
  }
}

// Define once
if (!customElements.get("category-picker")) {
  customElements.define("category-picker", CategoryPicker);
}
