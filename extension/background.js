/**
 * VerifAI Chrome Extension - Background Service Worker
 * Handles context menus and API relay.
 */

chrome.runtime.onInstalled.addListener(() => {
  chrome.contextMenus.create({
    id: "verifai-verify-selection",
    title: "Verify with VerifAI",
    contexts: ["selection"],
  });
});

chrome.contextMenus.onClicked.addListener((info, tab) => {
  if (info.menuItemId === "verifai-verify-selection" && info.selectionText) {
    // Store selected text in storage for popup to retrieve when opened
    chrome.storage.local.set(
      {
        pendingVerificationText: info.selectionText,
        pendingSourceUrl: tab?.url || "",
      },
      () => {
        // Open the extension popup / action
        if (chrome.action.openPopup) {
          chrome.action.openPopup();
        }
      }
    );
  }
});
