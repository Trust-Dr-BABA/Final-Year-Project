# Browser Extension Setup Guide

This guide explains how to install the browser extension in Google Chrome or any Chromium-based browser (such as Microsoft Edge or Brave) in Developer Mode.

## Prerequisites

* Google Chrome, Microsoft Edge, or another Chromium-based browser
* The browser extension source code

## Installation Steps

### Google Chrome

1. Open Chrome.
2. Navigate to:

   ```
   chrome://extensions/
   ```
3. Enable **Developer mode** using the toggle in the top-right corner.
4. Click **Load unpacked**.
5. Browse to the browser extension folder in this project.
6. Select the folder and click **Select Folder**.
7. The extension will now appear in the Extensions page and is ready to use.

### Microsoft Edge

1. Open Edge.
2. Navigate to:

   ```
   edge://extensions/
   ```
3. Enable **Developer mode**.
4. Click **Load unpacked**.
5. Select the browser extension folder.
6. The extension will be installed successfully.

## Updating the Extension

After making changes to the extension:

1. Save your changes.
2. Open the Extensions page.
3. Click the **Reload** (↻) button on the installed extension.
4. Refresh any browser tabs where you want to test the updated extension.

## Removing the Extension

1. Open the browser's Extensions page.
2. Locate the installed extension.
3. Click **Remove**.
4. Confirm the removal.

## Troubleshooting

* Ensure **Developer mode** is enabled.
* Verify that the selected folder contains the `manifest.json` file.
* If changes are not visible, click **Reload** on the extension and refresh the webpage.
* Check the browser's extension error logs for any reported issues.

## Project Structure

```
browser-extension/
├── manifest.json
├── popup.html
├── popup.js
├── background.js
├── content.js
├── icons/
└── ...
```

> **Note:** Always load the folder that contains the `manifest.json` file. Loading the wrong folder will cause the browser to reject the extension.
