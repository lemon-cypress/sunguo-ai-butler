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
  newsPanelOpen: {},
  newsRefreshPoll: null,
  awaitingFirstNews: false,
  stockWatchlist: [],
  stockSnapshot: [],
  mealPlan: null,
};

const newsSections = document.querySelector("#newsSections");
const newsSourceStrip = document.querySelector("#newsSourceStrip");
const todoList = document.querySelector("#todoList");
const todoForm = document.querySelector("#todoForm");
const todoTitleInput = document.querySelector("#todoTitleInput");
const todoNoteInput = document.querySelector("#todoNoteInput");
const deleteSelectedBtn = document.querySelector("#deleteSelectedBtn");
const stockSearchForm = document.querySelector("#stockSearchForm");
const stockSearchInput = document.querySelector("#stockSearchInput");
const stockSearchResults = document.querySelector("#stockSearchResults");
const stockWatchlist = document.querySelector("#stockWatchlist");
const refreshStocksBtn = document.querySelector("#refreshStocksBtn");
const mealPlan = document.querySelector("#mealPlan");
const mealStatus = document.querySelector("#mealStatus");

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
  await Promise.all([refreshNewsOnPageLoad(), loadTodos(), loadMealPlan()]);
  loadStockWatchlist();
  await loadBundle();
}

async function generateMealFromPreference(event, mealType, input) {
  event.preventDefault();
  const preference = input.value.trim();
  const label = mealType === "breakfast" ? "早餐" : "晚餐";
  if (!preference) {
    setMealStatus(`请先写下${label}想吃什么、忌口或现有食材。`, true);
    return;
  }
  const button = event.currentTarget.querySelector("button");
  button.disabled = true;
  setMealStatus(`正在按你的描述生成${label}…`);
  try {
    const result = await postJson("/api/meals/generate", { meal: mealType, preference });
    state.mealPlan[mealType] = result.data;
    renderMealPlan();
    setMealStatus(`已按你的描述更新${label}。`);
  } catch (error) {
    setMealStatus(error.message, true);
  } finally {
    button.disabled = false;
  }
}

async function loadMealPlan() {
  try {
    const response = await fetchWithTimeout("/api/meals", { cache: "no-store" }, 10000);
    if (!response.ok) throw new Error("无法读取餐谱");
    const result = await response.json();
    state.mealPlan = { breakfast: result.breakfast, dinner: result.dinner };
    renderMealPlan();
  } catch (error) {
    mealPlan.innerHTML = `<p class="stock-error">${escapeHtml(error.message)}</p>`;
  }
}

function setMealStatus(message = "", isError = false) {
  mealStatus.textContent = message;
  mealStatus.classList.toggle("is-error", isError);
}

function renderMealPlan() {
  if (!state.mealPlan?.breakfast || !state.mealPlan?.dinner) return;
  mealPlan.innerHTML = [
    renderMealCard("breakfast", state.mealPlan.breakfast),
    renderMealCard("dinner", state.mealPlan.dinner),
  ].join("");
  mealPlan.querySelectorAll(".meal-refresh-button").forEach((button) => {
    button.addEventListener("click", async () => {
      const mealType = button.dataset.mealType;
      button.disabled = true;
      setMealStatus(`正在换一份${mealType === "breakfast" ? "早餐" : "晚餐"}…`);
      try {
        const result = await postJson("/api/meals/refresh", { meal: mealType });
        state.mealPlan[mealType] = result.data;
        renderMealPlan();
        setMealStatus(`已换一份${mealType === "breakfast" ? "早餐" : "晚餐"}。`);
      } catch (error) {
        setMealStatus(error.message, true);
      }
    });
  });
  mealPlan.querySelectorAll(".meal-preference-form").forEach((form) => {
    form.addEventListener("submit", (event) => generateMealFromPreference(
      event,
      form.dataset.mealType,
      form.querySelector("input"),
    ));
  });
}

function renderMealCard(mealType, meal) {
  const items = Array.isArray(meal.items) ? meal.items : [];
  return `<article class="meal-card">
    <div class="meal-card-heading">
      <div class="meal-card-title"><span>${escapeHtml(meal.label || "餐谱")}</span><h3>${escapeHtml(meal.title || "今日餐谱")}</h3></div>
      <button class="meal-refresh-button" type="button" data-meal-type="${mealType}">换一换</button>
    </div>
    <form class="meal-preference-form" data-meal-type="${mealType}">
      <label>${mealType === "breakfast" ? "早餐想吃什么" : "晚餐想吃什么"}</label>
      <input type="text" maxlength="500" placeholder="${mealType === "breakfast" ? "例如：想吃热乎、不要甜，家里有鸡蛋和菠菜" : "例如：想吃清淡鱼类，家里有番茄和豆腐，不要辣"}" />
      <button type="submit">按描述生成${mealType === "breakfast" ? "早餐" : "晚餐"}</button>
    </form>
    <p class="meal-note">${escapeHtml(meal.summary || "")}</p>
    ${items.map((dish) => renderMealDish(dish)).join("")}
  </article>`;
}

function renderMealDish(dish) {
  const ingredients = Array.isArray(dish.ingredients) ? dish.ingredients : [];
  const steps = Array.isArray(dish.steps) ? dish.steps : [];
  return `<section class="meal-dish">
    <h4>${escapeHtml(dish.category || "菜品")}｜${escapeHtml(dish.name || "")}</h4>
    <div class="meal-dish-details">
      <div><h5>需要食材</h5><p>${ingredients.map((value) => escapeHtml(value)).join("、")}</p></div>
      <div><h5>制作步骤</h5><ol>${steps.map((value) => `<li>${escapeHtml(value)}</li>`).join("")}</ol></div>
    </div>
  </section>`;
}

stockSearchForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const query = stockSearchInput.value.trim();
  if (!query) return;
  stockSearchResults.textContent = "正在搜索…";
  try {
    const result = await postJson("/api/stocks/search", { query });
    renderStockSearchResults(result.items || [], query);
  } catch (error) {
    stockSearchResults.innerHTML = `<span class="stock-error">${escapeHtml(error.message)}</span>`;
  }
});

refreshStocksBtn.addEventListener("click", async () => {
  refreshStocksBtn.disabled = true;
  refreshStocksBtn.textContent = "刷新中…";
  try {
    const result = await postJson("/api/stocks/refresh", {});
    state.stockWatchlist = result.watchlist || [];
    state.stockSnapshot = result.items || [];
    renderStockWatchlist(result.error || "");
  } catch (error) {
    renderStockWatchlist(error.message);
  } finally {
    refreshStocksBtn.disabled = false;
    refreshStocksBtn.textContent = "刷新数据";
  }
});

async function loadStockWatchlist() {
  try {
    const response = await fetchWithTimeout("/api/stocks/watchlist", { cache: "no-store" }, 30000);
    if (!response.ok) throw new Error("无法读取自选股票");
    const result = await response.json();
    state.stockWatchlist = result.watchlist || [];
    state.stockSnapshot = result.items || [];
    renderStockWatchlist(result.error || "");
  } catch (error) {
    stockWatchlist.innerHTML = `<p class="stock-error">${escapeHtml(error.message)}</p>`;
  }
}

function renderStockSearchResults(items, query) {
  if (!items.length) {
    stockSearchResults.innerHTML = `<span class="stock-search-empty">未找到“${escapeHtml(query)}”。请输入 A 股六位代码，例如 000568。</span>`;
    return;
  }
  stockSearchResults.innerHTML = items.map((item) => `
    <button class="stock-result-add" type="button" data-symbol="${escapeAttribute(item.symbol)}" data-name="${escapeAttribute(item.name)}" data-sector="${escapeAttribute(item.sector || "")}">
      加入自选：${escapeHtml(item.name || item.symbol)} <span>${escapeHtml(item.symbol)}</span>
    </button>
  `).join("");
  stockSearchResults.querySelectorAll(".stock-result-add").forEach((node) => {
    node.addEventListener("click", async () => {
      await postJson("/api/stocks/add", {
        symbol: node.dataset.symbol,
        name: node.dataset.name,
        sector: node.dataset.sector,
      });
      stockSearchInput.value = "";
      stockSearchResults.textContent = "已加入自选；下次新闻刷新会开始定向关注。";
      await loadStockWatchlist();
    });
  });
}

function renderStockWatchlist(error = "") {
  const rowsBySymbol = new Map((state.stockSnapshot || []).map((row) => [row.symbol, row]));
  const items = state.stockWatchlist || [];
  if (!items.length) {
    stockWatchlist.innerHTML = `<p class="stock-empty">尚未加入自选股票。加入后才会进入新闻定向关注。</p>`;
    return;
  }
  const rows = items.map((stock) => {
    const data = rowsBySymbol.get(stock.symbol) || {};
    const quote = data.quote || {};
    const valuation = data.valuation || {};
    const financialSeries = data.financial_series || [];
    const change = Number(quote.change_percent);
    const changeClass = Number.isFinite(change) ? (change > 0 ? "is-up" : change < 0 ? "is-down" : "") : "";
    return `
      <div class="stock-line">
        <span class="stock-name"><b>${escapeHtml(stock.name || stock.symbol)}</b><em>${escapeHtml(stock.symbol)}</em></span>
        <span><small>价格</small>${formatStockNumber(quote.price)}<em>${escapeHtml(quote.date || "待更新")}</em></span>
        <span class="${changeClass}"><small>较前收盘</small>${formatPercent(quote.change_percent)}</span>
        <span><small>PE(TTM)</small>${formatStockNumber(valuation.pe_ttm)}</span>
        <div class="stock-financial-panels">
          ${renderFinancialPanel("收入", financialSeries, "revenue")}
          ${renderFinancialPanel("毛利率", financialSeries, "gross_margin")}
          ${renderFinancialPanel("净利润", financialSeries, "net_profit")}
        </div>
        <button class="stock-remove" type="button" data-symbol="${escapeAttribute(stock.symbol)}">移除</button>
      </div>`;
  }).join("");
  stockWatchlist.innerHTML = `${error ? `<p class="stock-error">${escapeHtml(error)}</p>` : ""}<div class="stock-head"><span>股票</span><span>最新交易日收盘价</span><span>涨跌幅</span><span>PE(TTM)</span>${renderFinancialHeader()}</div>${rows}`;
  stockWatchlist.querySelectorAll(".stock-remove").forEach((node) => {
    node.addEventListener("click", async () => {
      await postJson("/api/stocks/remove", { symbol: node.dataset.symbol });
      stockSearchResults.textContent = "已移除；后续新闻刷新不会再对该股定向关注。";
      await loadStockWatchlist();
    });
  });
}

function formatStockNumber(value) {
  const number = Number(value);
  return Number.isFinite(number) ? number.toFixed(number >= 100 ? 2 : 3).replace(/\.0+$/, "") : "—";
}

function formatPercent(value) {
  const number = Number(value);
  return Number.isFinite(number) ? `${number > 0 ? "+" : ""}${number.toFixed(2)}%` : "—";
}

function formatPercentRatio(value) {
  const number = Number(value);
  if (!Number.isFinite(number)) return "na";
  const percent = Math.abs(number) <= 1.5 ? number * 100 : number;
  return `${percent.toFixed(2)}%`;
}

function formatCurrency(value) {
  const number = Number(value);
  if (!Number.isFinite(number)) return "na";
  if (Math.abs(number) >= 1e8) return `${(number / 1e8).toFixed(2)}亿`;
  if (Math.abs(number) >= 1e4) return `${(number / 1e4).toFixed(2)}万`;
  return number.toFixed(2);
}

function renderFinancialPanel(title, rawSeries, metric) {
  const expected = ["25Q3", "25Q4", "26Q1", "26Q2"];
  const rows = new Map(rawSeries.map((row) => [row.label, row]));
  const cells = expected.map((label) => {
    const row = rows.get(label) || {};
    const available = Boolean(row.available);
    let value = "na";
    let sub = "";
    if (available && metric === "revenue") {
      value = formatCurrency(row.revenue);
      sub = `同比 ${formatSignedPercentRatio(row.revenue_yoy)}`;
    } else if (available && metric === "gross_margin") {
      value = formatPercentRatio(row.gross_margin);
    } else if (available && metric === "net_profit") {
      value = formatCurrency(row.net_profit);
      sub = `净利率 ${formatPercentRatio(row.net_margin)}`;
    }
    return `<span class="financial-quarter"><b>${value}</b>${sub ? `<span class="financial-sub">${sub}</span>` : ""}</span>`;
  }).join("");
  return `<section class="financial-panel"><div class="financial-quarter-list">${cells}</div></section>`;
}

function formatSignedPercentRatio(value) {
  const number = Number(value);
  if (!Number.isFinite(number)) return "na";
  const percent = Math.abs(number) <= 1.5 ? number * 100 : number;
  return `${percent > 0 ? "+" : ""}${percent.toFixed(2)}%`;
}

function renderFinancialHeader() {
  const labels = ["25Q3", "25Q4", "26Q1", "26Q2"];
  const panels = ["收入", "毛利率", "净利润"].map((title) => `
    <section class="financial-panel financial-panel-head">
      <b>${title}</b>
      <div class="financial-quarter-list">${labels.map((label) => `<span>${label}</span>`).join("")}</div>
    </section>`).join("");
  return `<div class="stock-financial-panels stock-financial-header">${panels}</div>`;
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
  bindCollapsibleNewsSections();
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
  const content = pool.content_extraction || {};

  if (!raw && !editorial) {
    return renderTextSection("新闻池摘要", `<p class="pool-empty">新闻池数据将在下一次刷新后显示。</p>`, "", true);
  }

  return renderTextSection("新闻池摘要", `
    <p class="pool-funnel">本次从 <b>${raw}</b> 条原始信息中筛出 <b>${ranked}</b> 条相关候选，聚类为 <b>${clustered}</b> 个事件，最终保留 <b>${editorial}</b> 条可展示事实。</p>
    <p class="pool-sources"><b>已摘录渠道：</b>${sourceCounts.length ? sourceCounts.map(([name, count]) => `<span>${escapeHtml(name)} ${count}条</span>`).join("、") : "待刷新"}</p>
    ${content.attempted ? `<p class="pool-content"><b>正文增强：</b>尝试 ${Number(content.attempted) || 0} 篇，新提取 ${Number(content.extracted) || 0} 篇，缓存命中 ${Number(content.cached) || 0} 篇。</p>` : ""}
    ${reasons.length ? `<p class="pool-reasons"><b>主要过滤：</b>${reasons.map(([name, count]) => `${escapeHtml(name)} ${count}条`).join("；")}</p>` : ""}
  `, "", true);
}

function renderTextSection(title, content, className = "", collapsible = false) {
  if (collapsible) {
    const isOpen = Boolean(state.newsPanelOpen[title]);
    return `
      <details class="news-section news-section-collapsible ${className}" data-collapse-key="${escapeAttribute(title)}"${isOpen ? " open" : ""}>
        <summary class="news-section-title-row">
          <span class="news-dot"></span>
          <h3>${escapeHtml(title)}</h3>
          <span class="collapse-indicator" aria-hidden="true"></span>
        </summary>
        <div class="news-section-content">${content}</div>
      </details>
    `;
  }
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

function bindCollapsibleNewsSections() {
  newsSections.querySelectorAll(".news-section-collapsible").forEach((node) => {
    node.addEventListener("toggle", () => {
      state.newsPanelOpen[node.dataset.collapseKey] = node.open;
    });
  });
}

function rememberNewsPanelStates() {
  newsSections.querySelectorAll(".news-section-collapsible").forEach((node) => {
    state.newsPanelOpen[node.dataset.collapseKey] = node.open;
  });
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
  `, "media-selection-section", true);
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
      rememberNewsPanelStates();
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
