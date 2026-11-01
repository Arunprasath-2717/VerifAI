# VerifAI — Chrome Extension (Manifest V3)

The **VerifAI Chrome Extension** integrates directly with popular AI web interfaces (such as ChatGPT, Anthropic Claude, Google Gemini, and Perplexity) and general web pages to capture AI-generated responses and verify factual consistency against independent evidence using the VerifAI backend.

---

## 1. Features

- **DOM Auto-Detection:** Automatically extracts completed assistant responses from ChatGPT (`data-message-author-role="assistant"`), Claude (`font-claude-message`), Gemini (`model-response`), and article elements.
- **User Selection Capture:** Highlight any sentence or paragraph on any web page to verify specific claims.
- **Context Menu Integration:** Right-click highlighted text and select **"Verify with VerifAI"**.
- **Real-Time Verification:** Dispatches structured ingestion payloads to the backend `POST /api/v1/ingest` endpoint.
- **Explainable Verdicts:** Displays aggregate trust score, claim breakdown (Supported, Contradicted, Unknown, Non-Factual), and evidence citations.
- **Live Search Toggle:** Optionally enables real-time search fallback when local evidence indices lack coverage.

---

## 2. Installation & Loading Instructions

1. Start the VerifAI backend on `http://localhost:8000`:
   ```bash
   cd /home/arun/Desktop/VerifAI/VerifAI
   source .venv/bin/activate
   uvicorn app.main:app --host 127.0.0.1 --port 8000
   ```
2. Open Google Chrome or any Chromium-based browser (Brave, Edge).
3. Navigate to:
   ```text
   chrome://extensions/
   ```
4. Enable **Developer mode** (toggle in the top-right corner).
5. Click **Load unpacked** in the top-left corner.
6. Select the `extension/` directory:
   ```text
   /home/arun/Desktop/VerifAI/VerifAI/extension
   ```
7. Pin the **VerifAI** extension to your browser toolbar.

---

## 3. Usage Guide

1. Open any webpage containing AI-generated text (e.g., ChatGPT, Claude, Gemini, or a news article).
2. Click the **VerifAI** extension icon in the toolbar.
3. Click **Auto-Capture** to grab the latest AI answer, or highlight text on the page and open the extension.
4. Click **Verify with VerifAI**.
5. Inspect the resulting trust score, claim breakdown, and evidence provenance.

---

## 4. Architecture & Security

- **Manifest Version:** 3
- **Network Boundary:** Connects only to `http://localhost:8000/*` and `http://127.0.0.1:8000/*`.
- **SSRF Hardening:** Source URLs submitted by the extension are validated against private, link-local, and cloud metadata network ranges by the backend.
- **Zero Token Tracking:** No user credentials or API keys are stored in the extension.
