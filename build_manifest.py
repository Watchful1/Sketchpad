import os
import re
from collections import defaultdict

# ── Config ────────────────────────────────────────────────────────────────────

BASE    = r"\\MYCLOUDPR4100\Public\asstr"
FOLDERS = ["mirror", "mirror2", "torrent", "wayback", "xyz_1", "xyz_2", "xyz_3", "ftp"]
OUTPUT  = os.path.join(BASE, "merge_manifest.txt")

# Source priority: first entry wins when the same canonical path exists in multiple folders.
# ftp   = raw filesystem copy, original author formatting — always preferred for .txt
# torrent = website crawl, reformatted .txt files but most complete coverage
# xyz_*  = other website crawls
# mirror/mirror2 = HTTrack mirrors
# wayback = Wayback Machine archive, HTML is genuinely different
PRIORITY = ["ftp", "torrent", "xyz_1", "xyz_2", "xyz_3", "mirror", "mirror2", "wayback"]
PRIORITY_RANK = {folder: i for i, folder in enumerate(PRIORITY)}

# ── Path normalisation (mirrors explore_merge.py exactly) ────────────────────

STRIP_PREFIX = {
    "wayback": "files",
    "mirror":  "mirror",
    "mirror2": "mirror2",
    "xyz_2":   "files",
    "xyz_3":   "files",
}
STRIP_FILES_SECOND = {"mirror", "mirror2"}
KNOWN_EXTENSIONS = {
    'html', 'htm', 'txt', 'doc', 'docx', 'jpg', 'jpeg', 'gif', 'png',
    'zip', 'pdf', 'rtf', 'mp3', 'ogg', 'css', 'js', 'xml', 'log',
    'lst', 'ftp', 'whtt',
}


def looks_like_domain(component):
    if '.' not in component or ' ' in component:
        return False
    if not re.match(r'^[a-zA-Z0-9.\-]+$', component):
        return False
    return component.rsplit('.', 1)[-1].lower() not in KNOWN_EXTENSIONS


def normalize(folder, path):
    norm = path.replace('\\', '/')
    prefix = STRIP_PREFIX.get(folder)
    if prefix and norm.startswith(prefix + '/'):
        norm = norm[len(prefix) + 1:]
    parts = norm.split('/')
    while parts and looks_like_domain(parts[0]):
        parts = parts[1:]
    norm = '/'.join(parts)
    if folder in STRIP_FILES_SECOND and norm.startswith('files/'):
        norm = norm[6:]
    if folder == 'wayback' and norm.startswith('authors/'):
        norm = 'Authors/' + norm[8:]
    return norm


def is_junk(path):
    parts = path.split('/')
    if not parts or not parts[0]:
        return True
    top, filename = parts[0], parts[-1]
    if top == 'hts-cache':
        return True
    if filename in {'hts-log.txt', 'hts-err.txt', 'backblue.gif', 'fade.gif'}:
        return True
    if filename.endswith('.whtt'):
        return True
    if re.match(r'^\d{14}', top):
        return True
    if any('=' in p or '&' in p for p in parts):
        return True
    if not all(ord(c) < 128 for c in path):
        return True
    return False


# ── Helpers ───────────────────────────────────────────────────────────────────

def load_hashes(folder):
    path = os.path.join(BASE, f"{folder}.txt")
    if not os.path.exists(path):
        return []
    entries = []
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.split('\t')
            if len(parts) == 2:
                entries.append((parts[0], parts[1]))
    return entries


def needs_strip(folder, canonical):
    """Torrent .txt files were served by the ASSTR website with an HTML wrapper
    and dynamic line-wrapping. The copy script must strip the header and unescape
    HTML entities before writing these files."""
    return folder == 'torrent' and canonical.endswith('.txt')


# ── Main ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":

    # 1. Load
    print("Loading hash files...")
    all_files = {}
    for folder in FOLDERS:
        raw = load_hashes(folder)
        if not raw:
            print(f"  {folder}: [missing]")
            continue
        kept = []
        for orig_path, h in raw:
            canonical = normalize(folder, orig_path)
            if canonical and not is_junk(canonical):
                kept.append((canonical, orig_path, h))
        all_files[folder] = kept
        print(f"  {folder}: {len(raw):,} raw  →  {len(kept):,} kept")

    # 2. Build unified index: canonical → list of (folder, orig_path, hash)
    print("\nBuilding unified index...")
    unified = defaultdict(list)
    for folder, files in all_files.items():
        for canonical, orig_path, h in files:
            unified[canonical].append((folder, orig_path, h))
    print(f"  {len(unified):,} distinct canonical paths")

    # 3. Detect file/directory name collisions.
    #    If canonical path "foo/bar" exists AND any path "foo/bar/..." also exists,
    #    then on a real filesystem "bar" can't be both a file and a directory.
    #    Drop the bare-file entry — the directory (and its contents) takes precedence.
    print("Detecting file/directory name collisions...")
    implied_dirs = set()
    for canonical in unified:
        parts = canonical.split('/')
        for depth in range(1, len(parts)):
            implied_dirs.add('/'.join(parts[:depth]))

    collision_paths = {c for c in unified if c in implied_dirs}
    if collision_paths:
        print(f"  {len(collision_paths):,} bare-file paths shadow a same-name directory — skipping them")
        for c in sorted(collision_paths)[:10]:
            print(f"    {c}")
        if len(collision_paths) > 10:
            print(f"    ... and {len(collision_paths) - 10} more")
    else:
        print("  No collisions found")

    # 4. Pick winner for each canonical path and write manifest
    print(f"\nWriting manifest to:\n  {OUTPUT}\n")

    stats = defaultdict(int)

    with open(OUTPUT, 'w', encoding='utf-8', newline='\n') as out:
        for canonical in sorted(unified):
            if canonical in collision_paths:
                stats['collision_skipped'] += 1
                continue

            sources = unified[canonical]

            # Highest-priority folder that has this file
            winner = min(sources, key=lambda x: PRIORITY_RANK.get(x[0], 999))
            folder, orig_path, h = winner
            source_path = os.path.join(BASE, folder, orig_path)

            stats['total'] += 1
            stats[f'from_{folder}'] += 1

            if needs_strip(folder, canonical):
                stats['needs_strip'] += 1
                out.write(f"{canonical}\t{source_path}\tstrip_asstr_header\n")
            else:
                out.write(f"{canonical}\t{source_path}\n")

    # 5. Summary
    print(f"  Total entries:              {stats['total']:>10,}")
    print(f"  Skipped (dir collisions):   {stats['collision_skipped']:>10,}")
    print()
    print("  Source breakdown:")
    for folder in PRIORITY:
        key = f'from_{folder}'
        if stats[key]:
            print(f"    {folder:<10} {stats[key]:>10,}")
    print()
    print(f"  Entries needing ASSTR header strip: {stats['needs_strip']:>8,}")
    print("\nDone.")
