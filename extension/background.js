const DEFAULT_API_BASE = 'http://localhost:3000/api/v1/extension';

chrome.runtime.onInstalled.addListener(() => {
  chrome.storage.local.set({ apiBaseUrl: DEFAULT_API_BASE });
  console.log('[VerifAI Extension] Installed successfully');
});

// Listener for content script & popup requests
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === 'CAPTURE_TEXT') {
    handleCapture(request.payload).then(sendResponse);
    return true;
  }

  if (request.action === 'VERIFY_TEXT') {
    handleVerify(request.payload).then(sendResponse);
    return true;
  }

  if (request.action === 'REPORT_FAILURE') {
    handleReportFailure(request.payload).then(sendResponse);
    return true;
  }

  if (request.action === 'FETCH_CONFIG') {
    fetchConfig().then(sendResponse);
    return true;
  }
});

async function getApiBase() {
  const store = await chrome.storage.local.get(['apiBaseUrl']);
  return store.apiBaseUrl || DEFAULT_API_BASE;
}

async function handleCapture(payload) {
  try {
    const apiBase = await getApiBase();
    const res = await fetch(`${apiBase}/capture`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    const data = await res.json();
    return data;
  } catch (err) {
    return { status: 'error', message: err.message || 'Capture failed' };
  }
}

async function handleVerify(payload) {
  try {
    const apiBase = await getApiBase();
    const res = await fetch(`${apiBase}/verify`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    const data = await res.json();
    return data;
  } catch (err) {
    return { status: 'error', message: err.message || 'Verification failed' };
  }
}

async function handleReportFailure(payload) {
  try {
    const apiBase = await getApiBase();
    const res = await fetch(`${apiBase}/report`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });
    return await res.json();
  } catch (err) {
    return { status: 'error', message: err.message };
  }
}

async function fetchConfig() {
  try {
    const apiBase = await getApiBase();
    const res = await fetch(`${apiBase}/config`);
    return await res.json();
  } catch (err) {
    return { status: 'error', message: 'Offline config fallback' };
  }
}
