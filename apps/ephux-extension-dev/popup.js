async function currentSelection() {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  const response = await chrome.tabs.sendMessage(tab.id, { kind: "EPHUX_GET_SELECTION" });
  return response?.selection || "";
}

async function localFetch(path, body) {
  const baseUrl = document.getElementById("baseUrl").value;
  const token = document.getElementById("token").value;
  const response = await fetch(`${baseUrl}${path}`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      "X-Ephux-Token": token
    },
    body: JSON.stringify(body)
  });
  const text = await response.text();
  try {
    return JSON.parse(text);
  } catch {
    return { raw: text, status: response.status };
  }
}

function write(payload) {
  document.getElementById("output").textContent = JSON.stringify(payload, null, 2);
}

document.getElementById("sendSelection").addEventListener("click", async () => {
  const selection = await currentSelection();
  const payload = await localFetch("/guardian/intake", { text: selection, source_metadata: { source: "extension-dev" } });
  write(payload);
});

document.getElementById("startActivation").addEventListener("click", async () => {
  const purpose = document.getElementById("purpose").value;
  const payload = await localFetch("/activation", { purpose, provider_preference: "scripted" });
  write(payload);
  if (payload.report_location) {
    chrome.tabs.create({ url: payload.report_location.replace(/\\/g, "/") });
  }
});
