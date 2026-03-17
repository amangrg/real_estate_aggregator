async function fetchPayload(url) {
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error(`Request failed for ${url}: ${response.status}`);
  }
  return response;
}

function confidenceClass(confidence) {
  if (confidence === "High") return "confidence-high";
  if (confidence === "Medium") return "confidence-medium";
  return "confidence-low";
}

function formatValue(value) {
  if (value === null || value === undefined) return "-";
  if (typeof value === "number") return value.toLocaleString();
  if (typeof value === "boolean") return value ? "Yes" : "No";
  return String(value);
}

function formatFactLabel(key) {
  return key.replaceAll("_", " ");
}

function renderFacts(resolved) {
  const factsGrid = document.getElementById("facts-grid");
  factsGrid.innerHTML = "";

  for (const [key, fact] of Object.entries(resolved.resolved_facts || {})) {
    const card = document.createElement("article");
    card.className = "fact-card";

    const conflict = fact.conflict
      ? `<div class="fact-conflict"><strong>Conflict:</strong> ${Object.entries(fact.conflict)
          .map(([source, value]) => `${source}: ${formatValue(value)}`)
          .join(" | ")}</div>`
      : "";

    card.innerHTML = `
      <div class="fact-topline">
        <span class="fact-key">${formatFactLabel(key)}</span>
        <span class="confidence-chip ${confidenceClass(fact.confidence)}">${fact.confidence}</span>
      </div>
      <div class="fact-value">${formatValue(fact.value)}</div>
      <div class="fact-meta">Sources: ${(fact.sources || []).join(", ") || "-"}</div>
      <div class="fact-reason">${fact.resolution_reason || ""}</div>
      ${conflict}
    `;
    factsGrid.appendChild(card);
  }
}

function renderFlags(resolved) {
  const flagsList = document.getElementById("flags-list");
  flagsList.innerHTML = "";

  const flags = resolved.flags || [];
  if (!flags.length) {
    flagsList.innerHTML = `<div class="empty-state">No flags were generated from the current data.</div>`;
    return;
  }

  for (const flag of flags) {
    const item = document.createElement("div");
    item.className = `flag-card flag-${flag.type}`;
    item.innerHTML = `
      <span class="flag-type">${flag.type}</span>
      <p>${flag.message}</p>
    `;
    flagsList.appendChild(item);
  }
}

function renderPermits(resolved) {
  const permitsContent = document.getElementById("permits-content");
  permitsContent.innerHTML = "";

  const history = resolved.permits_summary?.permit_history || [];
  if (!history.length) {
    permitsContent.innerHTML = `<div class="empty-state">No permit history was available.</div>`;
    return;
  }

  const openPermits = new Set(resolved.permits_summary?.open_permits || []);
  for (const permit of history) {
    const item = document.createElement("div");
    item.className = "timeline-item";
    item.innerHTML = `
      <span class="timeline-badge ${openPermits.has(permit) ? "timeline-open" : ""}">
        ${openPermits.has(permit) ? "Open" : "Closed"}
      </span>
      <p>${permit}</p>
    `;
    permitsContent.appendChild(item);
  }
}

function renderHazards(resolved) {
  const hazardsGrid = document.getElementById("hazards-grid");
  hazardsGrid.innerHTML = "";

  const hazardEntries = Object.entries(resolved.hazards_summary || {}).filter(
    ([, value]) => value !== null && value !== undefined && value !== ""
  );

  if (!hazardEntries.length) {
    hazardsGrid.innerHTML = `<div class="empty-state">No hazard data was available.</div>`;
    return;
  }

  for (const [key, value] of hazardEntries) {
    const card = document.createElement("div");
    card.className = "hazard-card";
    card.innerHTML = `
      <span class="hazard-key">${formatFactLabel(key)}</span>
      <strong>${formatValue(value)}</strong>
    `;
    hazardsGrid.appendChild(card);
  }
}

function renderBrief(markdown) {
  const container = document.getElementById("brief-content");
  container.innerHTML = "";

  const lines = markdown.split("\n").filter((line) => line.trim().length > 0);
  for (const line of lines) {
    let element;
    if (line.startsWith("## ")) {
      element = document.createElement("h3");
      element.textContent = line.replace("## ", "");
    } else if (line.startsWith("- ")) {
      element = document.createElement("p");
      element.className = "brief-bullet";
      element.textContent = line.replace("- ", "");
    } else if (line.startsWith("# ")) {
      continue;
    } else {
      element = document.createElement("p");
      element.textContent = line;
    }
    container.appendChild(element);
  }
}

function renderMeta(resolved) {
  document.getElementById("hero-address").textContent = resolved.canonical_address || "Unknown address";
  document.getElementById("property-id").textContent = resolved.property_id || "-";
  document.getElementById("flag-count").textContent = String((resolved.flags || []).length);
  document.getElementById("fact-count").textContent = String(
    Object.keys(resolved.resolved_facts || {}).length
  );

  const type = resolved.resolved_facts?.property_type?.value || "Property";
  const price = resolved.resolved_facts?.list_price?.value;
  const beds = resolved.resolved_facts?.beds?.value;
  const baths = resolved.resolved_facts?.baths?.value;
  const sqft = resolved.resolved_facts?.sqft?.value;
  const summaryParts = [
    type,
    beds !== undefined && beds !== null && baths !== undefined && baths !== null ? `${beds} bed / ${baths} bath` : null,
    sqft !== undefined && sqft !== null ? `${sqft.toLocaleString()} sqft` : null,
    price !== undefined && price !== null ? `$${price.toLocaleString()}` : null,
  ].filter(Boolean);
  document.getElementById("hero-summary").textContent = summaryParts.join(" | ");
}

async function bootstrap() {
  try {
    const [propertyResponse, briefResponse] = await Promise.all([
      fetchPayload("/api/property"),
      fetchPayload("/api/brief"),
    ]);
    const resolved = await propertyResponse.json();
    const brief = await briefResponse.text();

    renderMeta(resolved);
    renderBrief(brief);
    renderFacts(resolved);
    renderFlags(resolved);
    renderPermits(resolved);
    renderHazards(resolved);
    document.getElementById("json-viewer").textContent = JSON.stringify(resolved, null, 2);
  } catch (error) {
    document.body.innerHTML = `
      <main class="error-screen">
        <h1>Frontend failed to load</h1>
        <p>${error.message}</p>
      </main>
    `;
  }
}

bootstrap();
