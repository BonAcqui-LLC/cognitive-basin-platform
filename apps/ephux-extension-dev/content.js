chrome.runtime.onMessage.addListener((message, _sender, sendResponse) => {
  if (message?.kind === "EPHUX_GET_SELECTION") {
    sendResponse({ selection: window.getSelection().toString() });
  }
});
