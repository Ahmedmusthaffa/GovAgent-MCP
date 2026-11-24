/**
 * GovAgent MCP — Frontend Application Controller
 * Handles user interactions, API dispatch to FastAPI backend,
 * and live synchronization of Unity Catalog Security & MCP Inspector.
 */

// DOM Elements
const chatForm = document.getElementById("chatForm");
const queryInput = document.getElementById("queryInput");
const sendBtn = document.getElementById("sendBtn");
const roleSelector = document.getElementById("roleSelector");
const messagesContainer = document.getElementById("messagesContainer");
const activeRoleBadge = document.getElementById("activeRoleBadge");
const policyTier = document.getElementById("policyTier");
const policyPii = document.getElementById("policyPii");
const policyRefundLimit = document.getElementById("policyRefundLimit");
const policyRestricted = document.getElementById("policyRestricted");
const toolExecutionStream = document.getElementById("toolExecutionStream");
const toolCountBadge = document.getElementById("toolCountBadge");
const auditLogContainer = document.getElementById("auditLogContainer");
const refreshAuditBtn = document.getElementById("refreshAuditBtn");

// Role Configuration Definitions
const ROLE_CONFIGS = {
  intern: {
    badgeClass: "badge-intern",
    badgeText: "Intern",
    tier: "TIER 1 (Public Datasets)",
    pii: "Active (Phone/Email Masked)",
    piiClass: "text-amber",
    limit: "$500.00 USD",
    restricted: "Blocked (executive_salaries)",
    restrictedClass: "text-red"
  },
  manager: {
    badgeClass: "badge-manager",
    badgeText: "Manager",
    tier: "TIER 1, 2 & 3 (Full Catalog)",
    pii: "Disabled (Raw Enterprise Access)",
    piiClass: "text-green",
    limit: "$50,000.00 USD",
    restricted: "Authorized (executive_salaries)",
    restrictedClass: "text-green"
  },
  admin: {
    badgeClass: "badge-admin",
    badgeText: "Admin",
    tier: "Full Enterprise Clearance",
    pii: "Disabled (Superuser)",
    piiClass: "text-green",
    limit: "$1,000,000.00 USD",
    restricted: "Full Executive Access",
    restrictedClass: "text-green"
  }
};

// Initialize Application
document.addEventListener("DOMContentLoaded", () => {
  updatePolicyDisplay(roleSelector.value);
  fetchAuditLogs();
  setupEventListeners();
});

function setupEventListeners() {
  // Role change event
  roleSelector.addEventListener("change", (e) => {
    updatePolicyDisplay(e.target.value);
  });

  // Chat submit event
  chatForm.addEventListener("submit", (e) => {
    e.preventDefault();
    const query = queryInput.value.trim();
    if (!query) return;
    executeChatQuery(query);
  });

  // Shift+Enter newline, Enter submits
  queryInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      chatForm.dispatchEvent(new Event("submit"));
    }
  });

  // Quick scenario chips
  document.querySelectorAll(".chip-btn").forEach((chip) => {
    chip.addEventListener("click", () => {
      const query = chip.getAttribute("data-query");
      const role = chip.getAttribute("data-role");
      if (role) {
        roleSelector.value = role;
        updatePolicyDisplay(role);
      }
      queryInput.value = query;
      executeChatQuery(query);
    });
  });

  // Refresh audit logs button
  refreshAuditBtn.addEventListener("click", () => {
    fetchAuditLogs();
  });
}

function updatePolicyDisplay(role) {
  const config = ROLE_CONFIGS[role] || ROLE_CONFIGS.intern;
  activeRoleBadge.className = `badge ${config.badgeClass}`;
  activeRoleBadge.textContent = config.badgeText;
  policyTier.textContent = config.tier;
  policyPii.textContent = config.pii;
  policyPii.className = `policy-value ${config.piiClass}`;
  policyRefundLimit.textContent = config.limit;
  policyRestricted.textContent = config.restricted;
  policyRestricted.className = `policy-value ${config.restrictedClass}`;
}

async function executeChatQuery(query) {
  const currentRole = roleSelector.value;
  queryInput.value = "";
  sendBtn.disabled = true;

  // Append User Message to UI
  appendUserMessage(query, currentRole);

  // Append Thinking Indicator
  const thinkingId = appendThinkingIndicator();

  try {
    const response = await fetch("/api/v1/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ query: query, role: currentRole })
    });

    if (!response.ok) {
      throw new Error(`Server returned HTTP ${response.status}`);
    }

    const data = await response.json();

    // Remove thinking indicator
    removeThinkingIndicator(thinkingId);

    // Append Assistant Response
    appendAssistantMessage(data);

    // Update Right Inspector Panels
    updateToolExecutionInspector(data.tool_events);
    fetchAuditLogs();

  } catch (error) {
    removeThinkingIndicator(thinkingId);
    appendErrorMessage(error.message);
  } finally {
    sendBtn.disabled = false;
    queryInput.focus();
  }
}

function appendUserMessage(query, role) {
  const wrapper = document.createElement("div");
  wrapper.className = "message-wrapper user";
  wrapper.innerHTML = `
    <div class="message-avatar">YOU</div>
    <div class="message-card">
      <div class="message-header">
        <span class="message-sender">User (${role.toUpperCase()})</span>
        <span class="message-meta">${new Date().toLocaleTimeString()}</span>
      </div>
      <div class="message-body">
        <p>${escapeHtml(query)}</p>
      </div>
    </div>
  `;
  messagesContainer.appendChild(wrapper);
  scrollToBottom();
}

function appendThinkingIndicator() {
  const id = "thinking-" + Date.now();
  const wrapper = document.createElement("div");
  wrapper.id = id;
  wrapper.className = "message-wrapper assistant";
  wrapper.innerHTML = `
    <div class="message-avatar">AG</div>
    <div class="message-card">
      <div class="message-header">
        <span class="message-sender">GovAgent MCP</span>
        <span class="message-meta">Inspecting Unity Catalog Policies...</span>
      </div>
      <div class="message-body">
        <p style="color: #64748B;">Analyzing intent &bull; Evaluating permissions &bull; Calling MCP tool servers...</p>
      </div>
    </div>
  `;
  messagesContainer.appendChild(wrapper);
  scrollToBottom();
  return id;
}

function removeThinkingIndicator(id) {
  const el = document.getElementById(id);
  if (el) el.remove();
}

function appendAssistantMessage(data) {
  const wrapper = document.createElement("div");
  wrapper.className = "message-wrapper assistant";

  // Build pipeline steps HTML
  const stepsHtml = (data.step_history || [])
    .map((s) => `<div class="pipeline-step-item"><span>&bull;</span> ${escapeHtml(s)}</div>`)
    .join("");

  // Build governance alert banner if any
  let alertBanner = "";
  if (data.governance_alerts && data.governance_alerts.length > 0) {
    alertBanner = `
      <div class="security-alert-box">
        <div class="security-alert-title">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"></path>
          </svg>
          Unity Catalog Security Enforcement Alert
        </div>
        <div>${data.governance_alerts.map((a) => escapeHtml(a)).join("<br>")}</div>
      </div>
    `;
  }

  // Format markdown in final response using marked.js
  const formattedBody = marked.parse(data.final_response || "");

  wrapper.innerHTML = `
    <div class="message-avatar">AG</div>
    <div class="message-card">
      <div class="message-header">
        <span class="message-sender">GovAgent MCP (${data.user_role.toUpperCase()})</span>
        <span class="message-meta">Latency: ${data.total_latency_ms}ms</span>
      </div>
      <div class="pipeline-steps">
        ${stepsHtml}
      </div>
      ${alertBanner}
      <div class="message-body">
        ${formattedBody}
      </div>
    </div>
  `;

  messagesContainer.appendChild(wrapper);
  scrollToBottom();
}

function appendErrorMessage(errorMsg) {
  const wrapper = document.createElement("div");
  wrapper.className = "message-wrapper assistant";
  wrapper.innerHTML = `
    <div class="message-avatar" style="background-color: #DC2626;">ERR</div>
    <div class="message-card" style="border-color: #FECACA; background-color: #FEF2F2;">
      <div class="message-header">
        <span class="message-sender" style="color: #991B1B;">Communication Error</span>
      </div>
      <div class="message-body" style="color: #991B1B;">
        <p>Could not reach the GovAgent MCP backend server. Please verify the server is running.</p>
        <p><strong>Error:</strong> ${escapeHtml(errorMsg)}</p>
      </div>
    </div>
  `;
  messagesContainer.appendChild(wrapper);
  scrollToBottom();
}

function updateToolExecutionInspector(toolEvents) {
  if (!toolEvents || toolEvents.length === 0) {
    toolExecutionStream.innerHTML = `<div class="empty-state">No tool invocations required for this query.</div>`;
    toolCountBadge.textContent = "0 Tools";
    return;
  }

  toolCountBadge.textContent = `${toolEvents.length} Tools Invoked`;
  toolExecutionStream.innerHTML = "";

  toolEvents.forEach((t) => {
    const isBlocked = t.status === "BLOCKED";
    const statusBadgeClass = isBlocked ? "badge-blocked" : "badge-success";

    let detailSummary = "";
    if (t.tool === "mcp_database_query") {
      detailSummary = isBlocked
        ? `<strong>Denied:</strong> ${escapeHtml(t.security_alert || "")}`
        : `<strong>Queried Rows:</strong> ${t.row_count} records returned (PII Masking applied if non-manager).`;
    } else if (t.tool === "mcp_vector_search") {
      detailSummary = `<strong>Matches:</strong> ${t.results_count} policy sections retrieved (Top score: ${t.results && t.results[0] ? t.results[0].relevance_score + "%" : "N/A"}).`;
    } else if (t.tool === "mcp_execute_refund") {
      detailSummary = isBlocked
        ? `<strong>Denied:</strong> ${escapeHtml(t.security_alert || "")}`
        : `<strong>Executed:</strong> $${t.amount_usd} refund dispatched for Customer #${t.customer_id}.`;
    }

    const card = document.createElement("div");
    card.className = `tool-entry-card ${isBlocked ? "status-blocked" : ""}`;
    card.innerHTML = `
      <div class="tool-entry-header">
        <span class="tool-entry-name">${escapeHtml(t.tool)}</span>
        <div style="display:flex; align-items:center; gap:6px;">
          <span class="badge ${statusBadgeClass}">${t.status}</span>
          <span class="tool-entry-time">${t.execution_time_ms}ms</span>
        </div>
      </div>
      <div class="tool-entry-detail">
        ${detailSummary}
      </div>
    `;
    toolExecutionStream.appendChild(card);
  });
}

async function fetchAuditLogs() {
  try {
    const res = await fetch("/api/v1/audit/logs?limit=10");
    if (!res.ok) return;
    const data = await res.json();
    const logs = data.audit_trail || [];

    if (logs.length === 0) {
      auditLogContainer.innerHTML = `<div class="empty-state">No audit events recorded yet.</div>`;
      return;
    }

    auditLogContainer.innerHTML = "";
    // Display in reverse chronological order
    logs.slice().reverse().forEach((log) => {
      const isBlocked = log.status === "BLOCKED";
      const statusClass = isBlocked ? "status-blocked" : "status-allowed";
      const timeStr = log.timestamp ? log.timestamp.split("T")[1].substring(0, 8) : "";

      const entry = document.createElement("div");
      entry.className = `audit-entry ${statusClass}`;
      entry.innerHTML = `
        <div class="audit-entry-top">
          <span class="audit-tool">${escapeHtml(log.tool_name)}</span>
          <span class="audit-time">${timeStr} &bull; ${log.user_role.toUpperCase()}</span>
        </div>
        <div class="audit-details">
          <strong>${log.status}:</strong> ${escapeHtml(log.details)}
        </div>
      `;
      auditLogContainer.appendChild(entry);
    });
  } catch (e) {
    console.error("Failed to fetch audit logs", e);
  }
}

function scrollToBottom() {
  messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

function escapeHtml(text) {
  if (!text) return "";
  const map = {
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    '"': "&quot;",
    "'": "&#039;"
  };
  return text.replace(/[&<>"']/g, (m) => map[m]);
}
