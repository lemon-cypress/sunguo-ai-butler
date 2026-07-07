const params = new URLSearchParams(window.location.search);
const requestedDate = params.get("date");

const TEXT = {
  loadError: "没有读到早报输出包，请先运行 morning_brief_demo.py --save。",
  todoEmpty: "还没有待办事项，先加一条今天最重要的事。",
  newsEmpty: "今天还没有整理出新闻内容，请先生成最新早报。",
  unknownDate: "未知日期",
  unknownCity: "未知城市",
  newsClue: "待补充",
};

const FORMAT_DEFAULTS = {
  headingSize: 21,
  bodySize: 16,
  lineHeight: 1,
  moduleGap: 46,
  checkboxSize: 11,
  level1Indent: 0,
  level2Indent: 26,
  bulletWidth: 14,
};

const state = {
  bundle: null,
  todos: [],
};

const overviewList = document.querySelector("#overviewList");
const newsSections = document.querySelector("#newsSections");
const newsSourceStrip = document.querySelector("#newsSourceStrip");
const todoList = document.querySelector("#todoList");
const todoForm = document.querySelector("#todoForm");
const todoTitleInput = document.querySelector("#todoTitleInput");
const deleteSelectedBtn = document.querySelector("#deleteSelectedBtn");
const rootStyle = document.documentElement;

bootstrap();
initFormatPanel();

todoForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const title = todoTitleInput.value.trim();
  if (!title) return;
  await postJson("/api/todos/add", { title, completed: false });
  todoTitleInput.value = "";
  await loadTodos();
});

deleteSelectedBtn.addEventListener("click", async () => {
  const ids = Array.from(document.querySelectorAll(".todo-checkbox:checked"))
    .map((node) => node.value)
    .filter(Boolean);
  if (!ids.length) return;
  await postJson("/api/todos/delete", { ids });
  await loadTodos();
});

async function bootstrap() {
  await Promise.all([loadBundle(), loadTodos()]);
}

async function loadBundle() {
  const bundlePath = await resolveBundlePath();
  try {
    const response = await fetch(bundlePath, { cache: "no-store" });
    if (!response.ok) throw new Error(`Cannot read ${bundlePath}`);
    state.bundle = await response.json();
    renderBundle();
  } catch (error) {
    console.error(error);
    newsSections.innerHTML = `<article class="empty-state error-state">${escapeHtml(TEXT.loadError)}</article>`;
  }
}

async function loadTodos() {
  try {
    const response = await fetch("/api/todos", { cache: "no-store" });
    if (!response.ok) throw new Error("Cannot read todos");
    const payload = await response.json();
    state.todos = payload.items || [];
    renderTodos();
  } catch (error) {
    todoList.innerHTML = `<article class="empty-state error-state">${escapeHtml(error.message)}</article>`;
  }
}

async function resolveBundlePath() {
  if (requestedDate) return `../demos/${requestedDate}/output_bundle.json`;
  try {
    const response = await fetch("../demos/latest.json", { cache: "no-store" });
    if (response.ok) {
      const latest = await response.json();
      if (latest.bundle_path) return `../demos/${latest.bundle_path}`;
    }
  } catch (error) {
    console.warn("latest.json unavailable, fallback to local date", error);
  }
  return `../demos/${getLocalDateText()}/output_bundle.json`;
}

function renderBundle() {
  const bundle = state.bundle;
  if (!bundle) return;
  document.querySelector("#dateLabel").textContent = bundle.date || TEXT.unknownDate;
  document.querySelector("#cityLabel").textContent = bundle.city || TEXT.unknownCity;
  renderNews(bundle);
}

function renderTodos() {
  const items = state.todos || [];
  if (!items.length) {
    todoList.innerHTML = `<article class="empty-state">${escapeHtml(TEXT.todoEmpty)}</article>`;
    return;
  }

  todoList.innerHTML = items
    .map(
      (item) => `
        <label class="todo-item ${item.completed ? "is-complete" : ""}">
          <div class="todo-item-main">
            <input class="todo-checkbox" type="checkbox" value="${escapeHtml(item.id)}" ${item.completed ? "checked" : ""} />
            <div class="todo-copy">
              <strong>${escapeHtml(item.title || "")}</strong>
            </div>
          </div>
        </label>
      `,
    )
    .join("");

  document.querySelectorAll(".todo-checkbox").forEach((checkbox) => {
    checkbox.addEventListener("change", async (event) => {
      const node = event.currentTarget;
      await postJson("/api/todos/toggle", {
        id: node.value,
        completed: node.checked,
      });
      await loadTodos();
    });
  });
}

function renderNews(bundle) {
  const digest = bundle.news_digest || {};
  const overview = digest.overview || [];
  const sections = digest.sections || [];

  overviewList.innerHTML = overview.length
    ? overview.map((item) => `<li>${escapeHtml(item)}</li>`).join("")
    : "";
  newsSourceStrip.innerHTML = "";

  if (!sections.length) {
    newsSections.innerHTML = `<article class="empty-state">${escapeHtml(TEXT.newsEmpty)}</article>`;
    return;
  }

  newsSections.innerHTML = sections.map(renderNewsSection).join("");
}

function renderNewsSection(section) {
  return `
    <article class="news-section">
      <div class="news-section-title-row">
        <span class="news-dot"></span>
        <h3>${escapeHtml(section.title || TEXT.newsClue)}</h3>
      </div>
      <ul class="news-sublist">
        ${(section.items || []).map(renderNewsEntry).join("")}
      </ul>
    </article>
  `;
}

function renderNewsEntry(entry) {
  const timePrefix = entry.time ? `[${escapeHtml(entry.time)}] ` : "";
  const thesis = escapeHtml(entry.thesis || TEXT.newsClue);
  const summary = escapeHtml(entry.summary || "");
  return `<li>${timePrefix}${thesis}${summary ? `：${summary}` : ""}</li>`;
}

async function postJson(url, payload) {
  const response = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  const result = await response.json();
  if (!response.ok || result.ok === false) {
    throw new Error(result.error || response.statusText);
  }
  return result;
}

function getLocalDateText() {
  const now = new Date();
  const year = now.getFullYear();
  const month = String(now.getMonth() + 1).padStart(2, "0");
  const day = String(now.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

function initFormatPanel() {
  const controls = [
    ["headingSize", "controlHeadingSize", "outputHeadingSize", "px"],
    ["bodySize", "controlBodySize", "outputBodySize", "px"],
    ["lineHeight", "controlLineHeight", "outputLineHeight", ""],
    ["moduleGap", "controlModuleGap", "outputModuleGap", "px"],
    ["checkboxSize", "controlCheckboxSize", "outputCheckboxSize", "px"],
    ["level1Indent", "controlLevel1Indent", "outputLevel1Indent", "px"],
    ["level2Indent", "controlLevel2Indent", "outputLevel2Indent", "px"],
    ["bulletWidth", "controlBulletWidth", "outputBulletWidth", "px"],
  ];

  const saved = loadFormatSettings();
  controls.forEach(([key, inputId, outputId, suffix]) => {
    const input = document.querySelector(`#${inputId}`);
    const output = document.querySelector(`#${outputId}`);
    if (!input || !output) return;
    input.value = saved[key];
    output.textContent = `${saved[key]}${suffix}`;
    input.addEventListener("input", () => {
      const next = loadFormatSettings();
      next[key] = Number(input.value);
      saveFormatSettings(next);
      applyFormatSettings(next);
      renderFormatSummary(next);
      output.textContent = `${input.value}${suffix}`;
    });
  });

  const resetButton = document.querySelector("#resetFormatBtn");
  if (resetButton) {
    resetButton.addEventListener("click", () => {
      saveFormatSettings(FORMAT_DEFAULTS);
      applyFormatSettings(FORMAT_DEFAULTS);
      renderFormatSummary(FORMAT_DEFAULTS);
      controls.forEach(([key, inputId, outputId, suffix]) => {
        const input = document.querySelector(`#${inputId}`);
        const output = document.querySelector(`#${outputId}`);
        if (!input || !output) return;
        input.value = FORMAT_DEFAULTS[key];
        output.textContent = `${FORMAT_DEFAULTS[key]}${suffix}`;
      });
    });
  }

  const copyButton = document.querySelector("#copyFormatBtn");
  if (copyButton) {
    copyButton.addEventListener("click", async () => {
      const settings = loadFormatSettings();
      const summary = buildFormatSummary(settings);
      try {
        await navigator.clipboard.writeText(summary);
        copyButton.textContent = "已复制";
        window.setTimeout(() => {
          copyButton.textContent = "复制参数";
        }, 1200);
      } catch (error) {
        console.warn("copy format settings failed", error);
      }
    });
  }

  applyFormatSettings(saved);
  renderFormatSummary(saved);
}

function loadFormatSettings() {
  try {
    const raw = window.localStorage.getItem("sunguo-format-panel-v1");
    if (!raw) return { ...FORMAT_DEFAULTS };
    return { ...FORMAT_DEFAULTS, ...JSON.parse(raw) };
  } catch (error) {
    return { ...FORMAT_DEFAULTS };
  }
}

function saveFormatSettings(settings) {
  window.localStorage.setItem("sunguo-format-panel-v1", JSON.stringify(settings));
}

function applyFormatSettings(settings) {
  rootStyle.setProperty("--heading-size", `${settings.headingSize}px`);
  rootStyle.setProperty("--body-size", `${settings.bodySize}px`);
  rootStyle.setProperty("--body-line-height", String(settings.lineHeight));
  rootStyle.setProperty("--news-module-gap", `${settings.moduleGap}px`);
  rootStyle.setProperty("--checkbox-size", `${settings.checkboxSize}px`);
  rootStyle.setProperty("--level1-indent", `${settings.level1Indent}px`);
  rootStyle.setProperty("--level2-indent", `${settings.level2Indent}px`);
  rootStyle.setProperty("--bullet-width", `${settings.bulletWidth}px`);
  rootStyle.setProperty("--bullet-dot-size", `${Math.max(3, Math.round(settings.bulletWidth / 2.8))}px`);
}

function renderFormatSummary(settings) {
  const node = document.querySelector("#formatPresetText");
  if (!node) return;
  node.value = buildFormatSummary(settings);
}

function buildFormatSummary(settings) {
  return [
    `标题 ${settings.headingSize}px`,
    `正文 ${settings.bodySize}px`,
    `行距 ${settings.lineHeight}`,
    `模块间距 ${settings.moduleGap}px`,
    `待办方框 ${settings.checkboxSize}px`,
    `一级缩进 ${settings.level1Indent}px`,
    `二级缩进 ${settings.level2Indent}px`,
    `圆点宽度 ${settings.bulletWidth}px`,
  ].join(" | ");
}
