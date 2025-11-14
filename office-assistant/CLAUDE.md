# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Office Assistant is a personal dashboard application for managing daily expenses, file uploads, and calendar events. The frontend is a vanilla JavaScript SPA with TailwindCSS, while the backend is a Python FastAPI server located in the sibling `nonprofit_finance_db` directory.

## Architecture

### Frontend Structure

- **Main Shell**: `index.html` with `js/app.js` - Single-page application with tabbed navigation
- **Component System**: Custom Web Components using Shadow DOM
  - `<category-picker>`: Hierarchical category selection for expense categorization
  - `<upload-component>`: PDF bank statement upload interface
  - Calendar component: Class-based module in `js/components/calendar.js`
- **Event System**: Global event bus in `js/event-bus.js` for component communication
- **No Build Step**: Uses browser-native ES modules and TailwindCSS CDN

### Backend Integration

The frontend connects to a FastAPI server (`api_server.py`) in `/home/adamsl/planner/nonprofit_finance_db`:

- **Expense Data API**: Fetches transactions from MySQL database
- **Category Taxonomy**: Hierarchical categories stored in database, exposed via `/api/categories`
- **PDF Import Pipeline**: Processes bank statements using docling PDF extraction

### Data Flow

1. Transactions stored in MySQL database (`nonprofit_finance_db`)
2. API server exposes transaction data and category taxonomy
3. Frontend fetches data via `/api/` endpoints
4. Changes persist back to database via API
5. Local data files in `data/` directory are sample/fallback data only

## Running the Application

### Start the Backend Server

```bash
cd /home/adamsl/planner/nonprofit_finance_db
source venv/bin/activate
python3 api_server.py
```

Or use the convenience script from the office-assistant directory:

```bash
./start_server.sh
```

The API server runs on `http://localhost:8000` and serves:
- API endpoints at `/api/*`
- Office Assistant frontend at `/` (root)
- Legacy category picker at `/ui`

### Development Workflow

The application is designed for simple file editing without a build step. Just edit files and refresh the browser.

For TypeScript components (in `upload-component/`):

```bash
cd upload-component
npx tsc
```

This compiles TypeScript to `js/upload-component.js`.

## Key Conventions

### Component Communication

Components use a global event bus pattern:

```javascript
import { emit, on } from "./event-bus.js";

// Emit events
emit('category:selected', { categoryId: 123, transactionId: 456 });

// Listen for events
on('category:selected', (data) => { /* handle */ });
```

### Data Attributes for Styling

Uses Tailwind's `data-[attribute]` selectors for state-based styling:

```html
<button data-active="true" class="data-[active=true]:bg-blue-600">
```

### LocalStorage for Client State

- Calendar events: `localStorage.getItem('calendar_events')`
- Component maintains its own state persistence

### Category Taxonomy Structure

Categories are hierarchical with `parent_id` references:

```json
{ "id": 200, "name": "Housing", "parent_id": null }
{ "id": 203, "name": "Utilities", "parent_id": 200 }
{ "id": 204, "name": "Water", "parent_id": 203 }
```

Full path displayed as: "Housing / Utilities / Water"

## Important File Locations

- **API Server**: `/home/adamsl/planner/nonprofit_finance_db/api_server.py`
- **Database Config**: `/home/adamsl/planner/nonprofit_finance_db/app/config.py`
- **Ingestion Pipeline**: `/home/adamsl/planner/nonprofit_finance_db/ingestion/pipeline.py`
- **PDF Parser**: `/home/adamsl/planner/nonprofit_finance_db/parsers/pdf_parser.py`

## Component Details

### CategoryPicker Web Component

- Form-associated custom element
- Cascading select behavior (single `<select>` repopulated at each level)
- Turns green (`data-state="done"`) when leaf category selected
- Emits `category:selected` event via event bus
- Attributes: `name`, `data-src`, `expense-id`, `placeholder`

### Upload Component

- Lists recent PDF downloads from Downloads folder
- Radio button selection for file import
- Integrates with backend `/api/recent-downloads` and `/api/import-pdf`
- Shows loading spinner during processing
- Emits events: `upload:file-selected`, `upload:complete`, `upload:error`

### Calendar Component

- Class-based component (`window.calendar = new Calendar()`)
- Three view modes: month, week (not implemented), day
- Event types: meeting (blue), deadline (red), task (green)
- Persists to localStorage
- Modal dialogs for add/edit events

## Testing the Frontend

Open `index.html` in a browser (preferably with the API server running):

- Expense Categorizer tab loads `daily_expense_categorizer.html` in iframe
- Upload tab loads `upload_pdf_statements.html` in iframe
- Calendar tab renders the Calendar component directly

For standalone testing:
- `test-calendar.html` - Calendar component tests
- `test-upload-component.html` - Upload component tests
- Various `*-test.html` files for debugging specific features

## Notes

- No bundler or build process for main application (vanilla JS + ES modules)
- TailwindCSS loaded via CDN (no PostCSS needed)
- Shadow DOM isolates component styles
- Backend server handles CORS for local development
- MySQL connection details in backend config (not in this repo)
