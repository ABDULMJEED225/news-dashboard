"""Render data/news.json into a self-contained dashboard/index.html.

No server needed — the page embeds its data inline so it works when opened
directly from disk (file://) as well as when served.
"""
import json
from datetime import datetime, timezone

from common import NEWS_JSON, ROOT, load_json

DASHBOARD_DIR = ROOT / "dashboard"
OUTPUT_HTML = DASHBOARD_DIR / "index.html"
# GitHub Pages only serves from the repo root or /docs — mirror the same
# rendered page there so the public URL always matches the local copy.
DOCS_DIR = ROOT / "docs"
DOCS_HTML = DOCS_DIR / "index.html"

TEMPLATE = """<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>داشبورد أخبار الألعاب والتقنية</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Tajawal:wght@400;500;700;900&family=IBM+Plex+Mono:wght@500&display=swap" rel="stylesheet">
<style>
:root {
  --navy-900: #0a1a30;
  --navy-800: #0f2848;
  --navy-700: #16365e;
  --navy-500: #2a5694;
  --navy-300: #7fa8d9;
  --bg: #ffffff;
  --bg-secondary: #f4f7fb;
  --card-bg: #ffffff;
  --border: #dde4ee;
  --text-primary: #101826;
  --text-secondary: #55637a;
  --accent: var(--navy-800);
  --accent-soft: #e7edf7;
  --new-badge: #d64545;
  --cat-gaming: #1f7a5c;
  --cat-tech: #2a5694;
  --cat-update: #b8720e;
  --cat-review: #7d3fae;
  --radius: 14px;
  --shadow: 0 1px 2px rgba(10,26,48,0.06), 0 8px 24px rgba(10,26,48,0.05);
}
@media (prefers-color-scheme: dark) {
  :root {
    --bg: #0a1526;
    --bg-secondary: #0d1c33;
    --card-bg: #101f38;
    --border: #1e3355;
    --text-primary: #f2f5fa;
    --text-secondary: #a9b8cf;
    --accent: #6fa0e6;
    --accent-soft: #16365e;
    --new-badge: #ff6b6b;
    --cat-gaming: #4fd8a8;
    --cat-tech: #7fb2f5;
    --cat-update: #f0b64c;
    --cat-review: #cfa0f2;
  }
}
:root[data-theme="dark"] {
  --bg: #0a1526; --bg-secondary: #0d1c33; --card-bg: #101f38; --border: #1e3355;
  --text-primary: #f2f5fa; --text-secondary: #a9b8cf; --accent: #6fa0e6; --accent-soft: #16365e;
  --new-badge: #ff6b6b; --cat-gaming: #4fd8a8; --cat-tech: #7fb2f5; --cat-update: #f0b64c; --cat-review: #cfa0f2;
}
:root[data-theme="light"] {
  --bg: #ffffff; --bg-secondary: #f4f7fb; --card-bg: #ffffff; --border: #dde4ee;
  --text-primary: #101826; --text-secondary: #55637a; --accent: var(--navy-800); --accent-soft: #e7edf7;
  --new-badge: #d64545; --cat-gaming: #1f7a5c; --cat-tech: #2a5694; --cat-update: #b8720e; --cat-review: #7d3fae;
}
* { box-sizing: border-box; }
body {
  margin: 0; background: var(--bg); color: var(--text-primary);
  font-family: 'Tajawal', sans-serif; -webkit-font-smoothing: antialiased;
}
.wrap { max-width: 980px; margin: 0 auto; padding: 24px 20px 80px; }
header.top {
  display: flex; justify-content: space-between; align-items: flex-start;
  gap: 16px; margin-bottom: 20px; flex-wrap: wrap;
}
h1 { font-size: 22px; font-weight: 900; margin: 0 0 4px; }
.subtitle { color: var(--text-secondary); font-size: 13px; }
.stats { display: flex; gap: 10px; flex-wrap: wrap; }
.stat {
  background: var(--bg-secondary); border: 1px solid var(--border); border-radius: 10px;
  padding: 8px 14px; text-align: center; min-width: 80px;
}
.stat .n { font-family: 'IBM Plex Mono', monospace; font-size: 18px; font-weight: 500; display: block; }
.stat .l { font-size: 11px; color: var(--text-secondary); }
.controls {
  position: sticky; top: 0; background: var(--bg); padding: 10px 0 14px; z-index: 5;
  border-bottom: 1px solid var(--border); margin-bottom: 16px;
}
#search {
  width: 100%; padding: 11px 14px; border-radius: 10px; border: 1px solid var(--border);
  background: var(--bg-secondary); color: var(--text-primary); font-family: inherit; font-size: 14px;
  margin-bottom: 10px;
}
#search:focus { outline: 2px solid var(--accent); outline-offset: 1px; }
.chip-row { display: flex; gap: 7px; flex-wrap: wrap; }
.chip {
  border: 1px solid var(--border); background: var(--bg-secondary); color: var(--text-secondary);
  border-radius: 20px; padding: 6px 14px; font-size: 13px; cursor: pointer; font-family: inherit;
  transition: all .15s;
}
.chip:hover { border-color: var(--accent); color: var(--text-primary); }
.chip.on { background: var(--accent); border-color: var(--accent); color: #fff; font-weight: 500; }
.day-label {
  font-size: 13px; font-weight: 700; color: var(--text-secondary); margin: 26px 0 10px;
  display: flex; align-items: center; gap: 8px;
}
.day-label::after { content: ""; flex: 1; height: 1px; background: var(--border); }
.card {
  background: var(--card-bg); border: 1px solid var(--border); border-radius: var(--radius);
  padding: 16px 18px; margin-bottom: 12px; box-shadow: var(--shadow);
}
.card-top { display: flex; justify-content: space-between; align-items: flex-start; gap: 10px; margin-bottom: 8px; }
.badges { display: flex; gap: 6px; flex-wrap: wrap; }
.badge {
  font-size: 11px; font-weight: 700; padding: 3px 9px; border-radius: 6px; color: #fff;
  white-space: nowrap;
}
.badge.new { background: var(--new-badge); }
.card-title { font-size: 16px; font-weight: 700; margin: 0 0 6px; line-height: 1.5; }
.card-title a { color: var(--text-primary); text-decoration: none; }
.card-title a:hover { text-decoration: underline; }
.card-summary { font-size: 14px; color: var(--text-secondary); line-height: 1.8; margin: 0 0 10px; }
.card-meta {
  display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px;
  font-size: 12px; color: var(--text-secondary);
}
.tags { display: flex; gap: 6px; flex-wrap: wrap; }
.tag { background: var(--accent-soft); color: var(--accent); padding: 2px 8px; border-radius: 6px; font-size: 11px; }
.card-actions { display: flex; gap: 8px; }
.btn-copy {
  border: 1px solid var(--border); background: var(--bg-secondary); color: var(--text-primary);
  border-radius: 8px; padding: 5px 12px; font-size: 12px; cursor: pointer; font-family: inherit;
}
.btn-copy:hover { border-color: var(--accent); }
.btn-copy.copied { background: var(--accent); color: #fff; border-color: var(--accent); }
.empty { text-align: center; color: var(--text-secondary); padding: 60px 0; font-size: 14px; }
</style>
</head>
<body>
<div class="wrap">
  <header class="top">
    <div>
      <h1>داشبورد أخبار الألعاب والتقنية</h1>
      <div class="subtitle">آخر تحديث: __LAST_UPDATED__</div>
    </div>
    <div class="stats">
      <div class="stat"><span class="n">__COUNT_NEW__</span><span class="l">جديد اليوم</span></div>
      <div class="stat"><span class="n">__COUNT_TOTAL__</span><span class="l">إجمالي الأرشيف</span></div>
    </div>
  </header>

  <div class="controls">
    <input id="search" type="text" placeholder="ابحث في العناوين والملخصات...">
    <div class="chip-row" id="cat-filters">
      <span class="chip on" data-cat="الكل">الكل</span>
      <span class="chip" data-cat="ألعاب">ألعاب</span>
      <span class="chip" data-cat="تقنية">تقنية</span>
      <span class="chip" data-cat="تحديثات">تحديثات</span>
      <span class="chip" data-cat="مراجعات">مراجعات</span>
    </div>
  </div>

  <div id="feed"></div>
  <div id="empty" class="empty" style="display:none;">ما فيه أخبار تطابق البحث الحالي</div>
</div>

<script type="application/json" id="news-data">__NEWS_JSON__</script>
<script>
const news = JSON.parse(document.getElementById('news-data').textContent);
const feed = document.getElementById('feed');
const emptyEl = document.getElementById('empty');
const searchEl = document.getElementById('search');
let activeCat = 'الكل';

const catColorVar = { 'ألعاب': '--cat-gaming', 'تقنية': '--cat-tech', 'تحديثات': '--cat-update', 'مراجعات': '--cat-review' };

function itemSortKey(item) {
  return new Date(item.published_at || item.fetched_at).getTime() || 0;
}

function dayLabel(iso) {
  const d = new Date(iso);
  const now = new Date();
  const diffDays = Math.floor((now.setHours(0,0,0,0) - new Date(d).setHours(0,0,0,0)) / 86400000);
  if (diffDays === 0) return 'اليوم';
  if (diffDays === 1) return 'أمس';
  return d.toLocaleDateString('ar-SA', { day: 'numeric', month: 'long', year: 'numeric' });
}

function render() {
  const q = searchEl.value.trim().toLowerCase();
  const filtered = news.filter(item => {
    if (activeCat !== 'الكل' && item.category !== activeCat) return false;
    if (!q) return true;
    const hay = (item.title_ar + ' ' + item.summary_ar + ' ' + (item.tags||[]).join(' ') + ' ' + item.source).toLowerCase();
    return hay.includes(q);
  });
  filtered.sort((a, b) => itemSortKey(b) - itemSortKey(a));

  feed.innerHTML = '';
  emptyEl.style.display = filtered.length ? 'none' : 'block';

  let lastDay = null;
  for (const item of filtered) {
    const dl = dayLabel(item.published_at || item.fetched_at);
    if (dl !== lastDay) {
      const h = document.createElement('div');
      h.className = 'day-label';
      h.textContent = dl;
      feed.appendChild(h);
      lastDay = dl;
    }

    const card = document.createElement('div');
    card.className = 'card';
    const catVar = catColorVar[item.category] || '--accent';
    const publishedStr = new Date(item.published_at).toLocaleDateString('ar-SA', { day: 'numeric', month: 'short' });

    card.innerHTML = `
      <div class="card-top">
        <div class="badges">
          <span class="badge" style="background:var(${catVar})">${item.category}</span>
          ${item.is_new ? '<span class="badge new">جديد</span>' : ''}
        </div>
        <span style="font-size:12px;color:var(--text-secondary)">${item.source}</span>
      </div>
      <h3 class="card-title"><a href="${item.url}" target="_blank" rel="noopener">${item.title_ar}</a></h3>
      <p class="card-summary">${item.summary_ar}</p>
      <div class="card-meta">
        <div class="tags">${(item.tags||[]).map(t => `<span class="tag">${t}</span>`).join('')}<span>${publishedStr}</span></div>
        <div class="card-actions">
          <button class="btn-copy" data-id="${item.id}">نسخ للنشر</button>
        </div>
      </div>
    `;
    feed.appendChild(card);
  }
}

feed.addEventListener('click', (e) => {
  const btn = e.target.closest('.btn-copy');
  if (!btn) return;
  const item = news.find(n => n.id === btn.dataset.id);
  if (!item) return;
  const text = `${item.title_ar}\\n\\n${item.summary_ar}\\n\\nالمصدر: ${item.source}\\n${item.url}`;
  const markCopied = () => {
    btn.textContent = 'انتسخ ✓';
    btn.classList.add('copied');
    setTimeout(() => { btn.textContent = 'نسخ للنشر'; btn.classList.remove('copied'); }, 1500);
  };
  const fallbackCopy = () => {
    const ta = document.createElement('textarea');
    ta.value = text;
    ta.style.position = 'fixed';
    ta.style.opacity = '0';
    document.body.appendChild(ta);
    ta.select();
    try { document.execCommand('copy'); markCopied(); }
    catch (err) { alert(text); }
    document.body.removeChild(ta);
  };
  if (navigator.clipboard && navigator.clipboard.writeText) {
    navigator.clipboard.writeText(text).then(markCopied).catch(fallbackCopy);
  } else {
    fallbackCopy();
  }
});

document.getElementById('cat-filters').addEventListener('click', (e) => {
  const chip = e.target.closest('.chip');
  if (!chip) return;
  document.querySelectorAll('#cat-filters .chip').forEach(c => c.classList.remove('on'));
  chip.classList.add('on');
  activeCat = chip.dataset.cat;
  render();
});

searchEl.addEventListener('input', render);
render();
</script>
</body>
</html>
"""


def main():
    archive = load_json(NEWS_JSON, [])
    archive.sort(key=lambda x: x.get("published_at") or x.get("fetched_at", ""), reverse=True)

    now = datetime.now(timezone.utc)
    for item in archive:
        try:
            fetched = datetime.fromisoformat(item["fetched_at"])
        except Exception:
            fetched = now
        item["is_new"] = (now - fetched).total_seconds() < 24 * 3600

    count_new = sum(1 for item in archive if item["is_new"])

    html = TEMPLATE
    html = html.replace("__NEWS_JSON__", json.dumps(archive, ensure_ascii=False))
    html = html.replace("__LAST_UPDATED__", now.strftime("%Y-%m-%d %H:%M UTC"))
    html = html.replace("__COUNT_NEW__", str(count_new))
    html = html.replace("__COUNT_TOTAL__", str(len(archive)))

    DASHBOARD_DIR.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_HTML, "w", encoding="utf-8") as f:
        f.write(html)

    DOCS_DIR.mkdir(parents=True, exist_ok=True)
    with open(DOCS_HTML, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"[dashboard] wrote {OUTPUT_HTML} and {DOCS_HTML} ({len(archive)} items, {count_new} new)")


if __name__ == "__main__":
    main()
