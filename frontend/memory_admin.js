(function () {
  const ui = {
    title: "记忆管理",
    subtitle: "让松果记住长期偏好",
    unavailable: "记忆服务未启动。请用 dashboard_server.py 或 start_dashboard_api.ps1 启动网页。",
    saved: "已更新记忆。重新生成早报后，新记忆会进入今天的早报和追问。",
    failed: "记忆更新失败",
    add: "记住",
    remove: "删除",
    section: "类型",
    item: "内容",
    placeholder: "例如：小米汽车",
    sections: {
      regions: "国家/地区",
      industries: "行业",
      companies: "公司",
      markets: "市场变量",
      news_topics: "新闻主题",
      life_reminders: "生活提醒"
    }
  };

  window.addEventListener("load", () => {
    const anchor = document.querySelector("#reminderAdminPanel") || document.querySelector(".ask-panel");
    if (!anchor) return;
    const panel = document.createElement("section");
    panel.id = "memoryAdminPanel";
    panel.className = "memory-admin-panel";
    panel.innerHTML = `<div class="section-heading"><div><p class="eyebrow">Memory Config</p><h2>${ui.title}</h2></div><span>${ui.subtitle}</span></div><div id="memoryAdminStatus" class="admin-status"></div><div id="memoryAdminList"></div>${buildForm()}`;
    anchor.insertAdjacentElement("afterend", panel);
    panel.querySelector("#memoryAddForm").addEventListener("submit", addMemory);
    loadMemory();
  });

  function buildForm() {
    const options = Object.entries(ui.sections).map(([key, label]) => `<option value="${key}">${label}</option>`).join("");
    return `<form id="memoryAddForm" class="memory-admin-form"><label>${ui.section}<select name="section">${options}</select></label><label>${ui.item}<input name="item" required placeholder="${ui.placeholder}" /></label><button type="submit">${ui.add}</button></form>`;
  }

  async function loadMemory() {
    try {
      const response = await fetch("/api/memory", { cache: "no-store" });
      if (!response.ok) throw new Error("api unavailable");
      const payload = await response.json();
      renderMemory(payload.profile || {});
      setStatus("");
    } catch (error) {
      renderMemory(null);
      setStatus(ui.unavailable, true);
    }
  }

  function renderMemory(profile) {
    const list = document.querySelector("#memoryAdminList");
    if (!list) return;
    if (!profile) {
      list.innerHTML = "";
      return;
    }
    const focus = profile.focus || {};
    const groups = {
      regions: focus.regions || [],
      industries: focus.industries || [],
      companies: focus.companies || [],
      markets: focus.markets || [],
      news_topics: focus.news_topics || [],
      life_reminders: profile.life_reminders || []
    };
    list.innerHTML = Object.entries(groups).map(([section, values]) => renderGroup(section, values)).join("");
    list.querySelectorAll("[data-memory-remove]").forEach((button) => button.addEventListener("click", removeMemory));
  }

  function renderGroup(section, values) {
    const chips = values.length ? values.map((item) => `<span class="memory-chip"><span>${escapeHtml(item)}</span><button type="button" title="${ui.remove}" data-memory-remove="true" data-section="${section}" data-item="${escapeHtml(item)}">×</button></span>`).join("") : `<em>暂无</em>`;
    return `<article class="memory-group"><h3>${ui.sections[section] || section}</h3><div class="memory-chip-list">${chips}</div></article>`;
  }

  async function addMemory(event) {
    event.preventDefault();
    const form = event.currentTarget;
    const payload = Object.fromEntries(new FormData(form).entries());
    payload.item = (payload.item || "").trim();
    if (!payload.item) return;
    try {
      const result = await postJson("/api/memory/add", payload);
      renderMemory(result.profile || {});
      setStatus(ui.saved);
      form.reset();
    } catch (error) {
      setStatus(`${ui.failed}: ${error.message}`, true);
    }
  }

  async function removeMemory(event) {
    const button = event.currentTarget;
    try {
      const result = await postJson("/api/memory/remove", { section: button.dataset.section, item: button.dataset.item });
      renderMemory(result.profile || {});
      setStatus(ui.saved);
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
    const status = document.querySelector("#memoryAdminStatus");
    if (!status) return;
    status.textContent = message;
    status.className = isError ? "admin-status is-error" : "admin-status";
  }

  function escapeHtml(value) {
    return String(value).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/\"/g, "&quot;").replace(/'/g, "&#039;");
  }
})();
