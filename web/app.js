const API = "";
let data = null;
let activeTheme = "All";
let chatHistory = [];
let chatOpen = false;

const views = {
  login: document.getElementById("view-login"),
  processing: document.getElementById("view-processing"),
  report: document.getElementById("view-report"),
};

function showView(name) {
  Object.entries(views).forEach(([key, el]) => {
    el.classList.toggle("active", key === name);
  });
}

function getSession() {
  try {
    return JSON.parse(localStorage.getItem("savedna_session") || "null");
  } catch {
    return null;
  }
}

function setSession(session) {
  localStorage.setItem("savedna_session", JSON.stringify(session));
}

async function api(path, options = {}) {
  const res = await fetch(`${API}${path}`, {
    headers: { "Content-Type": "application/json", ...options.headers },
    ...options,
  });
  const body = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(body.error || res.statusText);
  return body;
}

// ─── Login ───────────────────────────────────────────────────

document.getElementById("btn-login").addEventListener("click", async () => {
  const username = document.getElementById("username").value.trim().replace(/^@/, "");
  const btn = document.getElementById("btn-login");
  btn.disabled = true;
  btn.textContent = "Connecting…";
  try {
    const auth = await api("/api/auth/login", {
      method: "POST",
      body: JSON.stringify({ username }),
    });
    const job = await api("/api/analyze/start", { method: "POST" });
    setSession({ token: auth.token, username: auth.username, jobId: job.id });
    showView("processing");
    pollJob(job.id);
  } catch (err) {
    alert(err.message);
    btn.disabled = false;
    btn.textContent = "Connect & analyze saves";
  }
});

// ─── Processing ──────────────────────────────────────────────

async function pollJob(jobId) {
  const fill = document.getElementById("progress-fill");
  const pct = document.getElementById("progress-pct");
  const label = document.getElementById("processing-label");
  const steps = document.querySelectorAll("#step-list li");

  const tick = async () => {
    try {
      const job = await api(`/api/analyze/status/${jobId}`);
      fill.style.width = `${job.progress}%`;
      pct.textContent = `${job.progress}%`;
      label.textContent = job.label || "Working…";

      const order = ["connect", "fetch", "transcribe", "analyze"];
      const idx = order.indexOf(job.step);
      steps.forEach((li, i) => {
        li.classList.toggle("done", i < idx || job.status === "done");
        li.classList.toggle("active", i === idx && job.status === "running");
      });

      if (job.status === "done") {
        fill.style.width = "100%";
        pct.textContent = "100%";
        steps.forEach(li => li.classList.add("done"));
        setTimeout(() => loadReport(), 600);
        return;
      }
      if (job.status === "error") {
        label.textContent = `Error: ${job.error}`;
        return;
      }
      setTimeout(tick, 800);
    } catch (err) {
      label.textContent = err.message;
    }
  };
  tick();
}

// ─── Report ──────────────────────────────────────────────────

async function loadReport() {
  try {
    data = await api("/api/report");
    showView("report");
    render();
    if (!chatHistory.length) {
      addChatMessage("assistant",
        "I've read your save profile. Ask me anything — themes, patterns, what you're optimizing for, or how your saves connect to your goals.");
    }
  } catch (err) {
    alert(err.message);
    showView("login");
  }
}

function formatDate(iso) {
  if (!iso) return "Unknown date";
  return new Date(iso + "T12:00:00").toLocaleDateString("en-US", {
    month: "short", day: "numeric", year: "numeric",
  });
}

function escapeHtml(str) {
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function renderStats() {
  const { stats } = data;
  const session = getSession();
  document.getElementById("subtitle").textContent =
    `@${session?.username || data.username} · ${stats.transcribed} saves analyzed · ${stats.total_words.toLocaleString()} words`;

  document.getElementById("stats").innerHTML = [
    { label: "Videos saved", value: stats.total_videos },
    { label: "Transcribed", value: stats.transcribed },
    { label: "Pending", value: stats.pending },
    { label: "Words captured", value: stats.total_words.toLocaleString() },
  ].map(s => `<div class="stat"><strong>${s.value}</strong><span>${s.label}</span></div>`).join("");
}

function renderThemes() {
  const max = Math.max(...data.themes.map(t => t.count), 1);
  document.getElementById("themes").innerHTML = data.themes.map(t => `
    <div class="theme-row">
      <label>${escapeHtml(t.name)}</label>
      <div class="bar-track"><div class="bar-fill" style="width:${(t.count / max) * 100}%"></div></div>
      <em>${t.pct}%</em>
    </div>`).join("");
}

function renderInsights() {
  document.getElementById("insights").innerHTML = data.insights.map(i => `
    <article class="insight-card">
      <h3>${escapeHtml(i.title)}</h3>
      <p>${escapeHtml(i.body)}</p>
      <div class="insight-tags">${i.tags.map(t => `<span class="tag">${escapeHtml(t)}</span>`).join("")}</div>
    </article>`).join("");
}

function saveCard(item, compact = false) {
  const excerpt = item.excerpt
    ? `<p>${escapeHtml(item.excerpt)}</p>`
    : `<p><em>No transcript yet</em></p>`;
  return `
    <article class="save-card">
      <div class="save-meta">
        <span>${formatDate(item.date)}</span>
        <span class="pill-theme">${escapeHtml(item.theme)}</span>
        ${item.word_count ? `<span>${item.word_count} words</span>` : ""}
      </div>
      <h3>${escapeHtml(item.caption)}</h3>
      ${excerpt}
    </article>`;
}

function renderFeatured() {
  document.getElementById("featured").innerHTML =
    data.featured_saves.map(i => saveCard(i)).join("") || `<p class="empty">None yet.</p>`;
}

function renderRecent() {
  document.getElementById("recent").innerHTML =
    data.recent_saves.map(i => saveCard(i)).join("") || `<p class="empty">None yet.</p>`;
}

function renderFilters() {
  const themes = ["All", ...new Set(data.items.map(i => i.theme))];
  document.getElementById("filters").innerHTML = themes.map(t => `
    <button class="filter-btn ${t === activeTheme ? "active" : ""}" data-theme="${escapeHtml(t)}">${escapeHtml(t)}</button>
  `).join("");
  document.querySelectorAll(".filter-btn").forEach(btn => {
    btn.onclick = () => { activeTheme = btn.dataset.theme; renderFilters(); renderAllSaves(); };
  });
}

function renderAllSaves() {
  const q = document.getElementById("search").value.trim().toLowerCase();
  const items = data.items.filter(item => {
    if (activeTheme !== "All" && item.theme !== activeTheme) return false;
    if (!q) return item.has_transcript;
    return item.has_transcript && `${item.caption} ${item.excerpt}`.toLowerCase().includes(q);
  });
  const el = document.getElementById("all-saves");
  el.innerHTML = items.slice(0, 80).map(i => saveCard(i, true)).join("") ||
    `<p class="empty">No matches.</p>`;
}

function render() {
  renderStats();
  renderPersonality();
  renderThemes();
  renderInsights();
  renderQuoteWall();
  renderFeatured();
  renderRecent();
  renderFilters();
  renderAllSaves();
}

document.getElementById("search")?.addEventListener("input", renderAllSaves);

// ─── Personality Card ────────────────────────────────────────

const ARCHETYPES = [
  { min: "Business & Tech", icon: "🔧", name: "The Systems Builder", desc: "You optimize both inner and outer worlds — building frameworks for life and work simultaneously." },
  { min: "Self & Mindset", icon: "🪞", name: "The Inner Cartographer", desc: "You're mapping your own psyche — identity, patterns, and the stories running beneath the surface." },
  { min: "Relationships", icon: "🤝", name: "The Connector", desc: "You study how humans bond, break, and rebuild — seeking depth in every interaction." },
  { min: "Fitness & Health", icon: "⚡", name: "The Foundation Layer", desc: "You know the body is the base — everything else is built on physical and mental stability." },
  { min: "Culture & Music", icon: "🎵", name: "The Curator", desc: "You collect vibes, sounds, and cultural moments that feed your creative identity." },
];

function renderPersonality() {
  const top = data.themes[0];
  const second = data.themes[1];
  const arch = ARCHETYPES.find(a => a.min === top.name) || ARCHETYPES[0];
  document.getElementById("personality-card").innerHTML = `
    <div class="personality-badge">${arch.icon}</div>
    <div class="personality-text">
      <h3>${arch.name}</h3>
      <p>${top.pct}% ${top.name.toLowerCase()}, ${second.pct}% ${second.name.toLowerCase()} — ${arch.desc}</p>
    </div>`;
}

// ─── Quote Wall ──────────────────────────────────────────────

const PULL_QUOTES = [
  { text: "You become the thoughts you repeat every single day.", date: "May 2026" },
  { text: "The most flexible element controls the entire system. Not the strongest, not the loudest — the most flexible.", date: "Apr 2026" },
  { text: "People do not bond with the version of you who has everything figured out.", date: "May 2026" },
  { text: "Scarcity repels abundance. The fear itself is what keeps it from you.", date: "May 2026" },
  { text: "How do you know you're on your path? Because it disappears.", date: "Jul 2025" },
  { text: "Suppression of expression leads to depression.", date: "May 2025" },
  { text: "A good life is something you build, not something you find.", date: "May 2026" },
  { text: "Your nervous system chooses your relationships before your brain does.", date: "May 2026" },
];

function renderQuoteWall() {
  document.getElementById("quote-wall").innerHTML = PULL_QUOTES.map(q => `
    <div class="quote-card">
      <blockquote>"${escapeHtml(q.text)}"</blockquote>
      <cite>— from your saves, ${q.date}</cite>
    </div>`).join("");
}

// ─── Chat ────────────────────────────────────────────────────

function toggleChat(open) {
  chatOpen = open;
  document.getElementById("chat-panel").classList.toggle("open", open);
  document.getElementById("chat-backdrop").classList.toggle("open", open);
  if (open) document.getElementById("chat-input").focus();
}

document.getElementById("btn-chat-toggle").addEventListener("click", () => toggleChat(true));
document.getElementById("btn-chat-close").addEventListener("click", () => toggleChat(false));
document.getElementById("chat-backdrop").addEventListener("click", () => toggleChat(false));

document.querySelectorAll(".prompt-chip").forEach(chip => {
  chip.addEventListener("click", () => {
    document.getElementById("chat-input").value = chip.textContent;
    document.getElementById("chat-form").dispatchEvent(new Event("submit", { cancelable: true }));
  });
});

function addChatMessage(role, content, loading = false) {
  const el = document.getElementById("chat-messages");
  const div = document.createElement("div");
  div.className = `chat-msg ${role}${loading ? " loading" : ""}`;
  div.textContent = content;
  el.appendChild(div);
  el.scrollTop = el.scrollHeight;
  return div;
}

document.getElementById("chat-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const input = document.getElementById("chat-input");
  const message = input.value.trim();
  if (!message) return;

  input.value = "";
  addChatMessage("user", message);
  chatHistory.push({ role: "user", content: message });

  const thinking = addChatMessage("assistant", "Thinking…", true);
  const submitBtn = e.target.querySelector("button[type=submit]");
  submitBtn.disabled = true;

  try {
    const { reply } = await api("/api/chat", {
      method: "POST",
      body: JSON.stringify({ message, history: chatHistory.slice(0, -1) }),
    });
    thinking.textContent = reply;
    thinking.classList.remove("loading");
    chatHistory.push({ role: "assistant", content: reply });
  } catch (err) {
    thinking.textContent = `Error: ${err.message}`;
    thinking.classList.remove("loading");
  }
  submitBtn.disabled = false;
});

// ─── Boot ────────────────────────────────────────────────────

(async function boot() {
  // Demo mode: skip login, load report instantly
  if (location.search.includes("demo")) {
    try {
      data = await api("/api/report");
      showView("report");
      render();
      addChatMessage("assistant",
        "I've read your save profile. Ask me anything — themes, patterns, what you're optimizing for, or how your saves connect to your goals.");
      return;
    } catch {}
  }

  const session = getSession();
  if (session?.jobId) {
    try {
      const job = await api(`/api/analyze/status/${session.jobId}`);
      if (job.status === "done") {
        await loadReport();
        return;
      }
      if (job.status === "running") {
        showView("processing");
        pollJob(session.jobId);
        return;
      }
    } catch {
      localStorage.removeItem("savedna_session");
    }
  }
  showView("login");
})();
