// Flashcards for the engine's lean exports (vocabulary.json / knowledge.json). No build step, no server:
// open index.html and pick the JSON files. Decks and progress are kept in localStorage.
"use strict";

const TYPE_LABELS = {
  acronym: "Viết tắt", abbreviation: "Viết tắt", technical_term: "Thuật ngữ", collocation: "Cụm từ",
  phrasal_verb: "Cụm động từ", academic: "Học thuật", general: "Từ vựng",
  concept: "Khái niệm", definition: "Định nghĩa", key_point: "Ý chính", process: "Quy trình", example: "Ví dụ",
  advantage: "Ưu điểm", disadvantage: "Nhược điểm", relation: "Quan hệ", warning: "Lưu ý",
};
const KINDS = { vocabulary: "Từ vựng", knowledge: "Kiến thức" };

const $ = (id) => document.getElementById(id);
const state = { decks: {}, kind: null, queue: [], flipped: false, filters: {} };

// --- storage (localStorage may be unavailable or full; the app still works without it) ---

function load(key, fallback) {
  try { return JSON.parse(localStorage.getItem(key)) ?? fallback; } catch { return fallback; }
}
function save(key, value) {
  try { localStorage.setItem(key, JSON.stringify(value)); } catch { /* quota or private mode */ }
}
const knownKey = () => `lbb:known:${state.decks[state.kind].slug}:${state.kind}`;
const knownSet = () => new Set(load(knownKey(), []));

// --- DOM helper: text is always set via textContent (no HTML injection) ---

function el(tag, attrs = {}, ...children) {
  const node = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs)) {
    if (k === "class") node.className = v;
    else if (k.startsWith("on")) node.addEventListener(k.slice(2), v);
    else node.setAttribute(k, v);
  }
  for (const child of children.flat()) {
    if (child === null || child === undefined || child === false) continue;
    node.append(child instanceof Node ? child : document.createTextNode(String(child)));
  }
  return node;
}

// --- decks ---

function buildDeck(data) {
  if (data.kind === "vocabulary") {
    const cards = data.terms.map((t) => ({ key: t.term, ...t }));
    return { kind: "vocabulary", slug: data.slug, course: data.course, cards };
  }
  if (data.kind === "knowledge") {
    const cards = [];
    for (const lesson of data.lessons) {
      for (const topic of lesson.topics) {
        for (const item of topic.items) {
          const title = item.title.en || Object.values(item.title)[0];
          cards.push({ key: `${lesson.n}|${item.type}|${title}`, lesson, topic, ...item });
        }
      }
    }
    return { kind: "knowledge", slug: data.slug, course: data.course, languages: data.languages, cards };
  }
  throw new Error("File JSON không phải vocabulary.json hoặc knowledge.json của engine.");
}

function addFile(text) {
  const data = JSON.parse(text);
  const deck = buildDeck(data);
  state.decks[deck.kind] = deck;
  save(`lbb:deck:${deck.kind}`, data);
  selectKind(deck.kind);
}

async function readFiles(files) {
  for (const file of files) {
    try { addFile(await file.text()); } catch (err) { alert(`${file.name}: ${err.message}`); }
  }
}

// --- filters ---

const option = (value, label, selected) => el("option", selected ? { value, selected: "" } : { value }, label);

function select(name, label, options) {
  const current = state.filters[name];
  const node = el("select", { onchange: (e) => { state.filters[name] = e.target.value; rebuild(); } },
    options.map(([value, text]) => option(value, text, String(value) === String(current))));
  return el("label", {}, label, node);
}

function renderFilters() {
  const deck = state.decks[state.kind];
  const f = state.filters;
  const types = [...new Set(deck.cards.map((c) => c.type))];
  const typeOptions = [["all", "Tất cả"], ...types.map((t) => [t, TYPE_LABELS[t] || t])];
  const onlyNew = el("input", { type: "checkbox", onchange: (e) => { f.onlyNew = e.target.checked; rebuild(); } });
  onlyNew.checked = f.onlyNew;
  const parts = [];
  if (state.kind === "vocabulary") {
    parts.push(select("top", "Số từ", [[50, "50 từ đầu"], [100, "100 từ đầu"], [200, "200 từ đầu"], [0, "Tất cả"]]));
  } else {
    const chapters = [...new Set(deck.cards.map((c) => c.lesson.chapter))];
    parts.push(select("chapter", "Chương", [["all", "Tất cả"], ...chapters.map((c) => [c, c])]));
    const langs = deck.languages || ["en"];
    parts.push(select("lang", "Ngôn ngữ", [...langs.map((l) => [l, l.toUpperCase()]), ["both", "Song ngữ"]]));
    parts.push(select("order", "Thứ tự", [["importance", "Quan trọng trước"], ["lesson", "Theo bài"]]));
  }
  parts.push(select("type", "Loại", typeOptions), el("label", {}, onlyNew, "Chỉ thẻ chưa nhớ"));
  $("filters").replaceChildren(...parts);
}

function rebuild() {
  const deck = state.decks[state.kind];
  const f = state.filters;
  const known = knownSet();
  let cards = deck.cards;
  if (state.kind === "vocabulary" && Number(f.top) > 0) cards = cards.slice(0, Number(f.top));
  if (state.kind === "knowledge" && f.chapter !== "all") cards = cards.filter((c) => c.lesson.chapter === f.chapter);
  if (f.type !== "all") cards = cards.filter((c) => c.type === f.type);
  if (state.kind === "knowledge" && f.order !== "lesson") {
    cards = [...cards].sort((a, b) => (b.importance ?? 0) - (a.importance ?? 0)); // stable: lesson order within ties
  }
  state.pool = cards;
  state.queue = f.onlyNew ? cards.filter((c) => !known.has(c.key)) : [...cards];
  renderFilters();
  show();
}

function selectKind(kind) {
  state.kind = kind;
  save("lbb:kind", kind);
  const deck = state.decks[kind];
  state.filters = load(`lbb:filters:${kind}`, null) || {
    top: 100, chapter: "all", type: "all", onlyNew: true, lang: deck.languages?.includes("vi") ? "vi" : "both",
    order: "importance",
  };
  $("empty").hidden = true;
  $("study").hidden = false;
  $("tabs").replaceChildren(...Object.keys(state.decks).map((k) => el("button",
    { class: `tab${k === kind ? " active" : ""}`, onclick: () => selectKind(k) },
    `${KINDS[k]} · ${state.decks[k].course}`)));
  rebuild();
}

// --- card rendering ---

function text(value, lang) {
  if (typeof value !== "object" || value === null || Array.isArray(value)) return value;
  if (lang === "both") return Object.values(value).join(" / ");
  return value[lang] ?? Object.values(value)[0];
}

function contentNode(value, lang) {
  const render = (v) => (Array.isArray(v) ? el("ol", {}, v.map((step) => el("li", {}, step))) : el("p", {}, v));
  if (lang === "both") return Object.entries(value).map(([l, v]) => el("div", {}, el("span", { class: "tag" }, l), render(v)));
  return render(value[lang] ?? Object.values(value)[0]);
}

function renderVocab(c) {
  const front = [
    el("span", { class: "tag" }, TYPE_LABELS[c.type] || c.type), c.pos && el("span", { class: "tag" }, c.pos),
    c.cefr && el("span", { class: "tag" }, c.cefr),
    el("p", { class: "term" }, c.term), c.expansion && el("p", { class: "muted" }, c.expansion),
  ];
  const back = [
    el("p", { class: "big" }, c.vi),
    el("p", {}, c.en), c.definition_vi && el("p", {}, c.definition_vi),
    c.example && el("div", { class: "example" }, el("p", {}, `“${c.example.text}” — bài ${c.example.lesson}`),
      c.example.vi && el("p", {}, c.example.vi)),
    c.note && el("p", {}, el("strong", {}, "Ghi chú: "), c.note),
    el("p", { class: "muted" }, `#${c.rank} · quan trọng ${c.importance}/100 · ${c.frequency} lần trong ${c.lessons} bài`),
  ];
  return [front, back];
}

function renderKnowledge(c) {
  const lang = state.filters.lang;
  const where = `Bài ${c.lesson.n}: ${c.lesson.title} · ${text(c.topic.title, lang)}`
    + (c.subtopic ? ` › ${text(c.subtopic, lang)}` : "");
  const front = [ // active recall: ask the question when knowledge_enrich made one
    el("span", { class: "tag" }, TYPE_LABELS[c.type] || c.type),
    c.importance !== undefined && el("span", { class: "tag" }, `quan trọng ${c.importance}`),
    el("p", { class: "big" }, text(c.question || c.title, lang)), el("p", { class: "muted" }, where),
  ];
  const back = [el("p", { class: "big" }, text(c.title, lang)), contentNode(c.content, lang),
    c.relation && el("p", { class: "muted" }, `${c.relation.from} → ${c.relation.type} → ${c.relation.to}`)];
  return [front, back];
}

function show() {
  const known = knownSet();
  const total = state.pool.length;
  const knownCount = state.pool.filter((c) => known.has(c.key)).length;
  $("progress").textContent = `Còn ${state.queue.length} thẻ · đã nhớ ${knownCount}/${total}`;
  save(`lbb:filters:${state.kind}`, state.filters);
  state.flipped = false;
  $("back").hidden = true;
  const card = state.queue[0];
  if (!card) {
    $("front").replaceChildren(el("p", { class: "done" }, total ? "Đã học hết các thẻ trong bộ lọc này 🎉" : "Không có thẻ nào."));
    $("back").replaceChildren();
    return;
  }
  const [front, back] = state.kind === "vocabulary" ? renderVocab(card) : renderKnowledge(card);
  $("front").replaceChildren(...front.flat().filter(Boolean)); // bilingual content yields a list of nodes
  $("back").replaceChildren(...back.flat().filter(Boolean));
}

// --- actions ---

function flip() {
  if (!state.queue.length) return;
  state.flipped = !state.flipped;
  $("back").hidden = !state.flipped;
}

function markKnown() {
  const card = state.queue.shift();
  if (!card) return;
  const known = knownSet();
  known.add(card.key);
  save(knownKey(), [...known]);
  show();
}

function again() {
  const card = state.queue.shift();
  if (!card) return;
  state.queue.splice(Math.min(5, state.queue.length), 0, card); // see it again a few cards later
  show();
}

function shuffle() {
  for (let i = state.queue.length - 1; i > 0; i -= 1) {
    const j = Math.floor(Math.random() * (i + 1));
    [state.queue[i], state.queue[j]] = [state.queue[j], state.queue[i]];
  }
  show();
}

function reset() {
  if (!confirm("Xóa tiến độ 'đã nhớ' của bộ thẻ này?")) return;
  save(knownKey(), []);
  rebuild();
}

// --- wiring ---

$("file").addEventListener("change", (e) => readFiles(e.target.files));
$("card").addEventListener("click", flip);
$("flip").addEventListener("click", flip);
$("known").addEventListener("click", markKnown);
$("again").addEventListener("click", again);
$("shuffle").addEventListener("click", shuffle);
$("reset").addEventListener("click", reset);

document.addEventListener("keydown", (e) => {
  if (state.kind === null || e.target.tagName === "SELECT" || e.target.tagName === "INPUT") return;
  if (e.key === " ") { e.preventDefault(); flip(); }
  else if (e.key === "ArrowRight" || e.key === "k") markKnown();
  else if (e.key === "ArrowLeft" || e.key === "j") again();
});

for (const target of [document.body]) {
  target.addEventListener("dragover", (e) => { e.preventDefault(); $("empty").classList.add("drag"); });
  target.addEventListener("dragleave", () => $("empty").classList.remove("drag"));
  target.addEventListener("drop", (e) => { e.preventDefault(); $("empty").classList.remove("drag"); readFiles(e.dataTransfer.files); });
}

// Restore decks loaded in a previous visit.
for (const kind of Object.keys(KINDS)) {
  const data = load(`lbb:deck:${kind}`, null);
  if (data) { try { state.decks[kind] = buildDeck(data); } catch { /* ignore stale data */ } }
}
const last = load("lbb:kind", null);
const first = state.decks[last] ? last : Object.keys(state.decks)[0];
if (first) selectKind(first);
