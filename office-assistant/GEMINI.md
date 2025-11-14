# Project Overview

This project is a web application called "Office Assistant". It seems to be designed as a dashboard for a freelancer or small business to manage their administrative tasks. The application is built with HTML, CSS, and vanilla JavaScript, using Tailwind CSS for styling.

The main features are:

*   **Expense Categorizer**: Allows users to categorize their daily expenses. It fetches transaction data from a local API and allows the user to assign categories to each transaction.
*   **PDF Statement Upload**: Provides a feature to upload PDF bank statements to extract and categorize transactions.
*   **Calendar**: A simple calendar to manage events.

The application is structured as a single-page application, but it loads different sections into iframes. It uses a local API for data, with a fallback to static JSON files (`data/transactions.json`, `data/categories.json`).

# Building and Running

There are no explicit build instructions in the project. The application can be run by opening the `index.html` file in a web browser. However, for the application to work correctly, a local web server is needed to serve the files and the API.

The `daily_expense_categorizer.html` file suggests that the API is expected to be running on `http://localhost:8080/api`.

A simple way to run the application is to use a static file server. For example, using Python's built-in HTTP server:

```bash
python3 -m http.server
```

Then, open `http://localhost:8000` in your browser.

To run the API, you would need to start the API server separately. The `start_server.sh` file might contain the command to start the API server.

# Development Conventions

*   The project uses vanilla JavaScript.
*   It uses Tailwind CSS for styling.
*   The application is structured into components (e.g., `calendar.js`, `upload-component.js`).
*   The application uses an event bus for communication between components (`js/event-bus.js`).
*   The application uses a local API for data, with a fallback to static JSON files.
*   The code is not bundled or transpiled.
