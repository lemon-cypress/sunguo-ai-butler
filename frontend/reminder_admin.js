(function () {
  const ui = {
    title: "\u63d0\u9192\u914d\u7f6e",
    subtitle: "\u9700\u8981\u7528 dashboard_server.py \u542f\u52a8",
    unavailable: "\u7f16\u8f91\u670d\u52a1\u672a\u542f\u52a8\uff0c\u53ef\u7ee7\u7eed\u67e5\u770b\u65e9\u62a5\uff0c\u4f46\u4e0d\u80fd\u5728\u7f51\u9875\u91cc\u4fee\u6539\u63d0\u9192\u3002",
    enabled: "\u542f\u7528",
    disabled: "\u5173\u95ed",
    add: "\u65b0\u589e\u63d0\u9192",
    save: "\u4fdd\u5b58",
    time: "\u65f6\u95f4",
    titleLabel: "\u6807\u9898",
    message: "\u8bdd\u672f",
    type: "\u7c7b\u578b",
    priority: "\u4f18\u5148\u7ea7",
    normal: "\u666e\u901a",
    high: "\u9ad8",
    saved: "\u5df2\u4fdd\u5b58\u3002\u91cd\u65b0\u751f\u6210\u65e9\u62a5\u540e\uff0c\u65b0\u63d0\u9192\u4f1a\u8fdb\u5165\u4eca\u5929\u7684\u63d0\u9192\u8ba1\u5212\u3002",
    failed: "\u4fdd\u5b58\u5931\u8d25",
    regenReal: "\u91cd\u65b0\u751f\u6210\u65e9\u62a5",
    regenMock: "\u5feb\u901f\u6d4b\u8bd5\u751f\u6210",
    regenerating: "\u6b63\u5728\u751f\u6210\u65e9\u62a5\uff0c\u8bf7\u7a0d\u7b49...",
    regenerated: "\u65e9\u62a5\u5df2\u751f\u6210\uff0c\u9875\u9762\u5373\u5c06\u5237\u65b0\u3002",
    mockRegenerated: "\u6d4b\u8bd5\u751f\u6210\u5b8c\u6210\uff0c\u6b63\u5f0f\u65e9\u62a5\u672a\u5237\u65b0\u3002"
  };

  window.addEventListener("load", () => {
    const anchor = document.querySelector("#reminderPanel") || document.querySelector(".ask-panel");
    if (!anchor) return;
    const panel = document.createElement("section");
    panel.id = "reminderAdminPanel";
    panel.className = "reminder-admin-panel";
    panel.innerHTML = `<div class="section-heading"><div><p class="eyebrow">Reminder Config</p><h2>${ui.title}</h2></div><span>${ui.subtitle}</span></div><div id="reminderAdminStatus"></div><div class="reminder-admin-actions"><button id="regenerateBriefBtn" type="button">${ui.regenReal}</button><button id="regenerateMockBriefBtn" type="button">${ui.regenMock}</button></div><div id="reminderAdminList"></div>${buildForm()}`;
    anchor.insertAdjacentElement("afterend", panel);
    loadRules();
    panel.querySelector("#reminderAddForm").addEventListener("submit", addReminder);
    panel.querySelector("#regenerateBriefBtn").addEventListener("click", () => regenerateBrief(false));
    panel.querySelector("#regenerateMockBriefBtn").addEventListener("click", () => regenerateBrief(true));
  });

  function buildForm() {
    return `<form id="reminderAddForm" class="reminder-admin-form"><label>${ui.time}<input name="time" required placeholder="22:30" pattern="\\d{2}:\\d{2}" /></label><label>${ui.titleLabel}<input name="title" required placeholder="\u5237\u7259" /></label><label>${ui.message}<input name="message" required placeholder="\u7761\u524d\u8bb0\u5f97\u5237\u7259\u3002" /></label><label>${ui.type}<select name="type"><option value="life">life</option><option value="health">health</option><option value="medicine">medicine</option></select></label><label>${ui.priority}<select name="priority"><option value="normal">${ui.normal}</option><option value="high">${ui.high}</option></select></label><button type="submit">${ui.add}</button></form>`;
  }

  async function loadRules() {
    try {
      const response = await fetch("/api/reminders", { cache: "no-store" });
      if (!response.ok) throw new Error("api unavailable");
      const rules = await response.json();
      renderRules(rules);
      setStatus("");
    } catch (error) {
      renderRules(null);
      setStatus(ui.unavailable, true);
    }
  }

  function renderRules(rules) {
    const list = document.querySelector("#reminderAdminList");
    if (!list) return;
    const reminders = rules?.fixed_reminders || [];
    list.innerHTML = reminders.map((item) => `<article class="reminder-rule ${item.enabled ? "is-enabled" : "is-disabled"}"><div><strong>${escapeHtml(item.time || "")} ${escapeHtml(item.title || "")}</strong><p>${escapeHtml(item.message || "")}</p><span>${escapeHtml(item.type || "life")} \u00b7 ${escapeHtml(item.priority || "normal")}</span></div><button type="button" data-title="${escapeHtml(item.title || "")}" data-enabled="${item.enabled ? "false" : "true"}">${item.enabled ? ui.enabled : ui.disabled}</button></article>`).join("");
    list.querySelectorAll("button[data-title]").forEach((button) => button.addEventListener("click", toggleReminder));
  }

  async function addReminder(event) {
    event.preventDefault();
    const form = event.currentTarget;
    const payload = Object.fromEntries(new FormData(form).entries());
    try {
      const result = await postJson("/api/reminders/add", payload);
      renderRules(result.rules);
      setStatus(ui.saved);
      form.reset();
    } catch (error) {
      setStatus(`${ui.failed}: ${error.message}`, true);
    }
  }

  async function toggleReminder(event) {
    const button = event.currentTarget;
    try {
      const result = await postJson("/api/reminders/toggle", { title: button.dataset.title, enabled: button.dataset.enabled === "true" });
      renderRules(result.rules);
      setStatus(ui.saved);
    } catch (error) {
      setStatus(`${ui.failed}: ${error.message}`, true);
    }
  }

  async function regenerateBrief(mock) {
    setStatus(ui.regenerating);
    try {
      await postJson("/api/brief/regenerate", { mock });
      setStatus(mock ? ui.mockRegenerated : ui.regenerated);
      if (!mock) window.setTimeout(() => window.location.reload(), 900);
    } catch (error) {
      setStatus(`${ui.failed}: ${error.message}`, true);
    }
  }

  async function postJson(url, payload) {
    const response = await fetch(url, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) });
    const result = await response.json();
    if (!response.ok || result.ok === false) throw new Error(result.error || response.statusText);
    return result;
  }

  function setStatus(message, isError = false) {
    const status = document.querySelector("#reminderAdminStatus");
    if (!status) return;
    status.textContent = message;
    status.className = isError ? "admin-status is-error" : "admin-status";
  }

  function escapeHtml(value) {
    return String(value).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/\"/g, "&quot;").replace(/'/g, "&#039;");
  }
})();


