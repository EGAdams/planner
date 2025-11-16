# Chat → Gemini Browser Extension Plan
https://chatgpt.com/c/691a0848-2cfc-832f-8cbd-f2bf334ba931
---
**Goal:** Make it one-click easy to send a ChatGPT conversation from your browser into the `gemini` CLI (running on your machine) without copy–pasting text by hand.

This document is written so your engineers can **follow it step-by-step** without needing to design anything. They just need to:

1. Create the folder structure shown below.
2. Copy the code blocks into the matching files.
3. Install dependencies.
4. Run the local Python bridge.
5. Load the extension in Chrome/Brave and click the icon on any ChatGPT chat.

> ⚠️ **Important:** This is for your **own chats** and personal use. Make sure use of this extension follows the website’s Terms of Use.

---

## 1. Project Structure

Create a new folder for this project anywhere you like, for example:

```text
chat-to-gemini-extension/
├─ README.md                  # This file
├─ extension/                 # Chrome/Brave extension source
│  ├─ manifest.json
│  ├─ background.js
│  ├─ content-script.js
│  └─ icons/
│     ├─ icon16.png
│     ├─ icon32.png
│     ├─ icon48.png
│     └─ icon128.png
└─ local_bridge/              # Local HTTP → gemini CLI bridge
   ├─ bridge.py
   ├─ requirements.txt
   └─ README_LOCAL_BRIDGE.md
```

Your engineers should literally create **these folders and files** and then **copy the code** from the sections below into the correct files.

---

## 2. High-Level Architecture

```text
+-----------------------+         HTTP POST           +-----------------------+
|   Browser (ChatGPT)   |  ----------------------->   |   Local Python Bridge |
|   - Chat page         |                             |   - bridge.py         |
|   - Chat DOM          |                             |   - calls `gemini`    |
+-----------+-----------+                             +-----------+-----------+
            |                                                         |
            | Extension: content-script.js                            |
            |   - Extracts chat text                                  |
            v                                                         v
+-----------------------+                               +---------------------+
|   background.js       |  <---- JSON result ---------- |   `gemini` CLI      |
|   - Sends text to     |                               +---------------------+
|     local bridge      |
|   - Shows notification|
+-----------------------+
```

Workflow:

1. You open a ChatGPT/ChatGPT.com conversation in your browser.
2. You click the extension icon.
3. The extension’s **content script** extracts all visible chat messages into a transcript string.
4. The **background script** sends this transcript to `http://127.0.0.1:8765/analyze`.
5. The **local Python bridge** calls `gemini -y "What is this chat about?\n\n<transcript>"`.
6. The bridge returns the CLI’s output to the extension.
7. The extension shows you the result (notification + console log).

You only need to manually tweak the **DOM selectors** in `content-script.js` to match the ChatGPT page structure.

---

## 3. Extension Code (folder: `extension/`)

### 3.1 `manifest.json`

Create `extension/manifest.json` and paste this:

```json
{
  "manifest_version": 3,
  "name": "Chat → Gemini Bridge",
  "description": "Extract current ChatGPT chat and send it to the local gemini CLI for analysis.",
  "version": "0.1.0",
  "permissions": [
    "scripting",
    "activeTab",
    "notifications"
  ],
  "host_permissions": [
    "https://chatgpt.com/*",
    "https://chat.openai.com/*",
    "http://127.0.0.1/*"
  ],
  "background": {
    "service_worker": "background.js"
  },
  "action": {
    "default_title": "Summarize this chat with Gemini"
  },
  "icons": {
    "16": "icons/icon16.png",
    "32": "icons/icon32.png",
    "48": "icons/icon48.png",
    "128": "icons/icon128.png"
  },
  "content_scripts": [
    {
      "matches": [
        "https://chatgpt.com/*",
        "https://chat.openai.com/*"
      ],
      "js": ["content-script.js"],
      "run_at": "document_idle"
    }
  ]
}
```

> ✅ This tells Chrome:
> - Use `background.js` as a service worker.
> - Inject `content-script.js` on ChatGPT pages.
> - Allow the extension to talk to `http://127.0.0.1/*` (your local bridge).

---

### 3.2 `background.js`

Create `extension/background.js` and paste this:

```js
// background.js (service worker for the extension)

// When the user clicks the extension icon in the toolbar
chrome.action.onClicked.addListener((tab) => {
  if (!tab.id) {
    console.error("No active tab id found.");
    return;
  }

  // Ask the content script in the current tab to extract the chat
  chrome.tabs.sendMessage(tab.id, { type: "EXTRACT_CHAT" }, (response) => {
    if (chrome.runtime.lastError) {
      console.warn("Error sending message to content script:", chrome.runtime.lastError.message);
    } else {
      console.log("EXTRACT_CHAT message sent to content script.");
    }
  });
});

// Listen for messages from the content script
chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  if (msg.type === "CHAT_TRANSCRIPT") {
    const transcript = msg.transcript || "";

    console.log("Received transcript from content script. Length:", transcript.length);

    // Send transcript to local Python bridge
    fetch("http://127.0.0.1:8765/analyze", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text: transcript })
    })
      .then((r) => r.json())
      .then((data) => {
        const output = data.output || "(No output from gemini CLI)";
        const error = data.error || "";
        const code = data.returncode;

        console.log("Gemini CLI output:", output);
        if (error) {
          console.error("Gemini CLI error:", error);
        }

        // Show a notification with a truncated result
        const message = output.slice(0, 500) + (output.length > 500 ? "..." : "");

        chrome.notifications.create({
          type: "basic",
          iconUrl: "icons/icon128.png",
          title: "Gemini Summary",
          message: message || "No summary text returned."
        });

        sendResponse({ ok: true, output, error, code });
      })
      .catch((err) => {
        console.error("Error talking to local bridge:", err);
        chrome.notifications.create({
          type: "basic",
          iconUrl: "icons/icon128.png",
          title: "Gemini Summary Error",
          message: "Could not reach local bridge at http://127.0.0.1:8765/analyze"
        });
        sendResponse({ ok: false, error: String(err) });
      });

    // Indicate we will respond asynchronously
    return true;
  }

  // For other messages, do nothing special
  return false;
});
```

> ✅ Summary: Background script waits for the toolbar icon click, asks the content script for the transcript, sends it to the local bridge, and shows a notification with the summary.

---

### 3.3 `content-script.js`

Create `extension/content-script.js` and paste this:

```js
// content-script.js
// Runs on chatgpt.com / chat.openai.com pages.
// Responsible for reading the chat DOM and building a text transcript.

/**
 * TODO: You MUST tweak this function for the actual ChatGPT DOM.
 * Use Chrome DevTools on a chat page and inspect the elements that contain
 * each message. Update the selectors accordingly.
 */
function extractMessagesFromPage() {
  const messages = [];

  // EXAMPLE SELECTORS ONLY – LIKELY NEED CHANGES.
  // 1. Find all message containers (user + assistant).
  //    Open DevTools, right-click on a chat message, "Inspect", and note its classes / attributes.
  const messageNodes = document.querySelectorAll("[data-message-author-role]");

  messageNodes.forEach((node) => {
    const role = node.getAttribute("data-message-author-role") || "unknown";

    // This is just a safe fallback; you should narrow this down in DevTools.
    const text = node.innerText.trim();

    if (text.length === 0) {
      return;
    }

    messages.push({
      role,
      text
    });
  });

  return messages;
}

/**
 * Build a single plain-text transcript from the extracted messages.
 * Example format:
 *
 *   [user]
 *   Hello
 *
 *   [assistant]
 *   Hi, how can I help?
 */
function buildTranscript() {
  const messages = extractMessagesFromPage();

  if (!messages || messages.length === 0) {
    return "No messages found on this page. Please adjust the selectors in content-script.js.";
  }

  const lines = [];

  messages.forEach((msg) => {
    const roleLabel = msg.role.toUpperCase();
    lines.push("[" + roleLabel + "]");
    lines.push(msg.text);
    lines.push(""); // blank line between messages
  });

  return lines.join("\n");
}

// Listen for messages from background.js
chrome.runtime.onMessage.addListener((msg, sender, sendResponse) => {
  if (msg.type === "EXTRACT_CHAT") {
    try {
      const transcript = buildTranscript();
      console.log("Transcript built by content script:", transcript);

      chrome.runtime.sendMessage({
        type: "CHAT_TRANSCRIPT",
        transcript
      });

      sendResponse({ ok: true, length: transcript.length });
    } catch (err) {
      console.error("Error while building transcript:", err);
      sendResponse({ ok: false, error: String(err) });
    }

    return true;
  }

  return false;
});
```

> ❗ **VERY IMPORTANT:**  
> The only part you *must* customize is `extractMessagesFromPage()`.  
> The current selector `"[data-message-author-role]"` is an educated guess; if it doesn’t work, inspect the ChatGPT DOM and replace it with the correct selector(s).

For example, you might end up with something like:

```js
const messageNodes = document.querySelectorAll("div[data-message-author-role]");
// or
const messageNodes = document.querySelectorAll("div.group div.text-base");
```

depending on the current layout of the site.

---

### 3.4 `icons/`

Create the folder:

```text
extension/icons/
```

You need some PNG images for the extension icon. The file names must match `manifest.json`:

- `icon16.png`
- `icon32.png`
- `icon48.png`
- `icon128.png`

They can be any simple icons you like. (Engineers can quickly draw something in an image editor or use any placeholder PNGs.)

---

## 4. Local Python Bridge (folder: `local_bridge/`)

This small HTTP server runs on your machine and is responsible for:

1. Accepting the transcript from the browser (JSON).
2. Running the `gemini` CLI with that transcript.
3. Returning the CLI output to the extension as JSON.

### 4.1 `requirements.txt`

Create `local_bridge/requirements.txt`:

```text
Flask
```

If you want pinned versions, you can later run `pip freeze > requirements.txt`, but just `Flask` is enough for now.

---

### 4.2 `bridge.py`

Create `local_bridge/bridge.py` and paste this:

```python
'''
bridge.py - Local HTTP -> gemini CLI bridge

How it works:
- Listens on http://127.0.0.1:8765/analyze
- Expects JSON: { "text": "<chat transcript>" }
- Runs: gemini -y "What is this chat about?\\n\\n<transcript>"
- Returns JSON with CLI output.
'''

from flask import Flask, request, jsonify
import subprocess

app = Flask(__name__)

GEMINI_COMMAND = "gemini"  # Assumes `gemini` is on PATH in your virtualenv
DEFAULT_PROMPT_PREFIX = "What is this chat about?\n\n"


@app.post("/analyze")
def analyze():
  '''
  HTTP endpoint that receives the chat transcript and calls the gemini CLI.
  '''
  try:
    data = request.get_json(force=True) or {}
  except Exception as e:
    return jsonify({"error": f"Invalid JSON: {e}", "output": "", "returncode": -1}), 400

  text = data.get("text", "")

  if not isinstance(text, str):
    return jsonify({"error": "Field 'text' must be a string.", "output": "", "returncode": -1}), 400

  # Build the full prompt for gemini
  full_prompt = DEFAULT_PROMPT_PREFIX + text

  # Call: gemini -y "<full_prompt>"
  cmd = [GEMINI_COMMAND, "-y", full_prompt]

  try:
    result = subprocess.run(
      cmd,
      capture_output=True,
      text=True,
      check=False  # We handle non-zero return codes ourselves
    )
  except FileNotFoundError:
    return jsonify({
      "error": "Could not find 'gemini' CLI. Make sure it is installed and on PATH.",
      "output": "",
      "returncode": -1
    }), 500
  except Exception as e:
    return jsonify({
      "error": f"Error running gemini CLI: {e}",
      "output": "",
      "returncode": -1
    }), 500

  # Package result
  response_data = {
    "output": result.stdout or "",
    "error": result.stderr or "",
    "returncode": result.returncode
  }

  return jsonify(response_data)


if __name__ == "__main__":
  # Run the Flask app on localhost:8765
  # Use debug=False for simplicity & to avoid auto-reload complications
  app.run(host="127.0.0.1", port=8765, debug=False)
```

> ✅ Assumptions:
> - You already have the `gemini` CLI installed in your virtualenv or system PATH.
> - You will run `bridge.py` **inside the same environment** where `gemini` is available.

If you want a smarter prompt, you can edit `DEFAULT_PROMPT_PREFIX` to something like:

```python
DEFAULT_PROMPT_PREFIX = (
  "You are a helpful assistant. Summarize the following chat and explain its main topic, "
  "the key decisions, and any open questions.\n\n"
)
```

---

### 4.3 `README_LOCAL_BRIDGE.md`

Optional but recommended: Create `local_bridge/README_LOCAL_BRIDGE.md` so your team has a tiny local reference:

```markdown
# Local Bridge for Chat → Gemini Extension

This small HTTP server receives chat transcripts from the browser extension
and forwards them to the `gemini` CLI installed on this machine.

## Setup

1. Create and activate your virtualenv (if not already done):

   ```bash
   cd local_bridge
   python3 -m venv .venv
   source .venv/bin/activate  # or .venv\Scripts\activate on Windows
   ```

2. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

3. Make sure the `gemini` CLI is installed and available in this virtualenv.

4. Run the server:

   ```bash
   python bridge.py
   ```

   It will listen on: `http://127.0.0.1:8765/analyze`

5. Leave this server running while you use the browser extension.
```

---

## 5. How to Install & Use the Extension

This is the **exact sequence** your engineers should follow.

### 5.1 Prepare the local bridge

1. Open a terminal.
2. Navigate to the `local_bridge` folder:

   ```bash
   cd /path/to/chat-to-gemini-extension/local_bridge
   ```

3. Create a virtualenv (optional but recommended):

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

4. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

5. Ensure `gemini` CLI works in this shell:

   ```bash
   gemini -h
   ```

   If this prints the help text, you’re good.

6. Start the bridge server:

   ```bash
   python bridge.py
   ```

   Leave this running. It should log something like:

   ```text
   * Serving Flask app 'bridge'
   * Running on http://127.0.0.1:8765
   ```

### 5.2 Load the extension in Chrome/Brave

1. Open Chrome or Brave.
2. Go to: `chrome://extensions/`
3. Turn on **Developer mode** (toggle in the top-right corner).
4. Click **“Load unpacked”**.
5. Select the `extension` folder inside your project:

   ```text
   /path/to/chat-to-gemini-extension/extension
   ```

6. You should now see **“Chat → Gemini Bridge”** listed as an installed extension.

### 5.3 Using the extension

1. Open a ChatGPT conversation (on `https://chatgpt.com/` or `https://chat.openai.com/`).
2. Click the extension icon in the browser toolbar (pin it if necessary).
3. The extension will:
   - Ask the content script to extract the transcript.
   - Send the transcript to the local bridge.
   - The bridge calls `gemini` CLI.
   - A notification appears with the summarized result.

4. If you don’t see meaningful output, check:

   - The DevTools Console for any errors (`background.js` logs).
   - The terminal running `bridge.py` for any error messages.
   - The DOM selectors in `content-script.js` and adjust them.

---

## 6. Tweaking the DOM Selectors (The Only “Smart” Part)

Your engineers only need to do **one small piece of investigation**:

1. Open a ChatGPT chat in Chrome.
2. Right-click on a user or assistant message → **Inspect**.
3. Look at the HTML structure surrounding that message:
   - Find a tag that repeats for **each** message (e.g. `div` with a specific class or attribute).
4. Change this line in `content-script.js`:

   ```js
   const messageNodes = document.querySelectorAll("[data-message-author-role]");
   ```

   to something that matches your DOM, for example:

   ```js
   const messageNodes = document.querySelectorAll("div[data-message-author-role]");
   // or
   const messageNodes = document.querySelectorAll("div.group div.text-base");
   ```

5. Inside the loop, you can further refine how the text is extracted, e.g.:

   ```js
   const textElement = node.querySelector(".your-message-text-selector") || node;
   const text = textElement.innerText.trim();
   ```

6. Refresh the ChatGPT page (or disable/enable the extension) after changes.

Once the selector finds the right nodes, the rest of the system should **just work**.

---

## 7. Summary for Your Team

- **You do NOT need a proxy.** The extension bypasses the 403 issue by using your logged-in browser session and sending **plain text**, not URLs, to `gemini`.
- All the design work is done here:
  - Folder structure is defined.
  - Manifest and JavaScript are provided.
  - Python bridge is provided.
- The **only customization** required is the message selectors in `content-script.js`.

If you keep this structure and just follow the steps in order, your team should be able to get a working prototype without needing to redesign anything.
