const wasmBytes = new Uint8Array([
  0x00, 0x61, 0x73, 0x6d, 0x01, 0x00, 0x00, 0x00,
  0x01, 0x05, 0x01, 0x60, 0x00, 0x01, 0x7c,
  0x02, 0x0b, 0x01, 0x03, 0x65, 0x6e, 0x76, 0x03, 0x6e, 0x6f, 0x77, 0x00, 0x00,
  0x03, 0x02, 0x01, 0x00,
  0x07, 0x0b, 0x01, 0x07, 0x67, 0x65, 0x74, 0x54, 0x69, 0x6d, 0x65, 0x00, 0x01,
  0x0a, 0x06, 0x01, 0x04, 0x00, 0x10, 0x00, 0x0b
]);

const wasmInstancePromise = WebAssembly.instantiate(wasmBytes, {
  env: {
    now: () => Date.now()
  }
}).then(result => result.instance);

const template = document.createElement('template');
template.innerHTML = `
  <style>
    :host {
      font-family: "Inter", "Segoe UI", system-ui, -apple-system, sans-serif;
      display: inline-flex;
      flex-direction: column;
      gap: 0.25rem;
      padding: 1rem 1.25rem;
      border-radius: 1rem;
      border: 1px solid #e5e7eb;
      background: linear-gradient(145deg, #ffffff, #f3f4f6);
      color: #111827;
      min-width: 16rem;
      box-shadow: 0 8px 20px rgba(15, 23, 42, 0.08);
    }
    .time {
      font-size: 1.35rem;
      font-weight: 600;
      letter-spacing: 0.02em;
    }
    .subtitle {
      font-size: 0.85rem;
      color: #6b7280;
    }
  </style>
  <div class="time">Loading current time...</div>
  <div class="subtitle">Preparing WebAssembly clock</div>
`;

class WasmClock extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: 'open' });
    this.shadowRoot.appendChild(template.content.cloneNode(true));
    this._timeEl = this.shadowRoot.querySelector('.time');
    this._subtitleEl = this.shadowRoot.querySelector('.subtitle');
    this._timer = null;
    this._instance = null;
    this._formatter = null;
    this._formatterLocale = null;
    this._isStarting = false;
    this._readyPromise = wasmInstancePromise.then(instance => {
      this._instance = instance;
      return instance;
    });
  }

  connectedCallback() {
    if (!this._timer && !this._isStarting) {
      this.startUpdates();
    }
  }

  disconnectedCallback() {
    if (this._timer) {
      clearInterval(this._timer);
      this._timer = null;
    }
  }

  async startUpdates() {
    this._isStarting = true;
    try {
      await this._readyPromise;
      if (!this.isConnected || !this._instance) {
        return;
      }
      this.updateTime();
      this._timer = setInterval(() => this.updateTime(), 1000);
      this._subtitleEl.textContent = 'Updated every second';
    } catch (error) {
      this._timeEl.textContent = 'Unable to load time';
      this._subtitleEl.textContent = 'WebAssembly failed to initialize';
      console.error('Wasm clock initialization failed', error);
    } finally {
      this._isStarting = false;
    }
  }

  updateTime() {
    if (!this._instance) {
      return;
    }
    const timestamp = this._instance.exports.getTime();
    const date = new Date(timestamp);
    const locale = navigator.language || 'en-US';
    if (!this._formatter || this._formatterLocale !== locale) {
      this._formatter = new Intl.DateTimeFormat(locale, {
        dateStyle: 'full',
        timeStyle: 'long'
      });
      this._formatterLocale = locale;
    }
    this._timeEl.textContent = this._formatter.format(date);
    const precise = date.toLocaleTimeString(locale, {
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    });
    this._subtitleEl.textContent = `Current time for ${locale} - ${precise}`;
  }
}

if (!customElements.get('wasm-clock')) {
  customElements.define('wasm-clock', WasmClock);
}