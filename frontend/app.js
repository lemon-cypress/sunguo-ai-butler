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

const HIDDEN_SECTIONS = new Set(["财秘关注", "财秘追踪", "财富聚焦"]);

const state = {
  bundle: null,
  todos: [],
  selectedMediaSources: null,
  newsRefreshPoll: null,
  awaitingFirstNews: false,
};

const newsSections = document.querySelector("#newsSections");
const newsSourceStrip = document.querySelector("#newsSourceStrip");
const todoList = document.querySelector("#todoList");
const todoForm = document.querySelector("#todoForm");
const todoTitleInput = document.querySelector("#todoTitleInput");
const todoNoteInput = document.querySelector("#todoNoteInput");
const deleteSelectedBtn = document.querySelector("#deleteSelectedBtn");

bootstrap();

todoForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const title = todoTitleInput.value.trim();
  if (!title) return;
  await postJson("/api/todos/add", { title, note: todoNoteInput.value.trim(), completed: false });
  todoTitleInput.value = "";
  todoNoteInput.value = "";
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
  await Promise.all([refreshNewsOnPageLoad(), loadTodos()]);
  await loadBundle();
}

async function refreshNewsOnPageLoad() {
  setNewsLoading("正在载入新闻…");
  try {
    const response = await fetchWithTimeout("/api/news/refresh", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: "{}",
    }, 12000);
    const result = await response.json();
    if (!response.ok || result.ok === false) throw new Error(result.error || "新闻池刷新失败");
    if (result.running) {
      state.awaitingFirstNews = true;
      watchNewsRefresh();
    }
  } catch (error) {
    console.warn("news refresh failed; loading last available bundle", error);
    setNewsLoading("正在载入上一次成功新闻…");
  }
}

function watchNewsRefresh() {
  if (state.newsRefreshPoll) window.clearInterval(state.newsRefreshPoll);
  let attempts = 0;
  state.newsRefreshPoll = window.setInterval(async () => {
    attempts += 1;
    try {
      const response = await fetchWithTimeout("/api/news/status", { cache: "no-store" }, 8000);
      const result = await response.json();
      if (!result.running) {
        window.clearInterval(state.newsRefreshPoll);
        state.newsRefreshPoll = null;
        if (!result.last_error) {
          state.awaitingFirstNews = false;
          await loadBundle();
        }
      }
    } catch (error) {
      console.warn("news refresh status unavailable", error);
    }
    if (attempts >= 90 && state.newsRefreshPoll) {
      window.clearInterval(state.newsRefreshPoll);
      state.newsRefreshPoll = null;
    }
  }, 2000);
}

async function loadBundle() {
  const bundlePath = await resolveBundlePath();
  try {
    const response = await fetchWithTimeout(bundlePath, { cache: "no-store" });
    if (!response.ok) throw new Error(`Cannot read ${bundlePath}`);
    state.bundle = await response.json();
    renderBundle();
  } catch (error) {
    console.error(error);
    if (state.awaitingFirstNews) {
      document.querySelector("#dateLabel").textContent = "正在生成首份新闻…";
      newsSections.innerHTML = `<article class="empty-state">首次打开正在汇集新闻，完成后会自动显示，无需再次刷新。</article>`;
    } else {
      document.querySelector("#dateLabel").textContent = "新闻加载失败";
      newsSections.innerHTML = `<article class="empty-state error-state">${escapeHtml(TEXT.loadError)}</article>`;
    }
  }
}

async function loadTodos() {
  try {
    const response = await fetchWithTimeout("/api/todos", { cache: "no-store" });
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
    const response = await fetchWithTimeout("../demos/latest.json", { cache: "no-store" });
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
              ${item.note ? `<span>${escapeHtml(item.note)}</span>` : ""}
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
  const pool = bundle.news_pool_audit || digest.news_pool || {};
  const sections = (digest.sections || []).filter((section) => !HIDDEN_SECTIONS.has(section.title));
  const cardsById = new Map((pool.top_candidates || []).map((card) => [card.id, card]));
  const sourceNames = String((bundle.source_summary || {}).news || "")
    .split(" + ")
    .filter(Boolean)
    .slice(0, 5);

  newsSourceStrip.innerHTML = sourceNames.map((source) => `<span>${escapeHtml(source)}</span>`).join("");

  if (!sections.length) {
    newsSections.innerHTML = `<article class="empty-state">${escapeHtml(TEXT.newsEmpty)}</article>`;
    return;
  }

  newsSections.innerHTML = [
    renderNewsPoolSection(pool),
    renderMediaSelectionSection(pool),
    ...sections.map((section) => renderNewsSection(section, cardsById)),
  ].join("");
  bindMediaSelection(pool);
}

function renderNewsPoolSection(pool) {
  const stages = pool.stage_counts || {};
  const sourceCounts = Object.entries(pool.source_counts || {}).slice(0, 10);
  const reasons = Object.entries(pool.rejection_reasons || {}).slice(0, 4);
  const raw = stages.raw ?? pool.total_candidates ?? 0;
  const ranked = stages.ranked ?? pool.ranked_candidates ?? 0;
  const clustered = stages.clustered ?? pool.clustered_candidates ?? ranked;
  const editorial = stages.editorial ?? pool.editorial_candidates ?? 0;

  if (!raw && !editorial) {
    return renderTextSection("新闻池摘要", `<p class="pool-empty">新闻池数据将在下一次刷新后显示。</p>`);
  }

  return renderTextSection("新闻池摘要", `
    <p class="pool-funnel">本次从 <b>${raw}</b> 条原始信息中筛出 <b>${ranked}</b> 条相关候选，聚类为 <b>${clustered}</b> 个事件，最终保留 <b>${editorial}</b> 条可展示事实。</p>
    <p class="pool-sources"><b>已摘录渠道：</b>${sourceCounts.length ? sourceCounts.map(([name, count]) => `<span>${escapeHtml(name)} ${count}条</span>`).join("、") : "待刷新"}</p>
    ${reasons.length ? `<p class="pool-reasons"><b>主要过滤：</b>${reasons.map(([name, count]) => `${escapeHtml(name)} ${count}条`).join("；")}</p>` : ""}
  `);
}

function renderTextSection(title, content, className = "") {
  return `
    <article class="news-section ${className}">
      <div class="news-section-title-row">
        <span class="news-dot"></span>
        <h3>${escapeHtml(title)}</h3>
      </div>
      <div class="news-section-content">${content}</div>
    </article>
  `;
}

function renderMediaSelectionSection(pool) {
  const candidates = mediaCandidates(pool);
  const sources = mediaSourceOptions(candidates);
  if (!sources.length) return "";
  if (state.selectedMediaSources === null) {
    state.selectedMediaSources = new Set(sources.slice(0, 6).map(([source]) => source));
  }
  const selected = state.selectedMediaSources;
  const visible = candidates
    .filter((item) => selected.has(item.source))
    .sort((left, right) => mediaScore(right) - mediaScore(left) || String(right.time).localeCompare(String(left.time)))
    .slice(0, 24);
  const controls = sources.map(([source, count]) => `
    <label class="media-choice"><input type="checkbox" value="${escapeHtml(source)}" ${selected.has(source) ? "checked" : ""} />
      <span>${escapeHtml(source)}</span><em>${count}</em>
    </label>
  `).join("");
  const rows = visible.length
    ? visible.map((item) => `
      <li class="media-article">
        <span class="media-article-score">${mediaScore(item)}</span>
        <a href="${escapeAttribute(safeExternalUrl(item.url))}" target="_blank" rel="noopener noreferrer">${escapeHtml(item.title || TEXT.newsClue)}</a>
        ${item.title_zh ? `<span class="media-article-translation">（${escapeHtml(item.title_zh)}）</span>` : ""}
        <span class="media-article-source">${escapeHtml(item.source || "")}</span>
      </li>
    `).join("")
    : `<li class="pool-empty">勾选上方媒体后，这里会列出新闻池中的原文标题。</li>`;
  return renderTextSection("主流媒体选读", `
    <p class="media-help">选择媒体后，只列出新闻池中的原文标题；英文标题后附中文翻译，点击英文标题可打开原文。数字为重要性分值。</p>
    <div class="media-choices" id="mediaChoices">${controls}</div>
    <ol class="media-article-list">${rows}</ol>
  `, "media-selection-section");
}

function mediaCandidates(pool) {
  const items = pool.media_candidates || pool.top_candidates || [];
  const seen = new Set();
  return items.filter((item) => {
    const key = `${item.source}|${item.title}`;
    if (!item.source || !item.title || !item.url || seen.has(key)) return false;
    seen.add(key);
    return true;
  });
}

function mediaSourceOptions(candidates) {
  const counts = new Map();
  candidates.forEach((item) => counts.set(item.source, (counts.get(item.source) || 0) + 1));
  return [...counts.entries()]
    .sort((left, right) => right[1] - left[1] || left[0].localeCompare(right[0], "zh-CN"))
    .slice(0, 18);
}

function bindMediaSelection(pool) {
  document.querySelectorAll("#mediaChoices input").forEach((node) => {
    node.addEventListener("change", () => {
      if (node.checked) state.selectedMediaSources.add(node.value);
      else state.selectedMediaSources.delete(node.value);
      renderNews(state.bundle);
    });
  });
}

function renderNewsSection(section, cardsById) {
  const items = [...(section.items || [])]
    .filter(isChineseNewsEntry)
    .sort((left, right) => scoreForEntry(right, cardsById) - scoreForEntry(left, cardsById));
  if (!items.length) return "";
  return `
    <article class="news-section">
      <div class="news-section-title-row">
        <span class="news-dot"></span>
        <h3>${escapeHtml(section.title || TEXT.newsClue)}</h3>
      </div>
      <div class="news-sublist">
        ${items.map((entry) => renderNewsEntry(entry, cardsById.get(entry.card_id))).join("")}
      </div>
    </article>
  `;
}

function isChineseNewsEntry(entry) {
  const title = String(entry?.thesis || "");
  const summary = String(entry?.summary || "");
  return /[\u4e00-\u9fff]/.test(title) && (!summary || /[\u4e00-\u9fff]/.test(summary));
}

function renderNewsEntry(entry, card = {}) {
  const score = Number(entry.importance_score || card.importance_score || card.score || 0);
  const clusterSize = Number(entry.cluster_size || card.cluster_size || 1);
  const source = entry.source || card.source || "";
  const sourceLabel = clusterSize > 1 ? `${clusterSize}个来源交叉印证` : source;
  const timePrefix = entry.time ? `<time>${escapeHtml(formatNewsTime(entry.time))}</time>` : "";
  const thesis = escapeHtml(entry.thesis || TEXT.newsClue);
  const summary = escapeHtml(entry.summary || "");
  return `
    <p class="news-line">
      <span class="news-line-meta">${timePrefix}${sourceLabel ? ` · ${escapeHtml(sourceLabel)}` : ""}</span>
      <span class="news-line-score">${score ? Math.min(100, Math.round(score)) : "—"}</span>
      <span class="news-line-copy"><b>${thesis}</b>${summary ? `：${summary}` : ""}</span>
    </p>
  `;
}

function scoreForEntry(entry, cardsById) {
  const card = cardsById.get(entry.card_id) || {};
  return Number(entry.importance_score || card.importance_score || card.score || 0);
}

function mediaScore(item) {
  return Math.min(100, Math.round(Number(item.importance_score || item.score || 0)));
}

function formatNewsTime(value) {
  const text = String(value || "").replace("T", " ");
  return text.length >= 16 ? text.slice(5, 16) : text;
}

async function postJson(url, payload) {
  const response = await fetchWithTimeout(url, {
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

function setNewsLoading(message) {
  document.querySelector("#dateLabel").textContent = message;
}

async function fetchWithTimeout(url, options = {}, timeoutMs = 20000) {
  const controller = new AbortController();
  const timer = window.setTimeout(() => controller.abort(), timeoutMs);
  try {
    return await fetch(url, { ...options, signal: controller.signal });
  } finally {
    window.clearTimeout(timer);
  }
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

function escapeAttribute(value) {
  return escapeHtml(value).replaceAll("'", "&#39;");
}

function safeExternalUrl(value) {
  try {
    const parsed = new URL(String(value || ""));
    return ["http:", "https:"].includes(parsed.protocol) ? parsed.href : "#";
  } catch (error) {
    return "#";
  }
}
