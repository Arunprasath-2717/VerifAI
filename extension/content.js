// Content script for VerifAI Chrome Extension
(function () {
  let floatingBtn = null;
  let selectedText = '';

  // Initialize Floating Selection Button
  function createFloatingButton() {
    if (floatingBtn) return;
    floatingBtn = document.createElement('div');
    floatingBtn.id = 'verifai-floating-verify-btn';
    floatingBtn.innerHTML = `
      <div class="verifai-btn-content">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
        </svg>
        <span>Verify with VerifAI</span>
      </div>
    `;
    floatingBtn.style.display = 'none';
    document.body.appendChild(floatingBtn);

    floatingBtn.addEventListener('click', onFloatingBtnClick);
  }

  // Handle Manual Selection
  document.addEventListener('mouseup', (e) => {
    const selection = window.getSelection();
    const text = selection ? selection.toString().trim() : '';

    if (text.length >= 10 && !isClickInsideFloatingBtn(e)) {
      selectedText = text;
      const range = selection.getRangeAt(0);
      const rect = range.getBoundingClientRect();

      createFloatingButton();
      floatingBtn.style.left = `${window.scrollX + rect.left + rect.width / 2 - 60}px`;
      floatingBtn.style.top = `${window.scrollY + rect.bottom + 8}px`;
      floatingBtn.style.display = 'block';

      // Save selected text to storage for popup accessibility
      chrome.storage.local.set({
        selectedText: text,
        pageUrl: window.location.href,
        pageTitle: document.title,
      });
    } else if (!isClickInsideFloatingBtn(e)) {
      if (floatingBtn) floatingBtn.style.display = 'none';
    }
  });

  function isClickInsideFloatingBtn(e) {
    return floatingBtn && floatingBtn.contains(e.target);
  }

  async function onFloatingBtnClick(e) {
    e.stopPropagation();
    if (!selectedText) return;

    floatingBtn.innerHTML = `<span>Verifying...</span>`;

    try {
      const response = await chrome.runtime.sendMessage({
        action: 'VERIFY_TEXT',
        payload: {
          text: selectedText,
          url: window.location.href,
          page_title: document.title,
          source_app: 'manual_selection',
        },
      });

      if (response && response.status === 'success') {
        const verif = response.data.verification;
        alert(
          `VerifAI Verification Complete!\n\nVerdict: ${verif.verdict}\nTrust Score: ${verif.trust_score}%\nVerification ID: ${verif.verification_id}`
        );
      } else {
        alert(`Verification notice: ${response?.message || 'Check extension popup'}`);
      }
    } catch (err) {
      alert(`Error verifying selection: ${err.message}`);
    } finally {
      if (floatingBtn) {
        floatingBtn.style.display = 'none';
        floatingBtn.innerHTML = `
          <div class="verifai-btn-content">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
            </svg>
            <span>Verify with VerifAI</span>
          </div>
        `;
      }
    }
  }

  // Automatic Capture Attempt for known AI Assistant interfaces
  function attemptAutoCapture() {
    const aiSelectors = [
      '[data-message-author-role="assistant"]',
      '.agent-turn',
      '.markdown.prose',
      '.chat-response',
    ];

    let capturedContent = null;
    let targetSelector = null;

    for (const sel of aiSelectors) {
      const el = document.querySelector(sel);
      if (el && el.textContent && el.textContent.trim().length > 20) {
        capturedContent = el.textContent.trim();
        targetSelector = sel;
        break;
      }
    }

    if (capturedContent) {
      chrome.runtime.sendMessage({
        action: 'CAPTURE_TEXT',
        payload: {
          captured_text: capturedContent,
          url: window.location.href,
          page_title: document.title,
          source_app: 'auto_capture',
          selector: targetSelector,
        },
      });
      chrome.storage.local.set({ autoCapturedText: capturedContent });
    } else {
      // Auto capture failed - store metadata for failure report option
      chrome.storage.local.set({
        autoCaptureFailed: true,
        lastFailedUrl: window.location.href,
      });
    }
  }

  // Run auto capture once page reaches idle state
  setTimeout(attemptAutoCapture, 1500);
})();
