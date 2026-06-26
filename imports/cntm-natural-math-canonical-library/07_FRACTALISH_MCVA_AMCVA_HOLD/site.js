function timestampToSeconds(value) {
  const parts = value.trim().split(":").map(Number);
  if (!parts.length || parts.some(Number.isNaN)) {
    return 0;
  }
  return parts.reduce((total, part) => (total * 60) + part, 0);
}

function parseTimedSubtitleText(rawText) {
  return rawText
    .replace(/\u00c2/g, "")
    .split(/\r?\n\r?\n+/)
    .map((block) => block.trim())
    .filter(Boolean)
    .map((block) => {
      const lines = block.split(/\r?\n/).map((line) => line.trim()).filter(Boolean);
      const time = lines.shift() || "00:00:00";
      return {
        time,
        seconds: timestampToSeconds(time),
        text: lines.join(" ").replace(/\s+/g, " ").trim(),
      };
    })
    .filter((item) => item.text);
}

function renderSubtitlePanel(panel, entries) {
  const list = panel.querySelector("[data-subtitle-list]");
  const empty = panel.querySelector("[data-subtitle-empty]");
  const videoUrl = panel.getAttribute("data-video-url") || "";

  list.innerHTML = "";

  for (const entry of entries) {
    const item = document.createElement("li");
    item.className = "subtitle-item";
    item.dataset.search = `${entry.time} ${entry.text}`.toLowerCase();

    const time = document.createElement("a");
    time.className = "subtitle-time";
    time.href = `${videoUrl}${videoUrl.includes("?") ? "&" : "?"}t=${entry.seconds}s`;
    time.target = "_blank";
    time.rel = "noreferrer noopener";
    time.textContent = entry.time;

    const text = document.createElement("span");
    text.className = "subtitle-text";
    text.textContent = entry.text;

    item.append(time, text);
    list.appendChild(item);
  }

  empty.classList.toggle("hide", entries.length > 0);
}

async function bootSubtitlePanels() {
  const panels = Array.from(document.querySelectorAll("[data-subtitle-source]"));

  await Promise.all(
    panels.map(async (panel) => {
      const status = panel.querySelector("[data-subtitle-status]");
      const input = panel.querySelector("[data-subtitle-search]");

      try {
        const response = await fetch(panel.getAttribute("data-subtitle-source"));
        if (!response.ok) {
          throw new Error(`HTTP ${response.status}`);
        }

        const entries = parseTimedSubtitleText(await response.text());
        panel._subtitleEntries = entries;
        renderSubtitlePanel(panel, entries);

        if (status) {
          status.textContent = `${entries.length} subtitle cues loaded.`;
        }

        if (input) {
          input.addEventListener("input", () => {
            const query = input.value.trim().toLowerCase();
            const filtered = !query
              ? panel._subtitleEntries
              : panel._subtitleEntries.filter((entry) =>
                  `${entry.time} ${entry.text}`.toLowerCase().includes(query)
                );
            renderSubtitlePanel(panel, filtered);
            if (status) {
              status.textContent = `${filtered.length} subtitle cues shown.`;
            }
          });
        }
      } catch (error) {
        if (status) {
          status.textContent = `Subtitle panel unavailable: ${error.message}`;
        }
      }
    })
  );
}

document.addEventListener("DOMContentLoaded", () => {
  if (document.querySelector("[data-subtitle-source]")) {
    bootSubtitlePanels();
  }
});
