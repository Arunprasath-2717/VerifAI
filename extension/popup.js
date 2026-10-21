/**
 * VerifAI Chrome Extension - Popup Interaction Script
 * Connects browser capture to the VerifAI Ingestion & Verification API.
 */

const DEFAULT_BACKEND_URL = "http://localhost:8000";
let API_BASE_URL = `${DEFAULT_BACKEND_URL}/api/v1`;

// Non-factual content types map onto the existing neutral badge styles.
const NON_FACTUAL_BADGE_CLASS = {
  OPINION: "VIEWPOINT",
  CREATIVE: "CREATIVE",
  HYPOTHETICAL: "SCENARIO",
  PREDICTION: "FUTURE_LOOKING",
  INSTRUCTION: "VIEWPOINT",
};

function normalizeBackendUrl(raw) {
  const url = new URL(raw.trim());
  if (url.protocol !== "http:" && url.protocol !== "https:") {
    throw new Error("Backend URL must start with http:// or https://");
  }
  return url.origin;
}

document.addEventListener("DOMContentLoaded", async () => {
  const backendStatus = document.getElementById("backend-status");
  const backendStatusText = document.getElementById("backend-status-text");
  const inputText = document.getElementById("input-text");
  const selectModel = document.getElementById("select-model");
  const optLiveSearch = document.getElementById("opt-live-search");
  const inputApiKey = document.getElementById("input-api-key");
  const inputBackendUrl = document.getElementById("input-backend-url");
  const btnDetect = document.getElementById("btn-detect");
  const btnVerify = document.getElementById("btn-verify");
  const btnVerifyText = document.getElementById("btn-verify-text");
  const btnSpinner = document.getElementById("btn-spinner");
  const loadingContainer = document.getElementById("loading-container");
  const loadingStage = document.getElementById("loading-stage");
  const resultsCard = document.getElementById("results-card");
  const errorBanner = document.getElementById("error-banner");
  const errorMessage = document.getElementById("error-message");

  let currentSourceUrl = "";

  // 1. Health Check
  async function checkBackendHealth() {
    try {
      const resp = await fetch(`${API_BASE_URL}/health`, { method: "GET" });
      if (resp.ok) {
        backendStatus.className = "status-pill status-online";
        backendStatusText.textContent = "Engine Online";
      } else {
        throw new Error(`HTTP ${resp.status}`);
      }
    } catch (err) {
      backendStatus.className = "status-pill status-offline";
      backendStatusText.textContent = "Engine Offline";
      backendStatus.title = `Ensure VerifAI backend is running on ${API_BASE_URL.replace(/\/api\/v1$/, "")}`;
    }
  }

  // Backend URL is configurable; non-default origins need a runtime grant.
  async function applyBackendUrl(origin) {
    API_BASE_URL = `${origin}/api/v1`;
    inputBackendUrl.value = origin;
    await checkBackendHealth();
  }

  const stored = await new Promise((resolve) =>
    chrome.storage.local.get(["verifaiBackendUrl"], resolve)
  );
  await applyBackendUrl(stored.verifaiBackendUrl || DEFAULT_BACKEND_URL);

  inputBackendUrl.addEventListener("change", async () => {
    try {
      const origin = normalizeBackendUrl(inputBackendUrl.value || DEFAULT_BACKEND_URL);
      const granted = await chrome.permissions.request({ origins: [`${origin}/*`] });
      if (!granted) {
        showError(`Permission to reach ${origin} was not granted.`);
        return;
      }
      chrome.storage.local.set({ verifaiBackendUrl: origin });
      hideError();
      await applyBackendUrl(origin);
    } catch (err) {
      showError(err.message || "Invalid backend URL.");
    }
  });

  // API key is kept in extension-local storage and sent as X-API-Key.
  if (chrome.storage && chrome.storage.local) {
    chrome.storage.local.get(["verifaiApiKey"], (data) => {
      inputApiKey.value = data.verifaiApiKey || "";
    });
    inputApiKey.addEventListener("change", () => {
      chrome.storage.local.set({ verifaiApiKey: inputApiKey.value.trim() });
    });
  }

  // 2. Check for pending selection passed via context menu
  if (chrome.storage && chrome.storage.local) {
    chrome.storage.local.get(["pendingVerificationText", "pendingSourceUrl"], (data) => {
      if (data.pendingVerificationText) {
        inputText.value = data.pendingVerificationText;
        currentSourceUrl = data.pendingSourceUrl || "";
        chrome.storage.local.remove(["pendingVerificationText", "pendingSourceUrl"]);
      }
    });
  }

  // 3. Auto-Capture from Active Tab
  btnDetect.addEventListener("click", async () => {
    try {
      const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
      if (!tab || !tab.id) return;

      currentSourceUrl = tab.url || "";
      let response;
      try {
        // Injected only on demand; activeTab grants access to this tab only.
        const [injection] = await chrome.scripting.executeScript({
          target: { tabId: tab.id },
          files: ["content.js"],
        });
        response = injection && injection.result;
      } catch (injectErr) {
        showError("Cannot capture from this page. Make sure you are on an active webpage.");
        return;
      }

      if (response && response.text) {
        inputText.value = response.text;
        if (response.model && response.model !== "web-capture") {
          // Set model selector heuristic if detected
          for (let i = 0; i < selectModel.options.length; i++) {
            if (selectModel.options[i].value.includes(response.model.replace("-auto", ""))) {
              selectModel.selectedIndex = i;
              break;
            }
          }
        }
        hideError();
      } else {
        showError("No text selection or AI response found on page. Please select text first or paste directly.");
      }
    } catch (err) {
      showError("Auto-capture failed: " + err.message);
    }
  });

  // 4. Verify Handler
  btnVerify.addEventListener("click", async () => {
    const text = inputText.value.trim();
    if (!text) {
      showError("Please enter or capture text to verify.");
      return;
    }

    hideError();
    resultsCard.classList.add("hidden");
    loadingContainer.classList.remove("hidden");
    btnVerify.disabled = true;
    btnVerifyText.textContent = "Verifying...";
    btnSpinner.classList.remove("hidden");

    // Stage progression indicator
    const stages = [
      "Extracting atomic verifiable claims...",
      "Classifying content taxonomy (factual vs non-factual)...",
      "Retrieving verified knowledge passages...",
      "Executing multi-judge consensus and disagreement analysis...",
      "Aggregating trust score and audit record..."
    ];
    let stageIdx = 0;
    const interval = setInterval(() => {
      stageIdx = (stageIdx + 1) % stages.length;
      loadingStage.textContent = stages[stageIdx];
    }, 450);

    const modelVal = selectModel.value === "auto" ? null : selectModel.value;

    const payload = {
      text: text,
      source_url: currentSourceUrl || null,
      model_name: modelVal,
      source: "CHROME_EXTENSION",
      client_version: "1.0.0",
      capture_metadata: {
        timestamp: new Date().toISOString(),
        character_count: text.length,
      },
      options: {
        enable_live_search: optLiveSearch.checked,
        strict_consensus: true,
        max_claims: 20
      },
      verify_immediately: true
    };

    try {
      const headers = { "Content-Type": "application/json" };
      const apiKey = inputApiKey.value.trim();
      if (apiKey) {
        headers["X-API-Key"] = apiKey;
      }
      const res = await fetch(`${API_BASE_URL}/ingest`, {
        method: "POST",
        headers,
        body: JSON.stringify(payload)
      });

      clearInterval(interval);

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        const msg = errData?.error?.message || `Ingestion failed (HTTP ${res.status})`;
        throw new Error(msg);
      }

      const data = await res.json();
      renderResults(data);
    } catch (err) {
      clearInterval(interval);
      showError(err.message || "Failed to communicate with VerifAI verification engine.");
    } finally {
      loadingContainer.classList.add("hidden");
      btnVerify.disabled = false;
      btnVerifyText.textContent = "Verify with VerifAI";
      btnSpinner.classList.add("hidden");
    }
  });

  function renderResults(data) {
    const ver = data.verification;
    if (!ver) {
      showError("Payload ingested, but verification result was not returned.");
      return;
    }

    // Trust Score (backend returns percentage 0.0 to 100.0)
    const trustScoreVal = document.getElementById("trust-score-val");
    if (ver.trust_score !== null && ver.trust_score !== undefined) {
      const scorePct = Math.round(ver.trust_score);
      trustScoreVal.textContent = `${scorePct}%`;
      if (scorePct >= 70) {
        trustScoreVal.style.color = "var(--color-supported)";
      } else if (scorePct >= 40) {
        trustScoreVal.style.color = "var(--color-unknown)";
      } else {
        trustScoreVal.style.color = "var(--color-contradicted)";
      }
    } else {
      trustScoreVal.textContent = "N/A";
      trustScoreVal.style.color = "var(--text-dim)";
    }

    // Metric counts
    document.getElementById("count-supported").textContent = ver.supported_claims || 0;
    document.getElementById("count-contradicted").textContent = ver.contradicted_claims || 0;
    document.getElementById("count-unknown").textContent = ver.unknown_claims || 0;
    document.getElementById("count-nonfactual").textContent = ver.non_factual_claims || 0;

    // Summary Text
    document.getElementById("result-summary-text").textContent =
      ver.summary || "No verification summary provided.";

    // Claims List
    const claimsList = document.getElementById("claims-list");
    claimsList.innerHTML = "";

    if (ver.claims && ver.claims.length > 0) {
      ver.claims.forEach((claim) => {
        const item = document.createElement("div");
        item.className = "claim-item";

        const topRow = document.createElement("div");
        topRow.className = "claim-top";

        const claimText = document.createElement("span");
        claimText.className = "claim-text";
        claimText.textContent = claim.claim_text;

        const verdictBadge = document.createElement("span");
        if (claim.verdict) {
          verdictBadge.className = `verdict-tag verdict-${claim.verdict}`;
          verdictBadge.textContent = claim.verdict;
        } else {
          // Non-factual claims carry no verdict; show their content type instead.
          const contentType = claim.content_type || "NON_FACTUAL";
          const badgeClass = NON_FACTUAL_BADGE_CLASS[contentType] || "VIEWPOINT";
          verdictBadge.className = `verdict-tag verdict-${badgeClass}`;
          verdictBadge.textContent = contentType.replace("_", " ");
        }

        topRow.appendChild(claimText);
        topRow.appendChild(verdictBadge);
        item.appendChild(topRow);

        if (claim.explanation) {
          const exp = document.createElement("div");
          exp.className = "claim-explanation";
          exp.textContent = claim.explanation;
          item.appendChild(exp);
        }

        claimsList.appendChild(item);
      });
    } else {
      claimsList.innerHTML = '<div class="claim-item"><span class="claim-text">No atomic claims extracted.</span></div>';
    }

    resultsCard.classList.remove("hidden");
  }

  function showError(msg) {
    errorMessage.textContent = msg;
    errorBanner.classList.remove("hidden");
  }

  function hideError() {
    errorBanner.classList.add("hidden");
  }
});
