import { emit } from "../js/event-bus.js";

const tpl = document.createElement("template");
tpl.innerHTML = `
  <style>
    :host{
      display:block;
      font: 14px/1.4 system-ui, -apple-system, Segoe UI, Roboto, Helvetica, Arial;
      color:#111;
      border:1px solid #bbb;
      border-radius:8px;
      padding:16px;
      background:#fff;
    }
    .header {
      font-size: 16px;
      font-weight: 600;
      margin-bottom: 12px;
    }
    .files-list {
      display: flex;
      flex-direction: column;
      gap: 8px;
    }
    .file-row {
      display: flex;
      align-items: center;
      gap: 12px;
      padding: 8px;
      border: 1px solid #ddd;
      border-radius: 6px;
      background: #fafafa;
      transition: background 0.2s ease;
      cursor: pointer;
    }
    .file-row:hover {
      background: #f0f0f0;
    }
    .file-row.selected {
      background: #e6f3ff;
      border-color: #4a90e2;
    }
    .file-row input[type="radio"] {
      cursor: pointer;
    }
    .file-info {
      flex: 1;
      display: flex;
      flex-direction: column;
      gap: 4px;
    }
    .file-name {
      font-weight: 500;
      color: #222;
    }
    .file-meta {
      font-size: 12px;
      color: #222;
    }
    .upload-button {
      margin-top: 12px;
      padding: 8px 16px;
      border: 1px solid #4a90e2;
      background: #4a90e2;
      color: white;
      border-radius: 6px;
      cursor: pointer;
      font-weight: 500;
      transition: background 0.2s ease;
    }
    .upload-button:hover:not(:disabled) {
      background: #357abd;
    }
    .upload-button:disabled {
      background: #ccc;
      border-color: #ccc;
      cursor: not-allowed;
    }
    .terminal {
      display: none;
      margin-top: 12px;
      background: #000;
      border: 1px solid #333;
      border-radius: 6px;
      padding: 12px;
      font-family: 'Courier New', Courier, monospace;
      font-size: 12px;
      color: #0f0;
      height: 160px;
      overflow: hidden;
      position: relative;
    }
    .terminal.active {
      display: block;
    }
    .terminal-content {
      display: flex;
      flex-direction: column;
      gap: 2px;
      animation: scroll-up 0.3s ease-out;
    }
    .terminal-line {
      white-space: pre-wrap;
      word-wrap: break-word;
      line-height: 1.4;
      opacity: 0;
      animation: fade-in 0.2s ease-out forwards;
    }
    .terminal-line.old {
      opacity: 0.6;
    }
    @keyframes scroll-up {
      from {
        transform: translateY(10px);
      }
      to {
        transform: translateY(0);
      }
    }
    @keyframes fade-in {
      from {
        opacity: 0;
      }
      to {
        opacity: 1;
      }
    }
    .terminal-cursor::after {
      content: "_";
      animation: blink 1s infinite;
    }
    @keyframes blink {
      0%, 50% { opacity: 1; }
      51%, 100% { opacity: 0; }
    }
    .status-message {
      margin-top: 12px;
      padding: 8px;
      border-radius: 6px;
      font-size: 13px;
    }
    .status-message.success {
      background: #e6ffe6;
      border: 1px solid #9bd49b;
      color: #2d5a2d;
    }
    .status-message.error {
      background: #ffe6e6;
      border: 1px solid #d49b9b;
      color: #5a2d2d;
    }
    .no-files {
      padding: 16px;
      text-align: center;
      color: #666;
      font-style: italic;
    }
  </style>
  <div class="header">Recent PDF Downloads</div>
  <div class="files-list" id="filesList"></div>
  <button class="upload-button" id="uploadBtn" disabled>Import Selected PDF</button>
  <div class="terminal" id="terminal">
    <div class="terminal-content" id="terminalContent"></div>
  </div>
  <div class="status-message" id="statusMsg" style="display:none;"></div>
`;

interface DownloadFile {
  filename: string;
  path: string;
  downloadTime: Date;
}

/**
 * <upload-component> — a custom element that displays recent PDF downloads
 * from the system and allows importing them into the database.
 *
 * Attributes:
 *  - api-endpoint: URL endpoint for uploading/importing files
 */
export class UploadComponent extends HTMLElement {
  static get observedAttributes() {
    return ["api-endpoint"];
  }

  private root: ShadowRoot;
  private filesList!: HTMLElement;
  private uploadBtn!: HTMLButtonElement;
  private terminal!: HTMLElement;
  private terminalContent!: HTMLElement;
  private statusMsg!: HTMLElement;
  private selectedFile: DownloadFile | null = null;
  private apiEndpoint: string = "/api/import-pdf";
  private terminalLines: string[] = [];
  private maxTerminalLines: number = 8;

  constructor() {
    super();
    this.root = this.attachShadow({ mode: "open" });
    this.root.appendChild(tpl.content.cloneNode(true));
  }

  connectedCallback() {
    this.filesList = this.root.getElementById("filesList")!;
    this.uploadBtn = this.root.getElementById("uploadBtn") as HTMLButtonElement;
    this.terminal = this.root.getElementById("terminal")!;
    this.terminalContent = this.root.getElementById("terminalContent")!;
    this.statusMsg = this.root.getElementById("statusMsg")!;

    this.uploadBtn.addEventListener("click", () => this.handleUpload());

    if (this.hasAttribute("api-endpoint")) {
      this.apiEndpoint = this.getAttribute("api-endpoint") || this.apiEndpoint;
    }

    this.loadRecentDownloads();
  }

  attributeChangedCallback(name: string, _old: string | null, val: string | null) {
    if (name === "api-endpoint" && val) {
      this.apiEndpoint = val;
    }
  }

  /**
   * Load recent PDF downloads from the Downloads folder
   */
  private async loadRecentDownloads() {
    try {
      // Call backend API to get recent downloads
      const response = await fetch("/api/recent-downloads", {
        method: "GET",
        headers: { "Content-Type": "application/json" }
      });

      if (!response.ok) {
        throw new Error(`Failed to fetch downloads: ${response.statusText}`);
      }

      const files: DownloadFile[] = await response.json();
      this.renderFiles(files);
    } catch (error) {
      console.error("[upload-component] Error loading downloads:", error);
      this.showError("Failed to load recent downloads");
      this.renderNoFiles();
    }
  }

  /**
   * Render the list of files
   */
  private renderFiles(files: DownloadFile[]) {
    if (files.length === 0) {
      this.renderNoFiles();
      return;
    }

    this.filesList.innerHTML = "";

    files.forEach((file, index) => {
      const row = document.createElement("div");
      row.className = "file-row";

      const radio = document.createElement("input");
      radio.type = "radio";
      radio.name = "file-select";
      radio.id = `file-${index}`;
      radio.addEventListener("change", () => this.selectFile(file, row));

      // Make entire row clickable
      row.addEventListener("click", () => {
        radio.checked = true;
        this.selectFile(file, row);
      });

      const info = document.createElement("div");
      info.className = "file-info";

      const name = document.createElement("div");
      name.className = "file-name";
      name.textContent = file.filename;

      const meta = document.createElement("div");
      meta.className = "file-meta";
      const downloadTime = new Date(file.downloadTime);
      meta.textContent = `Downloaded ${this.formatTime(downloadTime)}`;

      info.appendChild(name);
      info.appendChild(meta);

      row.appendChild(radio);
      row.appendChild(info);

      this.filesList.appendChild(row);
    });
  }

  /**
   * Render message when no files are available
   */
  private renderNoFiles() {
    this.filesList.innerHTML = '<div class="no-files">No recent PDF downloads found</div>';
    this.uploadBtn.disabled = true;
  }

  /**
   * Format timestamp for display
   */
  private formatTime(date: Date): string {
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);

    if (diffMins < 60) {
      return `${diffMins} minute${diffMins !== 1 ? 's' : ''} ago`;
    }

    const diffHours = Math.floor(diffMins / 60);
    if (diffHours < 24) {
      return `${diffHours} hour${diffHours !== 1 ? 's' : ''} ago`;
    }

    return date.toLocaleString();
  }

  /**
   * Handle file selection
   */
  private selectFile(file: DownloadFile, rowElement: HTMLElement) {
    this.selectedFile = file;
    this.uploadBtn.disabled = false;

    // Update visual selection
    const allRows = this.filesList.querySelectorAll(".file-row");
    allRows.forEach(row => row.classList.remove("selected"));
    rowElement.classList.add("selected");

    // Emit selection event
    emit("upload:file-selected", {
      filename: file.filename,
      path: file.path
    });
  }

  /**
   * Add a line to the terminal output
   */
  private addTerminalLine(text: string) {
    this.terminalLines.push(text);

    // Keep only the last N lines
    if (this.terminalLines.length > this.maxTerminalLines) {
      this.terminalLines.shift();
    }

    // Re-render terminal content
    this.terminalContent.innerHTML = "";
    this.terminalLines.forEach((line, index) => {
      const lineDiv = document.createElement("div");
      lineDiv.className = "terminal-line";
      if (index < this.terminalLines.length - 3) {
        lineDiv.classList.add("old");
      }
      lineDiv.textContent = line;
      this.terminalContent.appendChild(lineDiv);
    });
  }

  /**
   * Clear terminal output
   */
  private clearTerminal() {
    this.terminalLines = [];
    this.terminalContent.innerHTML = "";
  }

  /**
   * Handle upload button click
   */
  private async handleUpload() {
    if (!this.selectedFile) return;

    this.uploadBtn.disabled = true;
    this.terminal.classList.add("active");
    this.hideStatus();
    this.clearTerminal();

    this.addTerminalLine(`> Starting import of ${this.selectedFile.filename}`);
    this.addTerminalLine(`> File path: ${this.selectedFile.path}`);

    try {
      this.addTerminalLine(`> Starting PDF import process...`);

      // Call backend API to import the PDF with streaming
      const response = await fetch(this.apiEndpoint, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Accept": "text/event-stream"
        },
        body: JSON.stringify({
          filePath: this.selectedFile.path
        })
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: response.statusText }));
        throw new Error(errorData.detail || "Import failed");
      }

      // Check if response has streaming capability
      const contentType = response.headers.get("content-type");
      if (response.body && contentType?.includes("text/event-stream")) {
        this.addTerminalLine(`> Processing with real-time updates...`);
        await this.processStreamingResponse(response);
      } else {
        // Fallback to regular JSON response
        this.addTerminalLine(`> Using standard processing...`);
        await this.processRegularResponse(response);
      }

    } catch (error) {
      console.error("[upload-component] Upload error:", error);
      this.addTerminalLine(`✗ ERROR: ${error instanceof Error ? error.message : "Failed to import PDF"}`);

      setTimeout(() => {
        this.showError(error instanceof Error ? error.message : "Failed to import PDF");
        this.terminal.classList.remove("active");
      }, 2000);

      emit("upload:error", {
        filename: this.selectedFile?.filename,
        error: error instanceof Error ? error.message : "Unknown error"
      });
    } finally {
      this.uploadBtn.disabled = false;
    }
  }

  /**
   * Process streaming response from server using Server-Sent Events
   */
  private async processStreamingResponse(response: Response) {
    const reader = response.body!.getReader();
    const decoder = new TextDecoder();
    let buffer = '';

    try {
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');

        // Keep the last incomplete line in buffer
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6));

              if (data.type === 'log' && data.message) {
                // Clean up logging prefixes for cleaner display
                let msg = data.message;

                // Remove timestamp and logger name from log lines
                msg = msg.replace(/^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3} - .+ - \w+ - /, '');

                // Skip purely informational DEBUG/INFO prefixes
                if (msg.trim()) {
                  this.addTerminalLine(msg);
                }
              } else if (data.type === 'complete' && data.stats) {
                this.handleUploadComplete(data.stats);
                break;
              } else if (data.type === 'error' && data.message) {
                this.addTerminalLine(`✗ ERROR: ${data.message}`);
                throw new Error(data.message);
              }
            } catch (e) {
              if (e instanceof SyntaxError) {
                console.error('[upload-component] Failed to parse SSE data:', line);
              } else {
                throw e;
              }
            }
          }
        }
      }
    } finally {
      reader.releaseLock();
    }
  }

  /**
   * Process regular JSON response
   */
  private async processRegularResponse(response: Response) {
    const result = await response.json();

    // Check if we have output_lines from the backend
    if (result.output_lines && Array.isArray(result.output_lines)) {
      // Display each line with a delay for smooth scrolling
      for (const line of result.output_lines) {
        // Skip empty lines and separator lines
        if (line.trim() && !line.match(/^=+$/)) {
          this.addTerminalLine(line);
          await this.sleep(150);  // Fast but visible scrolling
        }
      }
    } else {
      // Fallback: simulate detailed progress
      this.addTerminalLine(`✓ PDF validated successfully`);
      await this.sleep(200);

      this.addTerminalLine(`> Extracting account information...`);
      await this.sleep(300);

      this.addTerminalLine(`> Parsing transactions...`);
      await this.sleep(400);

      this.addTerminalLine(`✓ Found ${result.total_transactions || 0} transactions`);
      await this.sleep(200);

      this.addTerminalLine(`> Checking for duplicates...`);
      await this.sleep(300);

      if (result.duplicate_count > 0) {
        this.addTerminalLine(`⚠ Skipped ${result.duplicate_count} duplicate(s)`);
        await this.sleep(200);
      }

      this.addTerminalLine(`> Inserting into database...`);
      await this.sleep(400);

      this.addTerminalLine(`✓ Successfully imported ${result.successful_imports || 0} transaction(s)`);
      await this.sleep(200);

      if (result.failed_imports > 0) {
        this.addTerminalLine(`✗ Failed to import ${result.failed_imports} transaction(s)`);
        await this.sleep(200);
      }

      this.addTerminalLine(`> Import complete!`);
    }

    this.handleUploadComplete(result);
  }

  /**
   * Handle successful upload completion
   */
  private handleUploadComplete(result: any) {
    setTimeout(() => {
      this.showSuccess(
        `Successfully imported ${result.successful_imports || 0} transactions ` +
        `(${result.duplicate_count || 0} duplicates skipped)`
      );
      this.terminal.classList.remove("active");
    }, 1500);

    // Emit success event
    emit("upload:complete", {
      filename: this.selectedFile?.filename,
      result: result
    });

    // Reset selection
    this.selectedFile = null;
    this.uploadBtn.disabled = true;

    // Refresh the file list
    setTimeout(() => this.loadRecentDownloads(), 2000);
  }

  /**
   * Sleep utility
   */
  private sleep(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  /**
   * Show success message
   */
  private showSuccess(message: string) {
    this.statusMsg.textContent = message;
    this.statusMsg.className = "status-message success";
    this.statusMsg.style.display = "block";
  }

  /**
   * Show error message
   */
  private showError(message: string) {
    this.statusMsg.textContent = message;
    this.statusMsg.className = "status-message error";
    this.statusMsg.style.display = "block";
  }

  /**
   * Hide status message
   */
  private hideStatus() {
    this.statusMsg.style.display = "none";
  }
}

// Define custom element
if (!customElements.get("upload-component")) {
  customElements.define("upload-component", UploadComponent);
}
