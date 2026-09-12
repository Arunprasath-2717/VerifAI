document.addEventListener('DOMContentLoaded', async () => {
  // Navigation Tabs
  const tabVerifyBtn = document.getElementById('tab-verify-btn');
  const tabConfigBtn = document.getElementById('tab-config-btn');
  const tabReportBtn = document.getElementById('tab-report-btn');

  const tabVerify = document.getElementById('tab-verify');
  const tabConfig = document.getElementById('tab-config');
  const tabReport = document.getElementById('tab-report');

  const textToVerify = document.getElementById('text-to-verify');
  const captureSourceInfo = document.getElementById('capture-source-info');

  const btnVerify = document.getElementById('btn-verify');
  const btnVerifyStream = document.getElementById('btn-verify-stream');
  const streamProgress = document.getElementById('stream-progress');
  const streamStatusText = document.getElementById('stream-status-text');

  const resultCard = document.getElementById('result-card');
  const resVerdict = document.getElementById('res-verdict');
  const resTrust = document.getElementById('res-trust');
  const resId = document.getElementById('res-id');
  const resSummary = document.getElementById('res-summary');
  const claimsContainer = document.getElementById('claims-container');

  const btnSaveConfig = document.getElementById('btn-save-config');
  const cfgEndpoint = document.getElementById('cfg-endpoint');
  const configStatus = document.getElementById('config-status');

  const btnSendReport = document.getElementById('btn-send-report');
  const repReason = document.getElementById('rep-reason');
  const repNote = document.getElementById('rep-note');
  const reportStatus = document.getElementById('report-status');

  // Switch Tabs
  tabVerifyBtn.addEventListener('click', () => switchTab(tabVerifyBtn, tabVerify));
  tabConfigBtn.addEventListener('click', () => switchTab(tabConfigBtn, tabConfig));
  tabReportBtn.addEventListener('click', () => switchTab(tabReportBtn, tabReport));

  function switchTab(btn, content) {
    document.querySelectorAll('.tab-btn').forEach((b) => b.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach((c) => c.classList.remove('active'));
    btn.classList.add('active');
    content.classList.add('active');
  }

  // Load storage captured content
  const store = await chrome.storage.local.get(['selectedText', 'autoCapturedText', 'apiBaseUrl']);
  if (store.apiBaseUrl) cfgEndpoint.value = store.apiBaseUrl;

  if (store.selectedText) {
    textToVerify.value = store.selectedText;
    captureSourceInfo.textContent = 'Source: Manual Highlighted Selection';
  } else if (store.autoCapturedText) {
    textToVerify.value = store.autoCapturedText;
    captureSourceInfo.textContent = 'Source: Automatic AI Response Capture';
  }

  // Verification Handler
  btnVerify.addEventListener('click', async () => {
    const text = textToVerify.value.trim();
    if (!text) {
      alert('Please select or paste content to verify.');
      return;
    }

    btnVerify.disabled = true;
    btnVerify.textContent = 'Verifying...';
    resultCard.classList.add('hidden');

    try {
      const response = await chrome.runtime.sendMessage({
        action: 'VERIFY_TEXT',
        payload: {
          text,
          source_app: 'extension_popup',
        },
      });

      if (response && response.status === 'success') {
        renderResult(response.data.verification, response.data.claims);
      } else {
        alert(response?.message || 'Verification failed');
      }
    } catch (err) {
      alert(`Error verifying: ${err.message}`);
    } finally {
      btnVerify.disabled = false;
      btnVerify.textContent = 'Verify Selection';
    }
  });

  // Streaming Verification Handler
  btnVerifyStream.addEventListener('click', async () => {
    const text = textToVerify.value.trim();
    if (!text) {
      alert('Please select or paste content to verify.');
      return;
    }

    btnVerifyStream.disabled = true;
    streamProgress.classList.remove('hidden');
    resultCard.classList.add('hidden');
    streamStatusText.textContent = 'Connecting to Arun Core stream...';

    try {
      const apiBase = cfgEndpoint.value.trim() || 'http://localhost:3000/api/v1/extension';
      const response = await fetch(`${apiBase}/verify/stream`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text }),
      });

      if (!response.ok || !response.body) {
        throw new Error('Streaming verification failed');
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        const chunkStr = decoder.decode(value);
        const lines = chunkStr.split('\n\n');

        for (const line of lines) {
          if (!line.startsWith('data: ')) continue;
          const dataStr = line.replace('data: ', '').trim();

          if (dataStr === '[DONE]') break;

          try {
            const payload = JSON.parse(dataStr);
            if (payload.message) streamStatusText.textContent = payload.message;

            if (payload.step === 'COMPLETED' && payload.verification) {
              renderResult(payload.verification, payload.claims || []);
            }
          } catch {
            // ignore line parse issues
          }
        }
      }
    } catch (err) {
      alert(`Streaming error: ${err.message}`);
    } finally {
      streamProgress.classList.add('hidden');
      btnVerifyStream.disabled = false;
    }
  });

  function renderResult(verification, claims = []) {
    resultCard.classList.remove('hidden');
    resVerdict.textContent = verification.verdict;
    resTrust.textContent = `${verification.trust_score}% Trust`;
    resId.textContent = `Arun ID: ${verification.verification_id}`;
    resSummary.textContent = verification.summary || 'Verified against core knowledge sources.';

    claimsContainer.innerHTML = '';
    if (claims.length === 0) {
      claimsContainer.innerHTML = `<div class="claim-item">No explicit claims extracted.</div>`;
    } else {
      claims.forEach((c) => {
        const div = document.createElement('div');
        div.className = 'claim-item';
        div.innerHTML = `<strong>${c.verdict}:</strong> ${c.text}`;
        claimsContainer.appendChild(div);
      });
    }
  }

  // Save Config
  btnSaveConfig.addEventListener('click', async () => {
    const url = cfgEndpoint.value.trim();
    await chrome.storage.local.set({ apiBaseUrl: url });
    configStatus.textContent = 'Settings saved successfully!';
    setTimeout(() => (configStatus.textContent = ''), 2500);
  });

  // Report Capture Failure
  btnSendReport.addEventListener('click', async () => {
    btnSendReport.disabled = true;
    reportStatus.textContent = 'Submitting report...';

    const storeData = await chrome.storage.local.get(['pageUrl', 'pageTitle']);

    try {
      const response = await chrome.runtime.sendMessage({
        action: 'REPORT_FAILURE',
        payload: {
          reason: repReason.value,
          user_note: repNote.value,
          url: storeData.pageUrl || 'Browser page',
          page_title: storeData.pageTitle || 'Web page',
          timestamp: new Date().toISOString(),
        },
      });

      if (response && response.status === 'success') {
        reportStatus.textContent = 'Failure report logged! Manual selection is available.';
        repNote.value = '';
      } else {
        reportStatus.textContent = 'Failed to submit report.';
      }
    } catch (err) {
      reportStatus.textContent = 'Error submitting report.';
    } finally {
      btnSendReport.disabled = false;
      setTimeout(() => (reportStatus.textContent = ''), 3000);
    }
  });
});
