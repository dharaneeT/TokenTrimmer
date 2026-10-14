const $ = (id) => document.getElementById(id);
const fmt = (n) => Number(n).toLocaleString();

function addCell(row, value, numeric) {
  const td = document.createElement("td");
  td.textContent = value;
  if (numeric) td.className = "num";
  row.appendChild(td);
}

function render(data) {
  const pct =
    data.start_tokens > 0
      ? Math.round((100 * data.saved) / data.start_tokens)
      : 0;
  $("summary").textContent =
    fmt(data.start_tokens) +
    " -> " +
    fmt(data.end_tokens) +
    " tokens (saved " +
    fmt(data.saved) +
    ", " +
    pct +
    "%), estimated";
  $("verdict").textContent = data.verdict;

  const body = $("steps").querySelector("tbody");
  body.textContent = "";
  data.steps.forEach((step, i) => {
    const row = document.createElement("tr");
    addCell(row, i + 1, true);
    addCell(row, step.name, false);
    addCell(row, fmt(step.after - step.before), true);
    addCell(row, fmt(step.after), true);
    addCell(row, step.note, false);
    body.appendChild(row);
  });
  $("output").value = data.output;
}

async function shrink() {
  const button = $("go");
  button.disabled = true;
  $("error").textContent = "";
  try {
    const response = await fetch("/api/shrink", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        text: $("text").value,
        question: $("question").value,
        budget: Number($("budget").value),
      }),
    });
    const data = await response.json();
    if (!response.ok) {
      $("error").textContent =
        typeof data.detail === "string"
          ? data.detail
          : JSON.stringify(data.detail);
      return;
    }
    render(data);
  } catch (error) {
    $("error").textContent = "Could not reach the server: " + error;
  } finally {
    button.disabled = false;
    loadStats();
  }
}

async function loadStats() {
  try {
    const response = await fetch("/api/stats");
    if (!response.ok) return;
    const data = await response.json();
    const pct =
      data.start_total > 0
        ? Math.round((100 * data.saved_total) / data.start_total)
        : 0;
    $("statsTotals").textContent =
      data.runs +
      " runs, estimated tokens " +
      fmt(data.start_total) +
      " -> " +
      fmt(data.end_total) +
      " (saved " +
      fmt(data.saved_total) +
      ", " +
      pct +
      "%)";
    const body = $("statsTable").querySelector("tbody");
    body.textContent = "";
    data.recent.forEach((run) => {
      const row = document.createElement("tr");
      addCell(row, "#" + run.id, false);
      addCell(row, run.created_at.replace("T", " ").slice(0, 19), false);
      addCell(row, run.source, false);
      addCell(row, fmt(run.budget), true);
      addCell(row, fmt(run.start_tokens), true);
      addCell(row, fmt(run.end_tokens), true);
      addCell(row, run.status, false);
      addCell(row, run.steps, true);
      addCell(row, fmt(run.duration_ms), true);
      body.appendChild(row);
    });
    $("stats").hidden = false;
  } catch (error) {
    // stats are optional; the page works without them
  }
}

$("go").addEventListener("click", shrink);
$("copy").addEventListener("click", () =>
  navigator.clipboard.writeText($("output").value),
);
loadStats();
