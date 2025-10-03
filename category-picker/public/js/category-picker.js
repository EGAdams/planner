import { emit } from "./event-bus.js";
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
function joinLabels(path) {
    return path.map(n => n.label).join(" / ");
}
function ensureArray(v) {
    if (!v)
        return [];
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
    static { this.formAssociated = true; }
    static get observedAttributes() {
        return ["name", "data-src", "expense-id", "placeholder", "disabled"];
    }
    constructor() {
        super();
        this.taxonomy = [];
        this.path = [];
        this.currentOptions = [];
        this.expenseId = "";
        this.placeholder = "Select a category…";
        this._value = "";
        this.root = this.attachShadow({ mode: "open" });
        this.root.appendChild(tpl.content.cloneNode(true));
        // ElementInternals for form association
        this.internals = this.attachInternals();
    }
    connectedCallback() {
        this.selectEl = this.root.getElementById("selector");
        this.statusEl = this.root.getElementById("status");
        this.resetBtn = this.root.getElementById("reset");
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
        }
        else {
            // Allow inline JSON via <script type="application/json"> child
            const script = this.querySelector('script[type="application/json"]');
            if (script?.textContent?.trim()) {
                try {
                    const data = JSON.parse(script.textContent);
                    this.setTaxonomy(data);
                }
                catch (e) {
                    console.error("[category-picker] Failed to parse inline JSON:", e);
                }
            }
            else {
                // No data provided — still render empty selector
                this.renderOptions([]);
            }
        }
        this.reflectDisabled();
    }
    attributeChangedCallback(name, _old, val) {
        switch (name) {
            case "name":
                this.updateCustomState("name", Boolean(val));
                break;
            case "expense-id":
                this.expenseId = val || "";
                break;
            case "placeholder":
                this.placeholder = val || this.placeholder;
                this.renderOptions(this.currentOptions);
                break;
            case "disabled":
                this.reflectDisabled();
                break;
        }
    }
    reflectDisabled() {
        const disabled = this.hasAttribute("disabled");
        this.selectEl?.toggleAttribute("disabled", disabled);
        this.resetBtn?.toggleAttribute("disabled", disabled);
    }
    /** Public API: programmatically set taxonomy */
    setTaxonomy(nodes) {
        this.taxonomy = ensureArray(nodes);
        this.path = [];
        this.renderOptions(this.taxonomy);
        this.updateStatus();
        this.markIncomplete();
    }
    /** Fetch JSON taxonomy from URL */
    async loadData(url) {
        try {
            const res = await fetch(url, { cache: "no-store" });
            if (!res.ok)
                throw new Error(`${res.status} ${res.statusText}`);
            const data = (await res.json());
            this.setTaxonomy(data);
        }
        catch (e) {
            console.error("[category-picker] Failed to load data-src:", e);
            this.renderOptions([]);
        }
    }
    /** Handle selection step */
    handleChange() {
        const selectedId = this.selectEl.value;
        const next = this.currentOptions.find(n => n.id === selectedId);
        if (!next)
            return;
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
        }
        else {
            // Leaf chosen -> finalize
            this.finalize();
        }
    }
    /** Render options into the single <select> */
    renderOptions(options) {
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
    updateStatus(incomplete = false) {
        const base = joinLabels(this.path);
        this.statusEl.value = incomplete ? (base ? base + " / " : "") : base;
    }
    finalize() {
        // Remove the selector and show a green state
        const fullLabel = joinLabels(this.path);
        this._value = fullLabel;
        this.internals.setFormValue(fullLabel);
        this.updateStatus(false);
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
    reset() {
        this.path = [];
        this._value = "";
        this.internals.setFormValue(null);
        this.resetBtn.hidden = true;
        // Recreate the select if it was removed
        if (!this.root.getElementById("selector")) {
            const row = this.root.querySelector(".row");
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
    markComplete() {
        this.setAttribute("data-state", "done");
    }
    markIncomplete() {
        this.setAttribute("data-state", "in-progress");
    }
    updateCustomState(token, enabled) {
        const extendedInternals = this.internals;
        const states = extendedInternals.states;
        if (!states)
            return;
        const add = states.add;
        const remove = (states.delete ?? states.remove);
        if (enabled) {
            add?.call(states, token);
        }
        else {
            remove?.call(states, token);
        }
    }
    // Form-associated plumbing
    formAssociatedCallback() { }
    formDisabledCallback(disabled) {
        if (disabled)
            this.setAttribute("disabled", "");
        else
            this.removeAttribute("disabled");
    }
    formResetCallback() { this.reset(); }
    formStateRestoreCallback(state) {
        if (typeof state === "string" && state) {
            // Accept restored value as final label (no rehydration of path tree here)
            this._value = state;
            this.statusEl.value = state;
            this.markComplete();
            this.selectEl.remove();
            this.resetBtn.hidden = false;
        }
    }
    get value() { return this._value; }
    set value(v) {
        // Setting value directly marks complete with given label
        this._value = v;
        this.internals.setFormValue(v || null);
        this.statusEl.value = v || "";
        if (v) {
            this.markComplete();
            this.selectEl?.remove();
            this.resetBtn.hidden = false;
        }
        else {
            this.reset();
        }
    }
}
// Define once
if (!customElements.get("category-picker")) {
    customElements.define("category-picker", CategoryPicker);
}
//# sourceMappingURL=category-picker.js.map