/**
 * <upload-component> — a custom element that displays recent PDF downloads
 * from the system and allows importing them into the database.
 *
 * Attributes:
 *  - api-endpoint: URL endpoint for uploading/importing files
 */
export declare class UploadComponent extends HTMLElement {
    static get observedAttributes(): string[];
    private root;
    private filesList;
    private uploadBtn;
    private terminal;
    private terminalContent;
    private statusMsg;
    private selectedFile;
    private apiEndpoint;
    private terminalLines;
    private maxTerminalLines;
    constructor();
    connectedCallback(): void;
    attributeChangedCallback(name: string, _old: string | null, val: string | null): void;
    /**
     * Load recent PDF downloads from the Downloads folder
     */
    private loadRecentDownloads;
    /**
     * Render the list of files
     */
    private renderFiles;
    /**
     * Render message when no files are available
     */
    private renderNoFiles;
    /**
     * Format timestamp for display
     */
    private formatTime;
    /**
     * Handle file selection
     */
    private selectFile;
    /**
     * Add a line to the terminal output
     */
    private addTerminalLine;
    /**
     * Clear terminal output
     */
    private clearTerminal;
    /**
     * Handle upload button click
     */
    private handleUpload;
    /**
     * Process streaming response from server using Server-Sent Events
     */
    private processStreamingResponse;
    /**
     * Process regular JSON response
     */
    private processRegularResponse;
    /**
     * Handle successful upload completion
     */
    private handleUploadComplete;
    /**
     * Sleep utility
     */
    private sleep;
    /**
     * Show success message
     */
    private showSuccess;
    /**
     * Show error message
     */
    private showError;
    /**
     * Hide status message
     */
    private hideStatus;
}
//# sourceMappingURL=upload-component.d.ts.map