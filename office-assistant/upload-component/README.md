# Upload Component

A web component for uploading and importing PDF bank statements into the database.

## Features

- Lists recent PDF downloads from the Downloads folder
- Shows files from the last hour, or last 3 files if none are recent
- Radio button selection for choosing which file to import
- Integrates with the PDF import pipeline
- Shows loading spinner during processing
- Displays success/error messages
- Emits events via the event bus

## Usage

```html
<upload-component api-endpoint="/api/import-pdf"></upload-component>

<script type="module">
  import "./js/upload-component.js";
</script>
```

## Attributes

- `api-endpoint`: URL endpoint for the import API (default: "/api/import-pdf")

## Events

The component emits the following events via the event bus:

- `upload:file-selected` - When a file is selected
  ```js
  { filename: "statement.pdf", path: "/path/to/file" }
  ```

- `upload:complete` - When import completes successfully
  ```js
  {
    filename: "statement.pdf",
    result: {
      success: true,
      total_transactions: 50,
      successful_imports: 45,
      duplicate_count: 5
    }
  }
  ```

- `upload:error` - When import fails
  ```js
  { filename: "statement.pdf", error: "error message" }
  ```

## Development

### Building

```bash
cd upload-component
npx tsc
```

This compiles `upload-component.ts` to JavaScript in the `../js` directory.

### API Requirements

The component requires two backend endpoints:

1. **GET /api/recent-downloads**
   - Returns list of recent PDF files
   - Response: `[{ filename: string, path: string, downloadTime: string }]`

2. **POST /api/import-pdf**
   - Imports a PDF statement
   - Request: `{ filePath: string }`
   - Response: `{ success: bool, total_transactions: int, successful_imports: int, duplicate_count: int }`

## Styling

The component uses shadow DOM and includes all styling internally. It matches the style of the category-picker component with:

- Clean, minimal design
- System fonts
- Responsive layout
- Hover states
- Success/error color coding
