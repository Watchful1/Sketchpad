"""
Generate a self-contained dark-mode HTML bookmark browser.
og:image URLs are pre-fetched in Python (with a local cache) and baked into the HTML,
so the browser just loads plain <img> tags — no API calls, no CORS, no rate limits.
"""
import json
import os
import sys
import urllib.request
import urllib.error
import html.parser
import concurrent.futures
import threading

INPUT     = r"C:\Users\greg\Downloads\baking_bookmarks_organized.txt"
OUTPUT    = r"C:\Users\greg\Downloads\bookmarks.html"
OG_CACHE  = r"C:\Users\greg\Downloads\og_cache.json"

WORKERS   = 16          # parallel fetches
TIMEOUT   = 10          # seconds per request
REFETCH_MISSES = True   # re-try previously-failed URLs once

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)
REDDIT_UA = "bookmarks-browser/1.0 (personal offline tool)"

# ── Parse bookmarks ───────────────────────────────────────────────────────────
bookmarks = []
with open(INPUT, encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if not line:
            continue
        parts = line.split(" | ")
        if len(parts) >= 3:
            folder = parts[0]
            url    = parts[-1]
            title  = " | ".join(parts[1:-1])
            bookmarks.append({"path": folder, "title": title, "url": url})

print(f"Loaded {len(bookmarks)} bookmarks.")

# ── Load og:image cache ───────────────────────────────────────────────────────
if os.path.exists(OG_CACHE):
    with open(OG_CACHE, encoding="utf-8") as f:
        og_cache = json.load(f)
    print(f"Loaded {len(og_cache)} cached og:image entries.")
else:
    og_cache = {}

# ── og:image extraction ───────────────────────────────────────────────────────
import urllib.parse

REDDIT_HOSTS = {"reddit.com", "www.reddit.com", "old.reddit.com", "new.reddit.com"}

def is_reddit(url):
    try:
        return urllib.parse.urlparse(url).netloc in REDDIT_HOSTS
    except Exception:
        return False

def fetch_reddit_image(url):
    """Use Reddit's public JSON API to get the post preview image."""
    try:
        parsed = urllib.parse.urlparse(url)
        # Normalise host to www.reddit.com and ensure .json suffix
        api_url = parsed._replace(
            netloc="www.reddit.com",
            path=parsed.path.rstrip("/") + ".json",
            query="raw_json=1",
            fragment=""
        ).geturl()
        req = urllib.request.Request(api_url, headers={"User-Agent": REDDIT_UA})
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            data = json.loads(resp.read())
        # data is a list; first element is the post listing
        post = data[0]["data"]["children"][0]["data"]
        # Best quality: preview images (HTML-entity encoded, needs unescape)
        preview = post.get("preview", {})
        images = preview.get("images", [])
        if images:
            src = images[0].get("source", {}).get("url", "")
            if src:
                return src.replace("&amp;", "&")
        # Fallback: thumbnail (lower res but almost always present)
        thumb = post.get("thumbnail", "")
        if thumb and thumb.startswith("http"):
            return thumb
    except Exception:
        pass
    return None

class MetaParser(html.parser.HTMLParser):
    """Extracts og:image / twitter:image from the first chunk of an HTML page."""
    def __init__(self):
        super().__init__()
        self.og_image = None

    def handle_starttag(self, tag, attrs):
        if self.og_image:
            return
        if tag == "meta":
            d = {k.lower(): v for k, v in attrs}
            prop = d.get("property", "") or d.get("name", "")
            if prop.lower() in ("og:image", "og:image:secure_url", "twitter:image"):
                self.og_image = d.get("content") or d.get("value")

def fetch_og_image(url):
    """Return an absolute image URL for the page, or None on failure."""
    if is_reddit(url):
        return fetch_reddit_image(url)
    try:
        req = urllib.request.Request(url, headers={"User-Agent": UA})
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            final_url = resp.geturl()   # after any redirects
            raw = resp.read(65536)      # 64 KB — enough to clear <head>
        try:
            text = raw.decode("utf-8", errors="replace")
        except Exception:
            text = raw.decode("latin-1", errors="replace")
        parser = MetaParser()
        parser.feed(text)
        img = parser.og_image
        if not img:
            return None
        # Resolve relative URLs against the final (post-redirect) URL
        if img.startswith("//"):
            img = "https:" + img
        elif not img.startswith("http"):
            img = urllib.parse.urljoin(final_url, img)
        return img
    except Exception:
        return None

# ── Fetch missing og:images in parallel ──────────────────────────────────────
all_urls = [bk["url"] for bk in bookmarks]
urls_to_fetch = [u for u in all_urls if u not in og_cache]

# Also re-try previous misses (empty-string cache entries)
if REFETCH_MISSES:
    retry = [u for u in all_urls if og_cache.get(u) == ""]
    urls_to_fetch = list(dict.fromkeys(urls_to_fetch + retry))  # dedupe, preserve order
    if retry:
        print(f"Will re-try {len(retry)} previously-failed URLs.")

print(f"Need to fetch og:image for {len(urls_to_fetch)} URLs "
      f"({len(all_urls) - len(urls_to_fetch)} already cached).")

if urls_to_fetch:
    lock    = threading.Lock()
    done    = [0]
    total   = len(urls_to_fetch)

    def fetch_and_cache(url):
        img = fetch_og_image(url)
        with lock:
            og_cache[url] = img or ""   # empty string = confirmed miss
            done[0] += 1
            pct = done[0] * 100 // total
            bar = "#" * (pct // 5) + "-" * (20 - pct // 5)
            print(f"\r  [{bar}] {done[0]}/{total} ({pct}%)", end="", flush=True)
        return url, img

    with concurrent.futures.ThreadPoolExecutor(max_workers=WORKERS) as ex:
        list(ex.map(fetch_and_cache, urls_to_fetch))

    print()  # newline after progress bar

    # Save updated cache
    with open(OG_CACHE, "w", encoding="utf-8") as f:
        json.dump(og_cache, f, ensure_ascii=False, indent=2)
    print(f"Cache saved to {OG_CACHE}")

# ── Attach og:image to each bookmark ─────────────────────────────────────────
hits = 0
for bk in bookmarks:
    img = og_cache.get(bk["url"], "")
    bk["img"] = img
    if img:
        hits += 1

print(f"og:image found for {hits}/{len(bookmarks)} bookmarks "
      f"({hits*100//len(bookmarks) if bookmarks else 0}%).")

data_js = json.dumps(bookmarks, ensure_ascii=False, indent=None)

# ── HTML template ─────────────────────────────────────────────────────────────
HTML = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Food &amp; Baking Bookmarks</title>
<style>
*,*::before,*::after{{box-sizing:border-box;margin:0;padding:0}}
:root{{
  --bg:#18181b;
  --surface:#27272a;
  --surface2:#3f3f46;
  --border:#3f3f46;
  --text:#e4e4e7;
  --text-muted:#a1a1aa;
  --accent:#f97316;
  --accent-dim:#7c2d12;
  --link:#fb923c;
  --link-hover:#fdba74;
  --badge-bg:#3f3f46;
  --badge-text:#d4d4d8;
  --active-bg:#431407;
  --active-border:#f97316;
  --header-h:54px;
  --sidebar-w:240px;
  --thumb-w:140px;
  --thumb-h:82px;
}}
html,body{{height:100%;overflow:hidden;background:var(--bg);color:var(--text);
  font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;font-size:14px}}

/* ── Header ── */
#header{{
  position:fixed;top:0;left:0;right:0;height:var(--header-h);
  background:var(--surface);border-bottom:1px solid var(--border);
  display:flex;align-items:center;gap:12px;padding:0 16px;z-index:10;
}}
#header h1{{font-size:15px;font-weight:600;white-space:nowrap;color:var(--text)}}
#header h1 span{{color:var(--accent)}}
#search{{
  flex:1;max-width:360px;margin-left:auto;
  background:var(--surface2);border:1px solid var(--border);
  border-radius:8px;padding:7px 12px;color:var(--text);font-size:13px;outline:none;
}}
#search::placeholder{{color:var(--text-muted)}}
#search:focus{{border-color:var(--accent)}}

/* ── Layout ── */
#layout{{
  position:fixed;top:var(--header-h);left:0;right:0;bottom:28px;
  display:flex;
}}

/* ── Sidebar ── */
#sidebar{{
  width:var(--sidebar-w);min-width:var(--sidebar-w);
  background:var(--surface);border-right:1px solid var(--border);
  overflow-y:auto;padding:10px 0;flex-shrink:0;
}}
.tree-root{{list-style:none}}
.tree-node{{list-style:none}}
.node-row{{
  display:flex;align-items:center;gap:6px;
  padding:5px 12px 5px 0;cursor:pointer;border-radius:6px;
  border-left:2px solid transparent;
  transition:background 0.1s;user-select:none;
}}
.node-row:hover{{background:var(--surface2)}}
.node-row.active{{background:var(--active-bg);border-left-color:var(--active-border)}}
.node-indent{{display:inline-block;width:16px;flex-shrink:0}}
.toggle{{
  width:16px;height:16px;flex-shrink:0;display:flex;align-items:center;
  justify-content:center;color:var(--text-muted);font-size:10px;border-radius:3px;
}}
.node-label{{flex:1;font-size:13px;color:var(--text);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}}
.node-row.active .node-label{{color:var(--accent)}}
.badge{{
  font-size:10px;padding:1px 6px;border-radius:10px;
  background:var(--badge-bg);color:var(--badge-text);flex-shrink:0;
}}
.node-row.active .badge{{background:var(--accent-dim);color:var(--accent)}}
.node-children{{padding-left:14px}}
.node-children.collapsed{{display:none}}
.top-node>.node-row{{padding-left:12px;font-weight:600}}

/* ── Main content ── */
#main{{flex:1;overflow-y:auto;padding:12px 20px 20px;}}

.group-header{{
  font-size:11px;font-weight:600;letter-spacing:0.06em;text-transform:uppercase;
  color:var(--text-muted);padding:18px 0 8px;border-bottom:1px solid var(--border);
  margin-bottom:10px;position:sticky;top:0;background:var(--bg);z-index:1;
}}
.group-header:first-child{{padding-top:4px}}

/* ── Bookmark card ── */
.bk-card{{
  display:flex;align-items:stretch;gap:14px;
  padding:10px 8px;border-radius:8px;
  border:1px solid transparent;
  transition:background 0.12s,border-color 0.12s;
  margin-bottom:6px;
}}
.bk-card:hover{{background:var(--surface);border-color:var(--border)}}

/* Thumbnail */
.bk-thumb{{
  width:var(--thumb-w);min-width:var(--thumb-w);height:var(--thumb-h);
  border-radius:6px;overflow:hidden;flex-shrink:0;
  background:var(--surface2);
  display:flex;align-items:center;justify-content:center;
}}
.bk-thumb img.og{{
  width:100%;height:100%;object-fit:cover;display:block;
}}
.bk-thumb img.fav{{
  width:32px;height:32px;object-fit:contain;opacity:0.65;
}}

/* Text */
.bk-body{{
  flex:1;display:flex;flex-direction:column;justify-content:center;gap:5px;min-width:0;
}}
.bk-link{{
  color:var(--link);text-decoration:none;font-size:13px;font-weight:500;
  line-height:1.45;
  display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden;
}}
.bk-link:hover{{color:var(--link-hover);text-decoration:underline}}
.bk-meta{{font-size:11px;color:var(--text-muted)}}

/* ── Status bar ── */
#status{{
  position:fixed;bottom:0;left:var(--sidebar-w);right:0;
  height:28px;background:var(--surface);border-top:1px solid var(--border);
  display:flex;align-items:center;padding:0 16px;gap:16px;
  font-size:11px;color:var(--text-muted);
}}
#status-bk::before{{content:'📑 '}}
#status-folders::before{{content:'📁 '}}

/* ── Empty state ── */
#empty{{
  display:none;flex-direction:column;align-items:center;justify-content:center;
  height:60%;color:var(--text-muted);gap:8px;font-size:14px;
}}
#empty.show{{display:flex}}

/* ── Scrollbar ── */
::-webkit-scrollbar{{width:6px}}
::-webkit-scrollbar-track{{background:transparent}}
::-webkit-scrollbar-thumb{{background:var(--surface2);border-radius:3px}}
</style>
</head>
<body>

<div id="header">
  <h1>🔖 <span>Food &amp; Baking</span> Bookmarks</h1>
  <input id="search" type="search" placeholder="🔍  Search titles…" autocomplete="off" spellcheck="false">
</div>

<div id="layout">
  <nav id="sidebar"><ul class="tree-root" id="tree"></ul></nav>
  <main id="main">
    <div id="empty">No bookmarks match your search.</div>
  </main>
</div>

<div id="status">
  <span id="status-bk"></span>
  <span id="status-folders"></span>
</div>

<script>
const BOOKMARKS = {data_js};

function escHtml(s) {{
  if (!s) return '';
  return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}}
function domain(url) {{
  try {{ return new URL(url).hostname.replace(/^www\\./, ''); }} catch {{ return ''; }}
}}
function faviconSrc(url) {{
  const d = domain(url);
  return d ? `https://www.google.com/s2/favicons?domain=${{encodeURIComponent(d)}}&sz=64` : '';
}}

// ── Folder tree ───────────────────────────────────────────────────────────────
function buildTree(bks) {{
  const root = {{}};
  for (const bk of bks) {{
    const parts = bk.path.split(' > ');
    let node = root;
    for (const p of parts) {{ if (!node[p]) node[p] = {{}}; node = node[p]; }}
  }}
  return root;
}}

let selectedPath = null;
let searchQuery  = '';

function filterBookmarks() {{
  return BOOKMARKS.filter(bk => {{
    const pm = selectedPath === null || bk.path === selectedPath || bk.path.startsWith(selectedPath + ' > ');
    const sm = searchQuery === '' || bk.title.toLowerCase().includes(searchQuery);
    return pm && sm;
  }});
}}
function countUnder(path) {{
  return BOOKMARKS.filter(bk => {{
    const pm = bk.path === path || bk.path.startsWith(path + ' > ');
    const sm = searchQuery === '' || bk.title.toLowerCase().includes(searchQuery);
    return pm && sm;
  }}).length;
}}

// ── Render list ───────────────────────────────────────────────────────────────
function renderList() {{
  const main  = document.getElementById('main');
  const empty = document.getElementById('empty');
  main.querySelectorAll('.group-header,.bk-card').forEach(el => el.remove());

  const filtered = filterBookmarks();
  empty.classList.toggle('show', filtered.length === 0);

  const groups = {{}};
  for (const bk of filtered) {{
    if (!groups[bk.path]) groups[bk.path] = [];
    groups[bk.path].push(bk);
  }}
  const sortedPaths = Object.keys(groups).sort();

  const frag = document.createDocumentFragment();

  for (const path of sortedPaths) {{
    const hdr = document.createElement('div');
    hdr.className = 'group-header';
    hdr.textContent = path;
    frag.appendChild(hdr);

    for (const bk of groups[path]) {{
      const card = document.createElement('div');
      card.className = 'bk-card';

      // Thumbnail
      const thumb = document.createElement('div');
      thumb.className = 'bk-thumb';
      if (bk.img) {{
        const img = document.createElement('img');
        img.className = 'og';
        img.loading = 'lazy';
        img.alt = '';
        img.src = bk.img;
        img.onerror = function() {{
          const fav = faviconSrc(bk.url);
          if (fav) {{ this.className='fav'; this.src=fav; this.onerror=null; }}
          else this.remove();
        }};
        thumb.appendChild(img);
      }} else {{
        const fav = faviconSrc(bk.url);
        if (fav) {{
          const img = document.createElement('img');
          img.className = 'fav';
          img.loading = 'lazy';
          img.alt = '';
          img.src = fav;
          thumb.appendChild(img);
        }}
      }}

      // Body
      const body = document.createElement('div');
      body.className = 'bk-body';
      const d = domain(bk.url);
      body.innerHTML =
        `<a class="bk-link" href="${{escHtml(bk.url)}}" target="_blank" rel="noopener noreferrer">${{escHtml(bk.title)}}</a>` +
        (d ? `<span class="bk-meta">${{escHtml(d)}}</span>` : '');

      card.appendChild(thumb);
      card.appendChild(body);
      frag.appendChild(card);
    }}
  }}

  main.appendChild(frag);

  document.getElementById('status-bk').textContent =
    `${{filtered.length}} bookmark${{filtered.length !== 1 ? 's' : ''}}`;
  document.getElementById('status-folders').textContent =
    `${{sortedPaths.length}} folder${{sortedPaths.length !== 1 ? 's' : ''}}`;
}}

// ── Render tree ───────────────────────────────────────────────────────────────
const treeData    = buildTree(BOOKMARKS);
const expandedSet = new Set();

function renderTree() {{
  const container = document.getElementById('tree');
  container.innerHTML = '';
  renderLevel(treeData, container, [], 0);
}}

function renderLevel(node, container, pathSoFar, depth) {{
  for (const key of Object.keys(node).sort()) {{
    const fullPath   = pathSoFar.length ? pathSoFar.join(' > ') + ' > ' + key : key;
    const hasChildren = Object.keys(node[key]).length > 0;
    const isTop      = depth === 0;
    const isExpanded = isTop || expandedSet.has(fullPath);
    const isActive   = selectedPath === fullPath;
    const count      = countUnder(fullPath);

    const li  = document.createElement('li');
    li.className = 'tree-node' + (isTop ? ' top-node' : '');

    const row = document.createElement('div');
    row.className = 'node-row' + (isActive ? ' active' : '');

    for (let i = 0; i < depth; i++) {{
      const sp = document.createElement('span'); sp.className = 'node-indent'; row.appendChild(sp);
    }}
    const tog = document.createElement('span');
    tog.className = 'toggle';
    tog.textContent = hasChildren ? (isExpanded ? '▾' : '▸') : '';
    row.appendChild(tog);

    const lbl = document.createElement('span');
    lbl.className = 'node-label'; lbl.textContent = key; row.appendChild(lbl);

    const badge = document.createElement('span');
    badge.className = 'badge'; badge.textContent = count; row.appendChild(badge);

    row.addEventListener('click', () => {{
      if (hasChildren) {{
        if (expandedSet.has(fullPath)) expandedSet.delete(fullPath);
        else expandedSet.add(fullPath);
      }}
      selectedPath = (isActive && !isTop) ? null : fullPath;
      renderTree(); renderList();
      document.getElementById('main').scrollTop = 0;
    }});

    li.appendChild(row);
    if (hasChildren) {{
      const ul = document.createElement('ul');
      ul.className = 'node-children' + (isExpanded ? '' : ' collapsed');
      renderLevel(node[key], ul, [...pathSoFar, key], depth + 1);
      li.appendChild(ul);
    }}
    container.appendChild(li);
  }}
}}

// ── Search ────────────────────────────────────────────────────────────────────
document.getElementById('search').addEventListener('input', e => {{
  searchQuery = e.target.value.trim().toLowerCase();
  renderTree(); renderList();
  document.getElementById('main').scrollTop = 0;
}});

renderTree();
renderList();
</script>
</body>
</html>
"""

with open(OUTPUT, "w", encoding="utf-8") as f:
    f.write(HTML)

print(f"\nGenerated {len(HTML):,} byte HTML file.")
print(f"Output: {OUTPUT}")
