/**
 * VerifAI Chrome Extension - Content Script
 * Captures selected text or auto-detects AI response containers on active web pages.
 */

(() => {
  // Selector heuristics for common LLM web interfaces
  const AI_CONTAINER_SELECTORS = [
    // OpenAI ChatGPT
    '[data-message-author-role="assistant"] .markdown',
    '[data-message-author-role="assistant"]',
    '.agent-turn .markdown',
    // Anthropic Claude
    '.font-claude-message',
    '[data-is-streaming="false"] .grid',
    // Google Gemini
    'model-response .response-content',
    'model-response',
    '.model-response-text',
    // Microsoft Copilot
    '.cib-message-main',
    // Perplexity
    '.prose.dark\\:prose-invert',
    // Generic fallback
    'article',
    'main'
  ];

  function detectModelFromPage() {
    const host = window.location.hostname.toLowerCase();
    if (host.includes("chatgpt.com") || host.includes("openai.com")) {
      return "chatgpt-auto";
    }
    if (host.includes("claude.ai") || host.includes("anthropic.com")) {
      return "claude-auto";
    }
    if (host.includes("gemini.google.com")) {
      return "gemini-auto";
    }
    if (host.includes("perplexity.ai")) {
      return "perplexity-auto";
    }
    if (host.includes("deepseek.com")) {
      return "deepseek-auto";
    }
    return "web-capture";
  }

  function extractDetectedText() {
    // 1. Prioritize active user selection
    const selection = window.getSelection()?.toString().trim();
    if (selection && selection.length > 5) {
      return {
        text: selection,
        method: "user_selection",
        url: window.location.href,
        model: detectModelFromPage(),
      };
    }

    // 2. Look for AI assistant message containers
    for (const selector of AI_CONTAINER_SELECTORS) {
      try {
        const elements = document.querySelectorAll(selector);
        if (elements.length > 0) {
          // Select the latest completed assistant message
          const latestElement = elements[elements.length - 1];
          const text = latestElement.innerText?.trim();
          if (text && text.length > 15) {
            return {
              text: text,
              method: `auto_detected:${selector}`,
              url: window.location.href,
              model: detectModelFromPage(),
            };
          }
        }
      } catch (err) {
        // Selector syntax error on edge browsers, continue
      }
    }

    return {
      text: "",
      method: "none",
      url: window.location.href,
      model: detectModelFromPage(),
    };
  }

  // Listen for extraction requests from popup or background script
  chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === "GET_PAGE_TEXT") {
      const result = extractDetectedText();
      sendResponse(result);
    }
    return true;
  });
})();
