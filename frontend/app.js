const params = new URLSearchParams(window.location.search);
const requestedDate = params.get("date");

const text = {
  unknownDate: "\u672a\u77e5\u65e5\u671f",
  unknownCity: "\u672a\u77e5\u57ce\u5e02",
  read: "\u6717\u8bfb",
  pause: "\u6682\u505c",
  loadError: "\u6ca1\u6709\u8bfb\u5230\u8f93\u51fa\u5305\u3002\u8bf7\u5148\u8fd0\u884c python .\\backend\\app\\morning_brief_demo.py --save\uff0c\u7136\u540e\u7528\u672c\u5730\u670d\u52a1\u5668\u6253\u5f00 frontend\u3002",
  reliability: "\u91cd\u8981\u7ed3\u8bba\u9700\u8981\u56de\u5230\u539f\u59cb\u6765\u6e90\u6838\u9a8c\u3002",
  steady: "\u4eca\u5929\u6211\u4eec\u7a33\u7a33\u63a8\u8fdb\u3002",
  emptyAsk: "\u4f60\u53ef\u4ee5\u95ee\u6211\uff1a\u4e3a\u4ec0\u4e48\u91cd\u8981\u3001\u8bc1\u636e\u662f\u4ec0\u4e48\u3001\u5f71\u54cd\u8c01\u3001\u4e0b\u4e00\u6b65\u770b\u4ec0\u4e48\u3001\u4eca\u5929\u4f1a\u63d0\u9192\u6211\u4ec0\u4e48\u3002",
  reminderReady: "\u4eca\u5929\u7684\u63d0\u9192\u5df2\u7ecf\u6574\u7406\u597d\u4e86\u3002",
  noMedicine: " \u76ee\u524d\u8fd8\u6ca1\u6709\u542f\u7528\u56fa\u5b9a\u5403\u836f\u63d0\u9192\u3002\u4f60\u53ef\u4ee5\u5728 backend/data/reminders.json \u91cc\u628a\u5403\u836f\u63d0\u9192\u6539\u4e3a enabled: true\u3002",
  reminderPanelTitle: "\u4e3b\u52a8\u63d0\u9192",
  reminderPanelSub: "\u7f51\u9875\u6253\u5f00\u65f6\u751f\u6548",
  enableNotify: "\u542f\u7528\u63d0\u9192",
  testNotify: "\u6d4b\u8bd5\u63d0\u9192",
  browserUnsupported: "\u6d4f\u89c8\u5668\u4e0d\u652f\u6301\u7cfb\u7edf\u901a\u77e5\uff0c\u4f46\u9875\u9762\u5185\u63d0\u9192\u4ecd\u53ef\u7528\u3002",
  notifyDenied: "\u901a\u77e5\u6743\u9650\u672a\u5f00\u542f\uff0c\u6682\u65f6\u53ea\u5728\u9875\u9762\u5185\u63d0\u9192\u3002",
  notifyOn: "\u5df2\u542f\u7528\u6d4f\u89c8\u5668\u63d0\u9192\u3002",
  noFuture: "\u4eca\u5929\u5269\u4f59\u65f6\u95f4\u6682\u65f6\u6ca1\u6709\u5f85\u89e6\u53d1\u63d0\u9192\u3002",
  scheduled: "\u5df2\u5b89\u6392",
  nextReminder: "\u4e0b\u4e00\u6761",
  reminderFallback: "\u63d0\u9192"
};

const keywords = {
  reminder: ["\u63d0\u9192", "\u53eb\u6211", "\u5230\u70b9", "\u5403\u836f", "\u4e3b\u52a8\u63d0\u9192", "\u51e0\u70b9\u63d0\u9192"],
  summary: ["\u603b\u7ed3", "\u603b\u89c8", "\u6700\u91cd\u8981", "\u91cd\u70b9", "\u4eca\u5929\u770b\u4ec0\u4e48"],
  sources: ["\u6765\u6e90", "\u6570\u636e\u6e90", "\u53ef\u9760\u5417", "\u53ef\u4fe1"],
  schedule: ["\u5f85\u529e", "\u65e5\u7a0b", "\u4eca\u5929\u505a\u4ec0\u4e48", "\u9879\u76ee"],
  memory: ["\u8bb0\u4f4f", "\u504f\u597d", "\u5173\u6ce8", "\u6211\u5173\u5fc3", "\u4f60\u77e5\u9053\u6211"],
  finance: ["\u8d22\u7ecf", "\u5e02\u573a", "\u80a1\u5e02", "\u6307\u6570", "\u884c\u4e1a", "\u516c\u53f8", "\u4e0a\u6da8", "\u4e0b\u8dcc", "\u539f\u56e0", "\u5f71\u54cd", "\u6838\u9a8c", "\u673a\u4f1a", "\u5165\u53e3", "\u94fe\u63a5", "\u5b98\u65b9", "\u53bb\u54ea", "\u54ea\u91cc", "\u62ab\u9732", "SEC", "8-K", "10-Q", "10-K", "20-F", "6-K"],
  evidence: ["\u8bc1\u636e", "\u4f9d\u636e", "\u4ece\u54ea"],
  impact: ["\u5f71\u54cd", "\u884c\u4e1a", "\u5bf9\u8c61", "\u8c01"],
  followup: ["\u4e0b\u4e00\u6b65", "\u6838\u9a8c", "\u770b\u4ec0\u4e48", "\u5173\u6ce8"],
  reason: ["\u539f\u56e0", "\u4e3a\u4ec0\u4e48"],
  filing: ["\u62ab\u9732", "SEC", "8-K", "10-Q", "10-K", "20-F", "6-K"]
};

const state = {
  bundle: null,
  avatarIndex: 0,
  reading: false,
  speechUtterance: null,
  reminderTimers: [],
  notificationsEnabled: false,
  voiceAudio: null,
  voiceAudioUrl: "",
  avatarTimer: null,
};

const cardGrid = document.querySelector("#cardGrid");
const sourceList = document.querySelector("#sourceList");
const speechList = document.querySelector("#speechList");
const readBtn = document.querySelector("#readBtn");
const nextAvatarBtn = document.querySelector("#nextAvatarBtn");
const askForm = document.querySelector("#askForm");
const askInput = document.querySelector("#askInput");
const askAnswer = document.querySelector("#askAnswer");

loadBundle();

readBtn.addEventListener("click", toggleRead);
nextAvatarBtn.addEventListener("click", nextAvatar);
askForm.addEventListener("submit", (event) => {
  event.preventDefault();
  answerQuestion(askInput.value);
});
document.querySelectorAll("[data-question]").forEach((button) => {
  button.addEventListener("click", () => {
    askInput.value = button.dataset.question || "";
    answerQuestion(askInput.value);
  });
});
initMotionTuner();

function initMotionTuner() {
  const controls = Array.from(document.querySelectorAll("[data-motion-path]"));
  const status = document.querySelector("#motionTunerStatus");
  const saveButton = document.querySelector("#saveMotionConfigBtn");
  if (!controls.length) return;

  const publish = () => {
    const patch = {};
    controls.forEach((control) => {
      const value = Number(control.value);
      setNestedMotionValue(patch, control.dataset.motionPath || "", Number.isFinite(value) ? value : control.value);
      const output = control.parentElement?.querySelector("output");
      if (output) output.textContent = control.value;
    });
    state.motionDraft = patch;
    if (status) status.textContent = "即时预览中";
    window.dispatchEvent(new CustomEvent("sunguo:motionConfigPatch", { detail: patch }));
  };

  controls.forEach((control) => {
    control.addEventListener("input", publish);
  });
  if (saveButton) saveButton.addEventListener("click", saveMotionConfig);
  publish();
}

async function saveMotionConfig() {
  const status = document.querySelector("#motionTunerStatus");
  const button = document.querySelector("#saveMotionConfigBtn");
  if (status) status.textContent = "正在保存";
  if (button) button.disabled = true;
  try {
    const response = await fetch("/api/motion/save", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ patch: state.motionDraft || {} })
    });
    const result = await response.json();
    if (!response.ok || result.ok === false) throw new Error(result.error || response.statusText);
    if (status) status.textContent = "已保存";
  } catch (error) {
    if (status) status.textContent = "保存失败: " + error.message;
  } finally {
    if (button) button.disabled = false;
  }
}

function setNestedMotionValue(target, path, value) {
  if (!path) return;
  const parts = path.split(".").filter(Boolean);
  let cursor = target;
  parts.forEach((part, index) => {
    if (index === parts.length - 1) {
      cursor[part] = value;
      return;
    }
    cursor[part] = cursor[part] || {};
    cursor = cursor[part];
  });
}

async function loadBundle() {
  const bundlePath = await resolveBundlePath();
  try {
    const response = await fetch(bundlePath, { cache: "no-store" });
    if (!response.ok) throw new Error(`Cannot read ${bundlePath}`);
    state.bundle = await response.json();
    render(state.bundle);
  } catch (error) {
    cardGrid.innerHTML = `<div class="error">${text.loadError}</div>`;
    console.error(error);
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

function render(bundle) {
  document.querySelector("#dateLabel").textContent = bundle.date || text.unknownDate;
  document.querySelector("#cityLabel").textContent = bundle.city || text.unknownCity;
  document.querySelector("#sourceLabel").textContent = requestedDate ? `fixed ${bundle.version || "output-v1"}` : `latest ${bundle.version || "output-v1"}`;
  state.voiceAudioUrl = bundle.speech_audio_path ? `../demos/${bundle.speech_audio_path}` : "";
  if (state.voiceAudio) {
    state.voiceAudio.pause();
    state.voiceAudio.currentTime = 0;
    state.voiceAudio = null;
  }
  state.reading = false;
  setReadButtonLabel(text.read);
  renderSources(bundle.source_summary || {});
  renderCards(bundle.screen_cards || []);
  renderSpeech(bundle.speech_script || []);
  renderAvatar(bundle.avatar_timeline || []);
  renderAvatar3d(getAvatar3dPayload(bundle));
  renderReminderPanel(bundle.reminder_plan || {});
}

function renderSources(summary) {
  const labels = { weather: "\u5929\u6c14", market: "\u5e02\u573a", news: "\u65b0\u95fb", themes: "\u4e3b\u9898", companies: "\u516c\u53f8", schedule: "\u65e5\u7a0b", memory: "\u8bb0\u5fc6" };
  sourceList.innerHTML = Object.entries(labels).map(([key, label]) => `<dt>${label}</dt><dd>${escapeHtml(summary[key] || "unknown")}</dd>`).join("");
  document.querySelector("#reliabilityNote").textContent = summary.reliability_note || text.reliability;
}

function renderCards(cards) {
  cardGrid.innerHTML = cards.map((card) => {
    const details = (card.details || []).map((item) => `<li>${escapeHtml(item)}</li>`).join("");
    return `<article class="brief-card ${card.priority || "normal"}"><div class="card-header"><h3>${escapeHtml(card.title || card.id)}</h3><span class="card-type">${escapeHtml(card.type || "card")}</span></div><p class="summary">${escapeHtml(card.summary || "")}</p><ul>${details}</ul><div class="card-source">source: ${escapeHtml(card.source || "unknown")}</div></article>`;
  }).join("");
}

function renderSpeech(script) {
  const voiceLabel = state.bundle?.speech_audio_path?.toLowerCase().endsWith(".mp3") ? "NEURAL" : (state.voiceAudioUrl ? "LOCAL" : "BROWSER");
  document.querySelector("#speechCount").textContent = `${script.length} \u6bb5 · ${voiceLabel}`;
  speechList.innerHTML = script.map((item, index) => `<li><div class="speech-meta">${index + 1}. ${escapeHtml(item.voice?.style || "clear")} \u00b7 ${item.voice?.pause_after_ms || 0}ms</div><p>${escapeHtml(item.text || "")}</p></li>`).join("");
}

function renderAvatar(timeline) {
  if (!timeline.length) return;
  const item = timeline[state.avatarIndex % timeline.length];
  const portrait = document.querySelector(".avatar-portrait");
  const mouth = item.mouth || (item.speaking ? "open" : "closed");
  const lipSync = item.lip_sync || (item.speaking ? "enabled" : "rest");
  portrait.dataset.expression = item.expression || "warm";
  portrait.dataset.gesture = item.gesture || "small_nod";
  portrait.dataset.mouth = mouth;
  portrait.dataset.lipsync = lipSync;
  portrait.dataset.section = item.section || "unknown";
  portrait.dataset.camera = item.camera || "medium";
  portrait.classList.toggle("speaking", Boolean(item.speaking));
  document.querySelector("#avatarCaption").textContent = item.caption || text.steady;
  document.querySelector("#avatarMeta").textContent = `expression: ${item.expression || "warm"} | gesture: ${item.gesture || "small_nod"} | camera: ${item.camera || "medium"}`;
  const avatarState = document.querySelector("#avatarState");
  if (avatarState) {
    avatarState.textContent = `mouth: ${mouth} | lip-sync: ${lipSync} | section: ${item.section || "unknown"}`;
  }
  window.dispatchEvent(new CustomEvent("sunguo:avatarMotion", { detail: { ...item, mouth, lip_sync: lipSync } }));
  scheduleAvatarMotion(timeline, item.duration_ms || 2600);
}

function getAvatar3dPayload(bundle) {
  const avatar3d = bundle.avatar_3d || {};
  if (avatar3d && Object.keys(avatar3d).length) return avatar3d;
  return buildClientAvatar3dFallback(bundle);
}

function buildClientAvatar3dFallback(bundle) {
  return {
    version: "client-avatar-3d-fallback-v1",
    avatar_profile: {
      name: "松果",
      body: { height_cm: 165, build: "balanced" },
      outfit: { default: "warm_home_butler_v1" },
      model_assets: {
        primary_vrm: "frontend/assets/avatar/sunguo.vrm",
        fallback: "low_poly_placeholder",
        supported_formats: ["vrm", "glb", "gltf"]
      }
    },
    runtime_state: {
      character_name: "松果",
      default_location: "briefing_spot",
      city: bundle.city || "北京-朝阳",
      date: bundle.date || getLocalDateText()
    },
    navigation_points: [
      { id: "briefing_spot", label: "Briefing spot", location: [0, 0, 0] },
      { id: "weather_window", label: "Weather window", location: [-1.2, 0, -0.55] },
      { id: "desk_console", label: "Desk console", location: [1.25, 0, -0.45] },
      { id: "reminder_corner", label: "Reminder corner", location: [0.35, 0, 0.85] }
    ],
    space_storyboard: [
      { location: "briefing_spot", action: "wave and greet", coordinates: [0, 0, 0], reason: "Start the morning brief as a personal butler." },
      { location: "weather_window", action: "turn to weather view", coordinates: [-1.2, 0, -0.55], reason: "Talk about weather and outfit suggestions." },
      { location: "desk_console", action: "point to market notes", coordinates: [1.25, 0, -0.45], reason: "Explain market and news highlights." },
      { location: "reminder_corner", action: "soft reminder gesture", coordinates: [0.35, 0, 0.85], reason: "Summarize tasks and life reminders." }
    ],
    asset_requirements: [
      { category: "model", target: "frontend/assets/avatar/sunguo.vrm", notes: "Use the exported VRoid VRM as the primary full-body character." },
      { category: "rig", target: "VRM humanoid bones", notes: "Keep standard humanoid rig for blinking, head movement, gestures, and later lip sync." },
      { category: "motion", target: "idle, wave, point, walk", notes: "Next step is to bind gesture clips to the avatar timeline." },
      { category: "space", target: "hologram base room", notes: "Use the current Three.js room as the prototype virtual space." }
    ]
  };
}
function renderAvatar3d(avatar3d) {
  if (!avatar3d || !Object.keys(avatar3d).length) return;
  const profile = avatar3d.avatar_profile || {};
  const runtime = avatar3d.runtime_state || {};
  const body = profile.body || {};
  const outfit = profile.outfit || {};
  const name = document.querySelector("#avatar3dName");
  if (name) name.textContent = profile.name || runtime.character_name || "Sunguo";
  const meta = document.querySelector("#avatar3dMeta");
  if (meta) {
    meta.textContent = `height ${body.height_cm || "?"}cm | build ${body.build || "balanced"} | outfit ${outfit.default || "daily_home_v1"}`;
  }
  const status = document.querySelector("#avatar3dStatus");
  if (status) {
    status.textContent = `${avatar3d.version || "avatar-3d"} | ${runtime.default_location || "briefing_spot"}`;
  }
  const routeHint = document.querySelector("#avatar3dRouteHint");
  const storyboard = avatar3d.space_storyboard || [];
  if (routeHint) {
    routeHint.textContent = storyboard.length
      ? `We already mapped ${storyboard.length} movement steps for the 3D butler, from entrance to weather, briefing, reminder, and closing.`
      : "The next step is to connect this package to modeling, rigging, and in-scene movement.";
  }
  const routeList = document.querySelector("#avatar3dRoute");
  if (routeList) {
    routeList.innerHTML = storyboard.map((item) => `<li><strong>${escapeHtml(item.location || "spot")}</strong> | ${escapeHtml(item.action || "idle")}<br /><span>${escapeHtml(item.reason || "")}</span></li>`).join("");
  }
  const assetList = document.querySelector("#avatar3dAssets");
  if (assetList) {
    assetList.innerHTML = (avatar3d.asset_requirements || []).map((item) => `<li><strong>${escapeHtml(item.category || "asset")}</strong> | ${escapeHtml(item.target || "")}<br /><span>${escapeHtml(item.notes || "")}</span></li>`).join("");
  }
  window.__sunguoAvatar3d = avatar3d;
  window.dispatchEvent(new CustomEvent("sunguo:avatar3d", { detail: avatar3d }));
}

function renderReminderPanel(plan) {
  let panel = document.querySelector("#reminderPanel");
  if (!panel) {
    panel = document.createElement("section");
    panel.id = "reminderPanel";
    panel.className = "reminder-panel";
    const avatarBand = document.querySelector(".avatar-band");
    avatarBand.insertAdjacentElement("afterend", panel);
  }
  const items = plan.items || [];
  const futureItems = getFutureReminders(items);
  const next = futureItems[0];
  panel.innerHTML = `<div><p class="eyebrow">Reminder Runtime</p><h2>${text.reminderPanelTitle}</h2><p id="reminderStatus">${escapeHtml(buildReminderRuntimeStatus(plan, futureItems))}</p></div><div class="reminder-next"><span>${text.nextReminder}</span><strong>${escapeHtml(next ? `${next.time} ${next.title}` : text.noFuture)}</strong></div><div class="reminder-actions"><button id="enableReminderBtn" type="button">${text.enableNotify}</button><button id="testReminderBtn" type="button">${text.testNotify}</button></div>`;
  document.querySelector("#enableReminderBtn").addEventListener("click", enableReminderRuntime);
  document.querySelector("#testReminderBtn").addEventListener("click", () => triggerReminder(items[0] || { title: text.reminderFallback, message: text.testNotify }));
  scheduleReminderRuntime(items);
}

function buildReminderRuntimeStatus(plan, futureItems) {
  if (!plan.items?.length) return "\u4eca\u5929\u6ca1\u6709\u4e3b\u52a8\u63d0\u9192\u8ba1\u5212\u3002";
  if (!futureItems.length) return `${plan.summary || text.reminderReady} ${text.noFuture}`;
  return `${plan.summary || text.reminderReady} ${text.scheduled} ${futureItems.length} \u6761\u5f85\u89e6\u53d1\u63d0\u9192\u3002`;
}

async function enableReminderRuntime() {
  if (!("Notification" in window)) {
    setReminderStatus(text.browserUnsupported);
    return;
  }
  if (Notification.permission === "default") await Notification.requestPermission();
  if (Notification.permission === "granted") {
    state.notificationsEnabled = true;
    setReminderStatus(text.notifyOn);
    scheduleReminderRuntime(state.bundle?.reminder_plan?.items || []);
  } else {
    setReminderStatus(text.notifyDenied);
  }
}

function scheduleReminderRuntime(items) {
  state.reminderTimers.forEach((timer) => clearTimeout(timer));
  state.reminderTimers = [];
  getFutureReminders(items).forEach((item) => {
    const delay = getReminderDelayMs(item.time);
    if (delay === null) return;
    const timer = window.setTimeout(() => triggerReminder(item), Math.min(delay, 2147483647));
    state.reminderTimers.push(timer);
  });
}

function triggerReminder(item) {
  const title = item.title || text.reminderFallback;
  const message = item.message || "";
  setReminderStatus(`${item.time || ""} ${title}\uff5c${message}`);
  speakText(`${title}\u3002${message}`, 1.02);
  if (state.notificationsEnabled && "Notification" in window && Notification.permission === "granted") {
    new Notification(`\u677e\u679c\u63d0\u9192\uff1a${title}`, { body: message, silent: false });
  }
}

function setReminderStatus(value) {
  const status = document.querySelector("#reminderStatus");
  if (status) status.textContent = value;
}

function getFutureReminders(items) {
  return (items || []).filter((item) => getReminderDelayMs(item.time) !== null).sort((a, b) => a.time.localeCompare(b.time));
}

function getReminderDelayMs(timeText) {
  if (!/^\d{2}:\d{2}$/.test(timeText || "")) return null;
  const [hours, minutes] = timeText.split(":").map(Number);
  const target = new Date();
  target.setHours(hours, minutes, 0, 0);
  const delay = target.getTime() - Date.now();
  return delay >= 0 ? delay : null;
}

function nextAvatar() {
  const timeline = state.bundle?.avatar_timeline || [];
  if (!timeline.length) return;
  state.avatarIndex = (state.avatarIndex + 1) % timeline.length;
  renderAvatar(timeline);
}

function scheduleAvatarMotion(timeline, durationMs) {
  if (state.avatarTimer) window.clearTimeout(state.avatarTimer);
  if (!timeline.length) return;
  const wait = Math.min(Math.max(Number(durationMs) || 2400, 1200), 6000);
  state.avatarTimer = window.setTimeout(() => {
    state.avatarIndex = (state.avatarIndex + 1) % timeline.length;
    renderAvatar(timeline);
  }, wait);
}

function toggleRead() {
  if (state.voiceAudioUrl) {
    toggleNativeVoice();
    return;
  }
  toggleBrowserVoice();
}

function toggleNativeVoice() {
  if (!state.voiceAudio || state.voiceAudio.src !== new URL(state.voiceAudioUrl, window.location.href).href) {
    state.voiceAudio = new Audio(state.voiceAudioUrl);
    state.voiceAudio.preload = "auto";
    state.voiceAudio.onplay = () => {
      state.reading = true;
      setReadButtonLabel(text.pause);
      setAvatarVoiceState(true);
    };
    state.voiceAudio.onpause = () => {
      state.reading = false;
      setReadButtonLabel(text.read);
      setAvatarVoiceState(false);
    };
    state.voiceAudio.onended = () => {
      state.reading = false;
      setReadButtonLabel(text.read);
      state.voiceAudio.currentTime = 0;
      setAvatarVoiceState(false);
    };
    state.voiceAudio.onerror = () => {
      console.warn("native voice unavailable, fallback to browser speech");
      state.voiceAudio = null;
      state.voiceAudioUrl = "";
      state.reading = false;
      setReadButtonLabel(text.read);
      setAvatarVoiceState(false);
      toggleBrowserVoice();
    };
  }

  if (state.voiceAudio.paused) {
    if (state.voiceAudio.ended) state.voiceAudio.currentTime = 0;
    state.voiceAudio.play().catch((error) => {
      console.warn("native voice play failed, fallback to browser speech", error);
      state.voiceAudio = null;
      state.voiceAudioUrl = "";
      state.reading = false;
      setReadButtonLabel(text.read);
      toggleBrowserVoice();
    });
  } else {
    state.voiceAudio.pause();
  }
}

function toggleBrowserVoice() {
  const script = state.bundle?.speech_script || [];
  if (!script.length || !("speechSynthesis" in window)) return;
  if (state.reading) {
    window.speechSynthesis.cancel();
    state.reading = false;
    setReadButtonLabel(text.read);
    setAvatarVoiceState(false);
    return;
  }
  const utterance = speakText(script.map((item) => item.text).join("\u3002"), 0.95);
  utterance.onend = () => {
    state.reading = false;
    setReadButtonLabel(text.read);
    setAvatarVoiceState(false);
  };
  state.speechUtterance = utterance;
  state.reading = true;
  setReadButtonLabel(text.pause);
  setAvatarVoiceState(true);
}

function setReadButtonLabel(label) {
  const buttonLabel = readBtn.querySelector("span:last-child");
  if (buttonLabel) buttonLabel.textContent = label;
}

function setAvatarVoiceState(speaking) {
  window.dispatchEvent(new CustomEvent("sunguo:voiceState", { detail: { speaking } }));
}

function speakText(value, rate = 0.95) {
  if (!("speechSynthesis" in window)) return { onend: null };
  window.speechSynthesis.cancel();
  const utterance = new SpeechSynthesisUtterance(value);
  utterance.lang = "zh-CN";
  utterance.rate = rate;
  utterance.pitch = 1.05;
  window.speechSynthesis.speak(utterance);
  return utterance;
}

async function answerQuestion(question) {
  const cleanQuestion = question.trim();
  askAnswer.innerHTML = `<p>松果正在查今天早报...</p>`;
  let result;
  try {
    result = await requestAskApi(cleanQuestion);
  } catch (error) {
    console.warn("ask api unavailable, fallback to local answer", error);
    result = buildLocalAnswer(state.bundle || {}, cleanQuestion);
  }
  renderAskAnswer(result);
}

async function requestAskApi(question) {
  const response = await fetch("/api/ask", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ question }) });
  const payload = await response.json();
  if (!response.ok || payload.ok === false) throw new Error(payload.error || response.statusText);
  return payload.result;
}

function renderAskAnswer(result) {
  const details = (result.details || []).map((item) => `<li>${escapeHtml(item)}</li>`).join("");
  const suggestions = (result.suggested_questions || []).slice(0, 4).map((item) => `<button type="button" data-follow-question="${escapeHtml(item)}">${escapeHtml(item)}</button>`).join("");
  askAnswer.innerHTML = `<p>${escapeHtml(result.answer)}</p><ul>${details}</ul>${suggestions ? `<div class="ask-followups">${suggestions}</div>` : ""}<div class="ask-source">source: ${escapeHtml(result.source || "local")}</div>`;
  askAnswer.querySelectorAll("[data-follow-question]").forEach((button) => {
    button.addEventListener("click", () => {
      askInput.value = button.dataset.followQuestion || "";
      answerQuestion(askInput.value);
    });
  });
}
function buildLocalAnswer(bundle, question) {
  const analysis = bundle.brief_analysis || {};
  const stories = analysis.top_stories || [];
  if (!question) return { answer: text.emptyAsk, details: [], source: "brief_analysis" };
  if (hasKeyword(question, keywords.reminder)) return buildReminderAnswer(bundle);
  if (hasKeyword(question, keywords.summary)) return { answer: analysis.today_overview || "\u4eca\u5929\u7684\u91cd\u70b9\u5df2\u7ecf\u6574\u7406\u5728\u4e09\u4ef6\u91cd\u8981\u4e8b\u91cc\u3002", details: stories.slice(0, 3).map((story, index) => `${index + 1}. ${story.title || "\u91cd\u8981\u4e8b\u9879"}`), source: "brief_analysis" };
  if (hasKeyword(question, keywords.sources)) return buildSourcesAnswer(bundle);
  if (hasKeyword(question, keywords.schedule)) return buildScheduleAnswer(bundle);
  if (hasKeyword(question, keywords.memory)) return buildMemoryAnswer(bundle);
  if (hasKeyword(question, keywords.finance)) return buildFinanceAnswer(bundle, question);
  return buildStoryAnswer(findStory(stories, question), question, stories);
}

function buildReminderAnswer(bundle) {
  const plan = bundle.reminder_plan || {};
  const details = (plan.items || []).slice(0, 12).map((item) => `${item.time || ""}\uff5c${item.title || text.reminderFallback}\uff5c${item.message || ""}`);
  let answer = plan.summary || text.reminderReady;
  if (!plan.medicine_configured) answer += text.noMedicine;
  return { answer, details, source: plan.version || "reminder_plan" };
}

function buildSourcesAnswer(bundle) {
  const summary = bundle.source_summary || {};
  return { answer: summary.reliability_note || text.reliability, details: [`\u5929\u6c14\uff1a${summary.weather || "unknown"}`, `\u5e02\u573a\uff1a${summary.market || "unknown"}`, `\u65b0\u95fb\uff1a${summary.news || "unknown"}`, `\u4e3b\u9898\uff1a${summary.themes || "unknown"}`, `\u516c\u53f8\uff1a${summary.companies || "unknown"}`, `\u65e5\u7a0b\uff1a${summary.schedule || "unknown"}`], source: "source_summary" };
}

function buildScheduleAnswer(bundle) {
  const schedule = (bundle.screen_cards || []).find((card) => card.id === "schedule");
  return { answer: schedule?.summary || "\u4eca\u5929\u5f85\u529e\u5df2\u6574\u7406\u3002", details: schedule?.details || [], source: schedule?.source || "schedule" };
}

function buildMemoryAnswer(bundle) {
  const memory = bundle.memory_summary || {};
  return { answer: "\u6211\u4f1a\u6309\u8fd9\u4e9b\u672c\u5730\u8bb0\u5fc6\u6765\u7ec4\u7ec7\u65e9\u62a5\u548c\u8ffd\u95ee\u56de\u7b54\u3002", details: [memory.regions?.length ? `\u5173\u6ce8\u56fd\u5bb6/\u5730\u533a\uff1a${memory.regions.join("\u3001")}` : "", memory.industries?.length ? `\u5173\u6ce8\u884c\u4e1a\uff1a${memory.industries.join("\u3001")}` : "", memory.companies?.length ? `\u5173\u6ce8\u516c\u53f8\uff1a${memory.companies.join("\u3001")}` : "", memory.life_reminders?.length ? `\u751f\u6d3b\u63d0\u9192\uff1a${memory.life_reminders.join("\u3001")}` : "", memory.current_priority ? `\u5f53\u524d\u9879\u76ee\u91cd\u70b9\uff1a${memory.current_priority}` : ""].filter(Boolean), source: "user_profile" };
}

function buildStoryAnswer(story, question, stories) {
  if (!story) return { answer: "\u6211\u73b0\u5728\u5148\u56f4\u7ed5\u4eca\u5929\u4e09\u4ef6\u91cd\u8981\u4e8b\u56de\u7b54\u3002", details: stories.slice(0, 3).map((item) => item.title || ""), source: "brief_analysis" };
  if (hasKeyword(question, keywords.evidence)) return { answer: "\u8fd9\u6761\u5224\u65ad\u76ee\u524d\u4e3b\u8981\u57fa\u4e8e\u8fd9\u4e9b\u8bc1\u636e\uff1a", details: [...(story.evidence || []), `\u53ef\u4fe1\u5ea6\uff1a${story.confidence || "\u5f85\u786e\u8ba4"}\uff5c\u6765\u6e90\uff1a${story.source || "unknown"}`], source: story.source || "brief_analysis" };
  if (hasKeyword(question, keywords.impact)) return { answer: "\u5b83\u4e3b\u8981\u5f71\u54cd\u8fd9\u4e9b\u5bf9\u8c61\uff1a", details: story.impact || [], source: story.source || "brief_analysis" };
  if (hasKeyword(question, keywords.followup)) return { answer: "\u4e0b\u4e00\u6b65\u5efa\u8bae\u8fd9\u6837\u6838\u9a8c\uff1a", details: [...(story.follow_up || []), `\u53ef\u4fe1\u5ea6\uff1a${story.confidence || "\u5f85\u786e\u8ba4"}\uff5c\u6765\u6e90\uff1a${story.source || "unknown"}`], source: story.source || "brief_analysis" };
  return { answer: story.why_it_matters || "\u8fd9\u6761\u503c\u5f97\u5173\u6ce8\uff0c\u56e0\u4e3a\u5b83\u4f1a\u5f71\u54cd\u4eca\u5929\u7684\u4fe1\u606f\u5224\u65ad\u987a\u5e8f\u3002", details: [...(story.evidence || []).slice(0, 2), ...(story.follow_up || []).slice(0, 2), `\u53ef\u4fe1\u5ea6\uff1a${story.confidence || "\u5f85\u786e\u8ba4"}\uff5c\u6765\u6e90\uff1a${story.source || "unknown"}`], source: story.source || "brief_analysis" };
}

function buildFinanceAnswer(bundle, question) {
  const finance = bundle.finance_reasoning || {};
  const items = selectFinanceItems(finance, question);
  if (!items.length) return { answer: finance.summary || "\u4eca\u5929\u8d22\u7ecf\u7ebf\u7d22\u4e0d\u8db3\uff0c\u5148\u4fdd\u6301\u89c2\u5bdf\u3002", details: finance.rules || [], source: "finance_reasoning" };
  if (hasKeyword(question, keywords.reason)) return { answer: "\u6211\u5148\u6309\u2018\u53ef\u80fd\u539f\u56e0\u2019\u6765\u56de\u7b54\uff0c\u4f46\u8fd9\u4e9b\u90fd\u9700\u8981\u7ee7\u7eed\u6838\u9a8c\u3002", details: items.slice(0, 5).map((item) => `${item.title || "\u8d22\u7ecf\u7ebf\u7d22"}\uff1a${item.possible_reason || "\u539f\u56e0\u5f85\u6838\u9a8c"}`), source: "finance_reasoning" };
  if (hasKeyword(question, keywords.impact)) return { answer: "\u8fd9\u4e9b\u7ebf\u7d22\u53ef\u80fd\u5f71\u54cd\u7684\u5bf9\u8c61\u4e3b\u8981\u662f\uff1a", details: items.slice(0, 5).map((item) => `${item.title || "\u8d22\u7ecf\u7ebf\u7d22"}\uff1a${item.impact || "\u5f71\u54cd\u5f85\u786e\u8ba4"}`), source: "finance_reasoning" };
  if (hasKeyword(question, keywords.filing)) return { answer: "\u6211\u67e5\u5230\u7684\u6700\u8fd1\u5b98\u65b9\u62ab\u9732\u662f\uff1a", details: items.slice(0, 5).map((item) => { const filing = (item.official_filings || [])[0]; return filing ? formatFilingAnswer(item, filing) : `${item.title || "\u8d22\u7ecf\u7ebf\u7d22"}\uff1a\u6682\u672a\u6293\u5230\u6700\u8fd1 SEC \u6587\u4ef6\uff0c\u5148\u770b\u516c\u53f8 IR \u548c SEC \u9875\u9762\u3002`; }), source: "finance_reasoning" };
  if (hasKeyword(question, keywords.followup)) return { answer: "\u4e0b\u4e00\u6b65\u5efa\u8bae\u8fd9\u6837\u6838\u9a8c\uff1a", details: items.slice(0, 5).map((item) => `${item.title || "\u8d22\u7ecf\u7ebf\u7d22"}\uff1a${(item.follow_up || []).slice(0, 2).join("\uff1b")}`), source: "finance_reasoning" };
  return { answer: finance.summary || "\u6211\u5df2\u7ecf\u6309\u4e8b\u5b9e\u3001\u539f\u56e0\u3001\u5f71\u54cd\u3001\u6838\u9a8c\u6574\u7406\u4e86\u8d22\u7ecf\u7ebf\u7d22\u3002", details: items.slice(0, 5).map((item) => `${item.title || "\u8d22\u7ecf\u7ebf\u7d22"}\uff5c\u4e8b\u5b9e\uff1a${item.fact || "\u5f85\u786e\u8ba4"}\uff5c\u53ef\u80fd\u539f\u56e0\uff1a${item.possible_reason || "\u5f85\u6838\u9a8c"}`), source: "finance_reasoning" };
}

function selectFinanceItems(finance, question) {
  if (hasKeyword(question, ["\u516c\u53f8", "\u82f1\u4f1f\u8fbe", "\u5fae\u8f6f", "AMD", "\u53f0\u79ef\u7535", "ASML", "\u516c\u544a", "\u8d22\u62a5"])) return filterCompanyItems(finance.companies || [], question);
  if (hasKeyword(question, ["\u884c\u4e1a", "\u677f\u5757", "\u4ef7\u683c", "\u5546\u54c1", "\u9ec4\u91d1", "\u94dc", "\u539f\u6cb9", "\u534a\u5bfc\u4f53ETF", "\u4e3b\u9898"])) return finance.themes || [];
  if (hasKeyword(question, ["\u5e02\u573a", "\u80a1\u5e02", "\u6307\u6570", "\u5927\u76d8", "\u4e2d\u56fd", "\u7f8e\u56fd", "\u65e5\u672c", "\u97e9\u56fd", "\u6b27\u6d32"])) return finance.market || [];
  return [...(finance.market || []), ...(finance.themes || []), ...(finance.companies || [])];
}

function filterCompanyItems(items, question) {
  const aliases = { "\u5fae\u8f6f": ["\u5fae\u8f6f", "MSFT", "Microsoft"], "\u82f1\u4f1f\u8fbe": ["\u82f1\u4f1f\u8fbe", "NVDA", "NVIDIA"], AMD: ["AMD"], "\u53f0\u79ef\u7535": ["\u53f0\u79ef\u7535", "TSM", "TSMC"], ASML: ["ASML"], "\u8c37\u6b4c": ["Alphabet", "GOOGL", "\u8c37\u6b4c", "Google"] };
  const tokens = Object.keys(aliases).filter((key) => question.includes(key)).flatMap((key) => aliases[key]).map((token) => token.toLowerCase());
  if (!tokens.length) return items;
  const filtered = items.filter((item) => tokens.some((token) => [item.title || "", item.fact || "", item.impact || ""].join(" ").toLowerCase().includes(token)));
  return filtered.length ? filtered : items;
}

function formatFilingAnswer(item, filing) {
  const summary = filing.document_summary || {};
  const items = (summary.items || []).slice(0, 3).join("\uff1b");
  const extra = items ? `\uff0c\u6458\u8981\uff1a${items}` : summary.title ? `\uff0c\u6807\u9898\uff1a${summary.title}` : "";
  return `${item.title || "\u8d22\u7ecf\u7ebf\u7d22"}\uff1a${filing.form || "\u62ab\u9732"}\uff0c\u63d0\u4ea4\u65e5 ${filing.filing_date || ""}${extra}\uff0c\u94fe\u63a5\uff1a${filing.url || ""}`;
}

function findStory(stories, question) {
  const ordinalMap = [["\u7b2c\u4e00", 0], ["\u7b2c1", 0], ["1", 0], ["\u7b2c\u4e8c", 1], ["\u7b2c2", 1], ["2", 1], ["\u7b2c\u4e09", 2], ["\u7b2c3", 2], ["3", 2]];
  for (const [keyword, index] of ordinalMap) if (question.includes(keyword) && stories[index]) return stories[index];
  return stories[0] || null;
}

function hasKeyword(question, list) {
  return list.some((keyword) => question.includes(keyword));
}

function escapeHtml(value) {
  return String(value).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;").replace(/'/g, "&#039;");
}

function getLocalDateText() {
  const now = new Date();
  return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, "0")}-${String(now.getDate()).padStart(2, "0")}`;
}








