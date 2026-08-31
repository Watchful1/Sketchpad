import difflib
import hashlib
import os
import re
from collections import defaultdict, Counter

base = r"\\MYCLOUDPR4100\Public\asstr"
folders = ["mirror", "mirror2", "torrent", "wayback", "xyz_1", "xyz_2", "xyz_3", "ftp"]

# Strip this leading path prefix if present (before domain-stripping pass below).
STRIP_PREFIX = {
    "wayback": "files",
    "mirror":  "mirror",
    "mirror2": "mirror2",
    "xyz_2":   "files",
    "xyz_3":   "files",
}

# File extensions that look like domains but are actually filenames
KNOWN_EXTENSIONS = {
    'html', 'htm', 'txt', 'doc', 'docx', 'jpg', 'jpeg', 'gif', 'png',
    'zip', 'pdf', 'rtf', 'mp3', 'ogg', 'css', 'js', 'xml', 'log',
    'lst', 'ftp', 'whtt',
}

KNOWN_ROOTS = {
    "Authors", "Collections", "New_from_A.S.S", "FAQs_and_Information",
    "Utilities", "Poetry", "Site_Info", "Non_Consensual", "compressed",
}

# After the folder-prefix and domain strips, these folders still have a
# 'files/' component that needs a second-pass removal.
STRIP_FILES_SECOND = {"mirror", "mirror2"}

# Wayback Machine toolbar block (injected into every HTML page)
WAYBACK_TOOLBAR_RE = re.compile(
    rb'<!-- BEGIN WAYBACK TOOLBAR INSERT -->.*?<!-- END WAYBACK TOOLBAR INSERT -->',
    re.DOTALL,
)
# Wayback URL rewrites: /web/20190521003743/ or /web/20190521003743if_/
WAYBACK_URL_RE = re.compile(rb'/web/\d{14}[a-z_]*/(?=https?://|http%3A)')


def load_hashes(folder):
    path = os.path.join(base, f"{folder}.txt")
    if not os.path.exists(path):
        return None
    files = []
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.split('\t')
            if len(parts) != 2:
                continue
            files.append((parts[0], parts[1]))
    return files


def looks_like_domain(component):
    """True if this path component looks like a hostname (www.asstr.org) not a filename.
    Real hostnames only contain alphanumeric, hyphens, and dots — no underscores or spaces.
    This prevents New_from_A.S.S from being misidentified as a domain."""
    if '.' not in component or ' ' in component:
        return False
    if not re.match(r'^[a-zA-Z0-9.\-]+$', component):
        return False
    ext = component.rsplit('.', 1)[-1].lower()
    return ext not in KNOWN_EXTENSIONS


def normalize(folder, path):
    norm = path.replace('\\', '/')

    # Step 1: strip folder-level prefix (e.g. 'files', 'mirror', 'mirror2')
    prefix = STRIP_PREFIX.get(folder)
    if prefix and norm.startswith(prefix + '/'):
        norm = norm[len(prefix) + 1:]

    # Step 2: strip leading domain-name components (e.g. www.asstr-mirror.org)
    parts = norm.split('/')
    while parts and looks_like_domain(parts[0]):
        parts = parts[1:]
    norm = '/'.join(parts)

    # Step 3: mirror/mirror2 still have a 'files/' prefix after the domain strip
    if folder in STRIP_FILES_SECOND and norm.startswith('files/'):
        norm = norm[6:]

    # Step 4: case-fold wayback's lowercase 'authors/' -> 'Authors/'
    if folder == 'wayback' and norm.startswith('authors/'):
        norm = 'Authors/' + norm[8:]

    return norm


def is_junk(normalized_path):
    """Filter on the already-normalized path."""
    parts = normalized_path.split('/')
    if not parts or not parts[0]:
        return True
    top = parts[0]
    filename = parts[-1]
    # HTTrack crawler artifacts
    if top == 'hts-cache':
        return True
    if filename in {'hts-log.txt', 'hts-err.txt', 'backblue.gif', 'fade.gif'}:
        return True
    if filename.endswith('.whtt'):
        return True
    # Wayback junk directories
    if re.match(r'^\d{14}', top):          # timestamp dirs like 20190521003743im_
        return True
    # URL parameter artifacts
    for part in parts:
        if '=' in part or '&' in part:
            return True
    # Non-ASCII characters in any path component (Wayback garbage like )
    if not all(ord(c) < 128 for c in normalized_path):
        return True
    return False


def md5_of_file(path):
    h = hashlib.md5()
    with open(path, 'rb') as f:
        for chunk in iter(lambda: f.read(65536), b''):
            h.update(chunk)
    return h.hexdigest()


def md5_of_wayback_stripped(path):
    """Read a wayback HTML file, strip toolbar and URL rewrites, return cleaned MD5."""
    try:
        with open(path, 'rb') as f:
            content = f.read()
        content = WAYBACK_TOOLBAR_RE.sub(b'', content)
        content = WAYBACK_URL_RE.sub(b'', content)
        return hashlib.md5(content).hexdigest()
    except OSError:
        return None


def separator(title):
    print(f"\n{'='*60}")
    print(f"  {title}")
    print('='*60)


if __name__ == "__main__":

    # ── Section flags ─────────────────────────────────────────────
    # Set to False to skip sections whose findings are already settled.
    # Sections 1+2 (load/normalize) always run — everything else depends on them.
    RUN = {
        'top_level_dirs':    False,  # DONE — normalization is stable
        'unified_stats':     True,
        'ext_breakdown':     False,  # DONE — extension conflict rates understood
        'unique_per_folder': True,
        'media_stats':       False,
        'nfas_check':        False,  # DONE — 293 unique, 69 duplicated elsewhere
        'wayback_stripping': False,  # DONE — HTML conflicts are genuine, not toolbar
        'line_ending_check': False,  # DONE — 0% resolved, conflicts are real content diffs
        'txt_header_exam':   False,  # DONE — header identified, see ASSTR_HEADER_RE below
        'txt_header_verify': False,  # DONE — 45% resolved by header strip + CRLF norm
        'txt_conflict_diag':  False,  # DONE — root cause: ftp=CRLF, torrent body=LF
        'txt_deep_diag':      False,  # DONE — remaining 55% due to ASSTR dynamic reformatting
        # MERGE STRATEGY CONCLUSION for .txt files:
        #   The ASSTR website hard-wraps text at ~70 chars and HTML-entity-encodes angle
        #   brackets when serving .txt files inside <pre>. The torrent was crawled from
        #   the website; ftp is the raw original. Line-unwrapping is lossy, so:
        #     - ftp copy exists  → use ftp (original format wins)
        #     - torrent-only     → strip ASSTR header + html.unescape() the content
        'torrent_txt_count':  True,   # ACTIVE — count torrent .txt files needing header strip
    }

    # ── 1. Load ──────────────────────────────────────────────────
    separator("LOADING")
    raw_files = {}
    for folder in folders:
        files = load_hashes(folder)
        if files:
            raw_files[folder] = files
            print(f"  {folder}: {len(files):,} files")
        else:
            print(f"  {folder}: [missing]")

    if not raw_files:
        print("No hash files found.")
        raise SystemExit

    # ── 2. Normalize and filter ───────────────────────────────────
    separator("NORMALIZATION + JUNK FILTER")
    all_files = {}
    for folder, files in raw_files.items():
        kept, junk_count, empty_count = [], 0, 0
        for path, h in files:
            canonical = normalize(folder, path)
            if not canonical:
                empty_count += 1
                continue
            if is_junk(canonical):
                junk_count += 1
                continue
            kept.append((canonical, path, h))
        all_files[folder] = kept
        print(f"  {folder}: {len(files):,} raw  →  {len(kept):,} kept"
              f"  ({junk_count:,} junk, {empty_count:,} empty-path)")

    # ── 3. Top-level dirs after normalization ─────────────────────
    if RUN['top_level_dirs']:
        separator("TOP-LEVEL DIRS AFTER NORMALIZATION (top 10 per folder)")
        for folder, files in all_files.items():
            top_dirs = Counter(canonical.split('/')[0] for canonical, _, _ in files)
            print(f"\n  {folder}:")
            for d, count in top_dirs.most_common(10):
                marker = " *" if d.startswith('~') else ""
                print(f"    {d!r:35s} {count:>10,}{marker}")

    # ── 4. Build unified index (always runs — other sections depend on it) ──
    unified = defaultdict(list)
    for folder, files in all_files.items():
        for canonical, orig_path, h in files:
            unified[canonical].append((folder, orig_path, h))

    if RUN['unified_stats']:
        separator("UNIFIED INDEX STATS")
        total         = len(unified)
        in_multiple   = sum(1 for v in unified.values() if len({f for f, p, h in v}) > 1)
        exact_matches = sum(1 for v in unified.values()
                            if len({f for f, p, h in v}) > 1 and len({h for f, p, h in v}) == 1)
        md5_conflicts = sum(1 for v in unified.values() if len({h for f, p, h in v}) > 1)
        unique_one    = sum(1 for v in unified.values() if len({f for f, p, h in v}) == 1)
        print(f"\n  Total canonical paths:         {total:>10,}")
        print(f"  In 2+ folders:                 {in_multiple:>10,}")
        print(f"    exact MD5 match:             {exact_matches:>10,}")
        print(f"    MD5 conflicts:               {md5_conflicts:>10,}")
        print(f"  Unique to 1 folder:            {unique_one:>10,}")

    # ── 5. Conflict breakdown by file extension ───────────────────
    if RUN['ext_breakdown']:
        separator("CONFLICT BREAKDOWN BY FILE EXTENSION")
        ext_stats = defaultdict(lambda: {'total': 0, 'conflict': 0, 'exact': 0})
        for canonical, sources in unified.items():
            ext = canonical.rsplit('.', 1)[-1].lower() if '.' in canonical.split('/')[-1] else '(none)'
            multi = len({f for f, p, h in sources}) > 1
            if multi:
                if len({h for f, p, h in sources}) > 1:
                    ext_stats[ext]['conflict'] += 1
                else:
                    ext_stats[ext]['exact'] += 1
            ext_stats[ext]['total'] += 1
        print(f"\n  {'ext':<12} {'total':>10} {'in 2+':>10} {'exact':>10} {'conflict':>10}  conflict%")
        for ext, s in sorted(ext_stats.items(), key=lambda x: -(x[1]['conflict'])):
            if s['total'] < 5:
                continue
            multi = s['exact'] + s['conflict']
            if multi == 0:
                continue
            pct = 100 * s['conflict'] / multi if multi else 0
            print(f"  {ext:<12} {s['total']:>10,} {multi:>10,} {s['exact']:>10,} {s['conflict']:>10,}  {pct:5.1f}%")

    # ── 6. Per-folder unique counts ───────────────────────────────
    if RUN['unique_per_folder']:
        separator("FILES UNIQUE TO EACH FOLDER")
        for folder in all_files:
            only_here = sum(1 for v in unified.values() if {f for f, p, h in v} == {folder})
            print(f"  {folder}: {only_here:,} paths not found anywhere else")

    # ── 7. Media file stats ───────────────────────────────────────
    IMAGE_EXTS = {'jpg', 'jpeg', 'png', 'gif', 'bmp', 'tif', 'tiff', 'webp', 'svg', 'ico'}
    VIDEO_EXTS = {'mp4', 'avi', 'mov', 'wmv', 'flv', 'mkv', 'webm', 'mpg', 'mpeg', 'm4v', 'rm', 'rmvb'}
    AUDIO_EXTS = {'mp3', 'ogg', 'wav', 'flac', 'aac', 'm4a', 'wma', 'mid', 'midi'}

    def media_type(canonical):
        ext = canonical.rsplit('.', 1)[-1].lower() if '.' in canonical.split('/')[-1] else ''
        if ext in IMAGE_EXTS: return 'image'
        if ext in VIDEO_EXTS: return 'video'
        if ext in AUDIO_EXTS: return 'audio'
        return None

    if RUN['media_stats']:
        separator("MEDIA FILE STATS")
        print(f"\n  {'folder':<12} {'images':>10} {'video':>10} {'audio':>10}  {'total media':>12}")
        for folder, files in all_files.items():
            counts = Counter(media_type(c) for c, _, _ in files)
            images = counts.get('image', 0)
            videos = counts.get('video', 0)
            audio  = counts.get('audio', 0)
            print(f"  {folder:<12} {images:>10,} {videos:>10,} {audio:>10,}  {images+videos+audio:>12,}")
        media_unified  = {c: v for c, v in unified.items() if media_type(c) is not None}
        media_multi    = {c: v for c, v in media_unified.items() if len({f for f, p, h in v}) > 1}
        media_exact    = {c: v for c, v in media_multi.items()  if len({h for f, p, h in v}) == 1}
        media_conflict = {c: v for c, v in media_multi.items()  if len({h for f, p, h in v}) > 1}
        media_unique   = {c: v for c, v in media_unified.items() if len({f for f, p, h in v}) == 1}
        print(f"\n  Total distinct media paths:  {len(media_unified):>8,}")
        print(f"  In 2+ folders:               {len(media_multi):>8,}  (exact: {len(media_exact):,}  conflict: {len(media_conflict):,})")
        print(f"  Unique to 1 folder:          {len(media_unique):>8,}")
        for mtype in ('image', 'video', 'audio'):
            paths = {c: v for c, v in media_unified.items() if media_type(c) == mtype}
            multi  = sum(1 for v in paths.values() if len({f for f, p, h in v}) > 1)
            unique = sum(1 for v in paths.values() if len({f for f, p, h in v}) == 1)
            ext_counts = Counter(c.rsplit('.', 1)[-1].lower() for c in paths if '.' in c.split('/')[-1])
            exts_str = '  '.join(f"{e}:{n:,}" for e, n in ext_counts.most_common(6))
            print(f"    {mtype:<8} {len(paths):>8,} total  shared:{multi:,}  unique:{unique:,}  [{exts_str}]")
        print(f"\n  Media unique to each folder:")
        for folder in all_files:
            u = [c for c, v in media_unified.items() if {f for f, p, h in v} == {folder}]
            by_type = Counter(media_type(c) for c in u)
            print(f"    {folder:<12} {len(u):>6,}  (img:{by_type.get('image',0):,}  vid:{by_type.get('video',0):,}  aud:{by_type.get('audio',0):,})")

    # ── 8. New_from_A.S.S cross-folder MD5 check ─────────────────
    if RUN['nfas_check']:
        separator("New_from_A.S.S CROSS-FOLDER MD5 CHECK")
        hash_index = defaultdict(list)
        for folder, files in all_files.items():
            for canonical, orig_path, h in files:
                hash_index[h].append((folder, canonical))
        nfas_files = [(c, v) for c, v in unified.items() if c.startswith('New_from_A.S.S/')]
        print(f"\n  Total New_from_A.S.S canonical paths: {len(nfas_files):,}")
        matched_elsewhere, only_here = [], []
        for canonical, sources in nfas_files:
            other_locations = [
                (of, oc, h)
                for h in {h for f, p, h in sources}
                for of, oc in hash_index[h]
                if not oc.startswith('New_from_A.S.S/')
            ]
            (matched_elsewhere if other_locations else only_here).append(
                (canonical, sources, other_locations) if other_locations else (canonical, sources))
        print(f"  MD5 appears elsewhere: {len(matched_elsewhere):,}  |  only in NFAS: {len(only_here):,}")
        for canonical, sources, other_locations in matched_elsewhere[:5]:
            print(f"\n    {canonical}  found in: {sorted({f for f,p,h in sources})}")
            for of, oc, h in other_locations[:3]:
                print(f"      also at [{of}] {oc}")

    # ── 9. Wayback stripping ──────────────────────────────────────
    # DONE — HTML conflicts are genuine rewrites, not just toolbar injection.
    # Kept for reference; set wayback_stripping=True to re-run.
    if RUN['wayback_stripping']:
        separator("WAYBACK HEADER STRIPPING (HTML and TXT conflicts)")

        def check_wayback_conflicts(label, ext_filter, path_prefix=None, sample_limit=2000):
            conflicts = [
                (canonical, sources)
                for canonical, sources in unified.items()
                if canonical.endswith(ext_filter)
                and (path_prefix is None or canonical.startswith(path_prefix))
                and len({h for f, p, h in sources}) > 1
                and any(f == 'wayback' for f, p, h in sources)
                and any(f != 'wayback' for f, p, h in sources)
            ]
            scope = f" under {path_prefix}" if path_prefix else ""
            print(f"\n  {label}{scope}: {len(conflicts):,} conflicts (sampling {sample_limit:,})")
            resolved, still_conflict, unreadable, samples_shown = 0, 0, 0, 0
            for canonical, sources in conflicts[:sample_limit]:
                wb_entries    = [(f, p, h) for f, p, h in sources if f == 'wayback']
                other_entries = [(f, p, h) for f, p, h in sources if f != 'wayback']
                other_hashes  = {h for f, p, h in other_entries}
                for wb_f, wb_p, wb_h in wb_entries:
                    cleaned = md5_of_wayback_stripped(os.path.join(base, wb_f, wb_p))
                    if cleaned is None:
                        unreadable += 1; continue
                    if cleaned in other_hashes:
                        resolved += 1
                        if samples_shown < 3:
                            of, op, oh = next((f,p,h) for f,p,h in other_entries if h == cleaned)
                            print(f"    RESOLVED: {canonical}")
                            print(f"      wayback: {os.path.join(base, wb_f, wb_p)}")
                            print(f"      other  : {os.path.join(base, of, op)}")
                            samples_shown += 1
                    else:
                        still_conflict += 1
                        if samples_shown < 3:
                            print(f"    CONFLICT: {canonical}")
                            print(f"      wayback: {os.path.join(base, wb_f, wb_p)}")
                            for of, op, oh in other_entries[:1]:
                                print(f"      other  : {os.path.join(base, of, op)}")
                            samples_shown += 1
            checked = resolved + still_conflict
            if checked:
                print(f"    Resolved: {resolved:,}/{checked:,} ({100*resolved/checked:.1f}%)  unreadable: {unreadable:,}")

        check_wayback_conflicts("HTML", ".html", path_prefix="Authors/", sample_limit=2000)
        check_wayback_conflicts("TXT",  ".txt",  path_prefix="Authors/", sample_limit=2000)

    # ── 10. Line-ending check ─────────────────────────────────────
    # DONE — 0% resolved. Conflicts are genuine content differences, not CRLF/LF.
    if RUN['line_ending_check']:
        separator("LINE-ENDING CHECK FOR TXT CONFLICTS")

        def md5_strip_cr(path):
            try:
                with open(path, 'rb') as f:
                    content = f.read()
                return hashlib.md5(content.replace(b'\r', b'')).hexdigest()
            except OSError:
                return None

        txt_conflicts_tf = [
            (canonical, sources) for canonical, sources in unified.items()
            if canonical.endswith('.txt') and canonical.startswith('Authors/')
            and len({h for f, p, h in sources}) > 1
            and any(f == 'torrent' for f, p, h in sources)
            and any(f == 'ftp'     for f, p, h in sources)
        ]
        print(f"  torrent vs ftp Authors/ .txt conflicts: {len(txt_conflicts_tf):,}")
        crlf_resolved, still_differ, unreadable_cr, cr_samples = 0, 0, 0, 0
        for canonical, sources in txt_conflicts_tf[:2000]:
            for t_f, t_p, t_h in [(f,p,h) for f,p,h in sources if f == 'torrent']:
                for fp_f, fp_p, fp_h in [(f,p,h) for f,p,h in sources if f == 'ftp']:
                    if t_h == fp_h: continue
                    t_full, fp_full = os.path.join(base,t_f,t_p), os.path.join(base,fp_f,fp_p)
                    t_norm, fp_norm = md5_strip_cr(t_full), md5_strip_cr(fp_full)
                    if t_norm is None or fp_norm is None:
                        unreadable_cr += 1; continue
                    if t_norm == fp_norm:
                        crlf_resolved += 1
                        if cr_samples < 3:
                            print(f"  RESOLVED: {canonical}\n    torrent: {t_full}\n    ftp    : {fp_full}")
                            cr_samples += 1
                    else:
                        still_differ += 1
                        if cr_samples < 3:
                            print(f"  STILL DIFFERS: {canonical}\n    torrent: {t_full}\n    ftp    : {fp_full}")
                            cr_samples += 1
        checked_cr = crlf_resolved + still_differ
        if checked_cr:
            print(f"  Resolved: {crlf_resolved:,}/{checked_cr:,} ({100*crlf_resolved/checked_cr:.1f}%)")

    # ── 11. TXT header examination ────────────────────────────────
    if RUN['txt_header_exam']:
        separator("TXT HEADER EXAMINATION")
        print("  Reading both versions of conflicting txt files to identify header pattern.\n")

        txt_conflicts_tf = [
            (canonical, sources) for canonical, sources in unified.items()
            if canonical.endswith('.txt') and canonical.startswith('Authors/')
            and len({h for f, p, h in sources}) > 1
            and any(f == 'torrent' for f, p, h in sources)
            and any(f == 'ftp'     for f, p, h in sources)
        ]

        shown = 0
        for canonical, sources in txt_conflicts_tf:
            if shown >= 3:
                break
            t_f, t_p, t_h   = next((f,p,h) for f,p,h in sources if f == 'torrent')
            fp_f, fp_p, fp_h = next((f,p,h) for f,p,h in sources if f == 'ftp')
            t_full  = os.path.join(base, t_f,  t_p)
            fp_full = os.path.join(base, fp_f, fp_p)
            try:
                t_lines  = open(t_full,  encoding='utf-8', errors='replace').readlines()
                fp_lines = open(fp_full, encoding='utf-8', errors='replace').readlines()
            except OSError:
                continue

            # Find where the files first differ
            first_diff = next(
                (i for i, (a, b) in enumerate(zip(t_lines, fp_lines)) if a != b),
                min(len(t_lines), len(fp_lines))
            )

            print(f"  ── File {shown+1}: {canonical}")
            print(f"     torrent ({len(t_lines)} lines): {t_full}")
            print(f"     ftp     ({len(fp_lines)} lines): {fp_full}")
            print(f"     First difference at line {first_diff + 1}")
            print(f"\n     [torrent] first 15 lines:")
            for i, line in enumerate(t_lines[:15]):
                print(f"       {i+1:3}: {line!r}")
            print(f"\n     [ftp] first 15 lines:")
            for i, line in enumerate(fp_lines[:15]):
                print(f"       {i+1:3}: {line!r}")
            if first_diff > 0:
                print(f"\n     Context around first diff (lines {max(1,first_diff-1)}-{first_diff+3}):")
                for i in range(max(0, first_diff-1), min(len(t_lines), first_diff+3)):
                    t_line  = t_lines[i]  if i < len(t_lines)  else '<missing>'
                    fp_line = fp_lines[i] if i < len(fp_lines) else '<missing>'
                    marker = '!!' if t_line != fp_line else '  '
                    print(f"       {marker} {i+1:3} torrent: {t_line!r}")
                    print(f"       {marker}     ftp    : {fp_line!r}")
            print()
            shown += 1

    # ── 12. TXT header stripping verification ─────────────────────
    # ASSTR website served .txt files with an HTML wrapper. The torrent was
    # crawled from the website; ftp is a raw filesystem copy without the wrapper.
    # Pattern: <!--ADULTSONLY--> ... <pre>\n  (always 10 lines, then story content)
    ASSTR_HEADER_RE = re.compile(
        rb'<!--ADULTSONLY-->.*?<pre>\r?\n?',
        re.DOTALL | re.IGNORECASE,
    )

    def strip_asstr_header(content):
        """Strip the ASSTR HTML wrapper from a .txt file served by the website."""
        if not content.lstrip().startswith(b'<!--ADULTSONLY-->'):
            return content
        stripped = ASSTR_HEADER_RE.sub(b'', content, count=1)
        return stripped

    def md5_asstr_stripped(path):
        try:
            with open(path, 'rb') as f:
                content = f.read()
            return hashlib.md5(strip_asstr_header(content)).hexdigest()
        except OSError:
            return None

    def normalize_content(b):
        """Strip BOM, normalize CRLF→LF, strip trailing whitespace. Applied to both sides."""
        if b.startswith(b'\xef\xbb\xbf'):
            b = b[3:]
        b = b.replace(b'\r\n', b'\n').replace(b'\r', b'\n')
        return b.rstrip(b'\r\n\t ')

    if RUN['txt_header_verify']:
        SAMPLE_LIMIT = 500
        separator("TXT HEADER STRIPPING VERIFICATION (torrent vs ftp, Authors/)")
        print("  Strategy: strip ASSTR header from torrent, then normalize CRLF on both sides.")

        txt_conflicts_tf = [
            (canonical, sources) for canonical, sources in unified.items()
            if canonical.endswith('.txt') and canonical.startswith('Authors/')
            and len({h for f, p, h in sources}) > 1
            and any(f == 'torrent' for f, p, h in sources)
            and any(f == 'ftp'     for f, p, h in sources)
        ]
        total_conflicts = len(txt_conflicts_tf)
        sample = txt_conflicts_tf[:SAMPLE_LIMIT]
        print(f"\n  Total torrent vs ftp Authors/ .txt conflicts: {total_conflicts:,}")
        print(f"  Sampling first {len(sample):,} for file-read verification\n")

        resolved, still_conflict, no_header, unreadable = 0, 0, 0, 0
        resolved_samples, conflict_samples = [], []
        # Raw content saved for deep diagnostics in section 14
        deep_diag_pairs = []  # (canonical, t_norm, fp_raw)

        for canonical, sources in sample:
            torrent_entries = [(f, p, h) for f, p, h in sources if f == 'torrent']
            ftp_entries     = [(f, p, h) for f, p, h in sources if f == 'ftp']

            for t_f, t_p, t_h in torrent_entries:
                t_full = os.path.join(base, t_f, t_p)
                try:
                    with open(t_full, 'rb') as fh:
                        t_raw = fh.read()
                except OSError:
                    unreadable += 1
                    continue

                if not t_raw.lstrip().startswith(b'<!--ADULTSONLY-->'):
                    no_header += 1
                    continue

                t_norm = normalize_content(ASSTR_HEADER_RE.sub(b'', t_raw, count=1))

                # Compare against each ftp version (normalized on both sides)
                matched_fp = None
                for fp_f, fp_p, fp_h in ftp_entries:
                    fp_full = os.path.join(base, fp_f, fp_p)
                    try:
                        with open(fp_full, 'rb') as fh:
                            fp_raw = fh.read()
                    except OSError:
                        continue
                    if normalize_content(fp_raw) == t_norm:
                        matched_fp = (fp_f, fp_p, fp_h)
                        break

                if matched_fp:
                    resolved += 1
                    if len(resolved_samples) < 3:
                        resolved_samples.append((canonical, t_p, matched_fp[1]))
                else:
                    still_conflict += 1
                    if len(conflict_samples) < 3:
                        fp_f, fp_p, fp_h = ftp_entries[0]
                        conflict_samples.append((canonical, t_p, fp_p))
                    # Save raw content for deep diagnostics (first ftp entry only)
                    if len(deep_diag_pairs) < 10:
                        try:
                            fp_f, fp_p, fp_h = ftp_entries[0]
                            fp_full = os.path.join(base, fp_f, fp_p)
                            with open(fp_full, 'rb') as fh:
                                fp_raw = fh.read()
                            deep_diag_pairs.append((canonical, t_norm, fp_raw))
                        except OSError:
                            pass

        checked = resolved + still_conflict
        print(f"  Has ASSTR header:                       {checked + no_header:>10,}")
        print(f"  No ASSTR header (torrent):              {no_header:>10,}")
        print(f"  Unreadable:                             {unreadable:>10,}")
        print(f"  Resolved (header strip + CRLF norm):   {resolved:>10,}")
        print(f"  Still differ after all normalization:  {still_conflict:>10,}")
        if checked:
            print(f"  Resolution rate:                        {100*resolved/checked:>9.1f}%")

        if resolved_samples:
            print(f"\n  Sample RESOLVED:")
            for canonical, t_p, fp_p in resolved_samples:
                print(f"    {canonical}")
                print(f"      torrent: {os.path.join(base, 'torrent', t_p)}")
                print(f"      ftp    : {os.path.join(base, 'ftp',     fp_p)}")

        if conflict_samples:
            print(f"\n  Sample STILL CONFLICTING:")
            for canonical, t_p, fp_p in conflict_samples:
                print(f"    {canonical}")
                print(f"      torrent: {os.path.join(base, 'torrent', t_p)}")
                print(f"      ftp    : {os.path.join(base, 'ftp',     fp_p)}")

    # ── 13. TXT still-conflicting diagnostics ─────────────────────
    if RUN['txt_conflict_diag']:
        separator("TXT STILL-CONFLICTING DIAGNOSTICS")
        print("  Reading stripped-torrent vs ftp pairs to find the byte-level difference.\n")

        # Collect up to 8 pairs that are still conflicting after header strip
        diag_pairs = []
        txt_conflicts_tf = [
            (canonical, sources) for canonical, sources in unified.items()
            if canonical.endswith('.txt') and canonical.startswith('Authors/')
            and len({h for f, p, h in sources}) > 1
            and any(f == 'torrent' for f, p, h in sources)
            and any(f == 'ftp'     for f, p, h in sources)
        ]
        for canonical, sources in txt_conflicts_tf:
            if len(diag_pairs) >= 8:
                break
            t_f, t_p, t_h   = next(((f,p,h) for f,p,h in sources if f == 'torrent'), (None,None,None))
            fp_f, fp_p, fp_h = next(((f,p,h) for f,p,h in sources if f == 'ftp'),     (None,None,None))
            if not t_p or not fp_p:
                continue
            try:
                with open(os.path.join(base, t_f, t_p), 'rb') as fh:
                    t_raw = fh.read()
                with open(os.path.join(base, fp_f, fp_p), 'rb') as fh:
                    fp_raw = fh.read()
            except OSError:
                continue
            t_stripped = ASSTR_HEADER_RE.sub(b'', t_raw, count=1) if t_raw.lstrip().startswith(b'<!--ADULTSONLY-->') else t_raw
            if hashlib.md5(t_stripped).hexdigest() != fp_h:
                diag_pairs.append((canonical, t_p, t_stripped, fp_p, fp_raw))

        def norm_crlf(b):    return b.replace(b'\r\n', b'\n').replace(b'\r', b'\n')
        def strip_bom(b):    return b[3:] if b.startswith(b'\xef\xbb\xbf') else b
        def strip_trail(b):  return b.rstrip(b'\r\n\t ')
        def norm_all(b):     return strip_trail(norm_crlf(strip_bom(b)))

        # Aggregate counts across all pairs
        totals = {'crlf': 0, 'bom': 0, 'trail': 0, 'combo': 0, 'footer': 0, 'still': 0}

        for canonical, t_p, t_body, fp_p, fp_body in diag_pairs:
            t_crlf  = norm_crlf(t_body)
            t_bom   = strip_bom(t_body)
            t_trail = strip_trail(t_body)
            t_combo = norm_all(t_body)
            fp_combo = norm_all(fp_body)

            crlf_match  = hashlib.md5(t_crlf).hexdigest()  == hashlib.md5(fp_body).hexdigest()
            bom_match   = hashlib.md5(t_bom).hexdigest()   == hashlib.md5(fp_body).hexdigest()
            trail_match = hashlib.md5(t_trail).hexdigest() == hashlib.md5(fp_body).hexdigest()
            combo_match = hashlib.md5(t_combo).hexdigest() == hashlib.md5(fp_combo).hexdigest()

            # Check for closing footer tags at the end of the torrent body
            t_tail = t_body[-200:].lower()
            has_footer = b'</pre>' in t_tail or b'</body>' in t_tail or b'</html>' in t_tail

            first_diff = next(
                (i for i, (a, b) in enumerate(zip(t_body, fp_body)) if a != b),
                min(len(t_body), len(fp_body))
            )

            if crlf_match:  totals['crlf']  += 1
            if bom_match:   totals['bom']   += 1
            if trail_match: totals['trail'] += 1
            if combo_match: totals['combo'] += 1
            if has_footer:  totals['footer'] += 1
            if not combo_match: totals['still'] += 1

            print(f"  ── {canonical}")
            print(f"     sizes: torrent_body={len(t_body):,}  ftp={len(fp_body):,}  diff={len(t_body)-len(fp_body):+,}")
            print(f"     first byte diff at offset {first_diff:,}")
            print(f"     fixes: crlf={crlf_match}  bom={bom_match}  trailing={trail_match}  all_combined={combo_match}  has_footer={has_footer}")

            # Show context around first difference
            lo = max(0, first_diff - 20)
            hi = min(len(t_body), first_diff + 40)
            print(f"     torrent bytes [{lo}:{hi}]: {t_body[lo:hi]!r}")
            fp_hi = min(len(fp_body), first_diff + 40)
            print(f"     ftp     bytes [{lo}:{fp_hi}]: {fp_body[lo:fp_hi]!r}")

            # Show last 80 bytes of each to catch footer differences
            print(f"     torrent tail: {t_body[-80:].rstrip()!r}")
            print(f"     ftp     tail: {fp_body[-80:].rstrip()!r}")
            print()

        n = len(diag_pairs)
        if n:
            print(f"  ── Summary across {n} sample pairs ──")
            print(f"  Resolved by CRLF normalisation:      {totals['crlf']:>4} / {n}")
            print(f"  Resolved by BOM strip:               {totals['bom']:>4} / {n}")
            print(f"  Resolved by trailing-whitespace trim:{totals['trail']:>4} / {n}")
            print(f"  Resolved by all three combined:      {totals['combo']:>4} / {n}")
            print(f"  Has </pre>/</body>/</html> footer:   {totals['footer']:>4} / {n}")
            print(f"  Still differs after all fixes:       {totals['still']:>4} / {n}")

    # ── 14. Deep diagnostics on still-conflicting normalized pairs ──
    if RUN['txt_deep_diag']:
        separator("TXT DEEP DIAGNOSTICS (still differ after header strip + CRLF norm)")
        print("  Trying more aggressive normalizations and showing exact diff location.\n")

        def norm_lines(b):
            """Strip per-line trailing whitespace and leading/trailing blank lines."""
            lines = b.split(b'\n')
            lines = [line.rstrip(b' \t') for line in lines]
            # Drop leading blank lines
            while lines and not lines[0].strip():
                lines.pop(0)
            # Drop trailing blank lines
            while lines and not lines[-1].strip():
                lines.pop()
            return b'\n'.join(lines)

        def norm_aggressive(b):
            """Full normalization: BOM + CRLF + per-line trailing space + blank lines."""
            if b.startswith(b'\xef\xbb\xbf'):
                b = b[3:]
            b = b.replace(b'\r\n', b'\n').replace(b'\r', b'\n')
            return norm_lines(b)

        def first_diff_after_norm(a, b):
            """Return (offset, byte_a, byte_b) of first differing byte, or None if equal."""
            for i, (x, y) in enumerate(zip(a, b)):
                if x != y:
                    return i, x, y
            if len(a) != len(b):
                return min(len(a), len(b)), None, None
            return None

        agg_totals = {'line_rstrip': 0, 'aggressive': 0, 'still': 0, 'nonascii_t': 0, 'nonascii_f': 0}

        if not deep_diag_pairs:
            print("  (No deep_diag_pairs — run txt_header_verify first)")

        agg_totals = {'line_rstrip': 0, 'aggressive': 0, 'still': 0, 'nonascii_t': 0, 'nonascii_f': 0}

        for canonical, t_norm, fp_raw in deep_diag_pairs:
            fp_norm = normalize_content(fp_raw)

            t_lines_raw = norm_lines(t_norm)
            fp_lines_raw = norm_lines(fp_norm)
            line_match = (t_lines_raw == fp_lines_raw)

            t_agg  = norm_aggressive(t_norm)
            fp_agg = norm_aggressive(fp_raw)
            agg_match = (t_agg == fp_agg)

            t_nonascii  = sum(1 for byte in t_norm  if byte > 127)
            fp_nonascii = sum(1 for byte in fp_norm if byte > 127)

            if line_match:    agg_totals['line_rstrip'] += 1
            if agg_match:     agg_totals['aggressive']  += 1
            if not agg_match: agg_totals['still']       += 1
            if t_nonascii:    agg_totals['nonascii_t']  += 1
            if fp_nonascii:   agg_totals['nonascii_f']  += 1

            # Split into decoded lines for difflib (errors='replace' so bad bytes don't crash)
            t_lines  = t_agg.decode('utf-8', errors='replace').splitlines()
            fp_lines = fp_agg.decode('utf-8', errors='replace').splitlines()

            # Count changed/added/removed lines
            matcher = difflib.SequenceMatcher(None, t_lines, fp_lines, autojunk=False)
            changed_blocks = [(tag, i1, i2, j1, j2)
                              for tag, i1, i2, j1, j2 in matcher.get_opcodes()
                              if tag != 'equal']
            changed_t_lines = sum(i2 - i1 for tag, i1, i2, j1, j2 in changed_blocks)
            changed_f_lines = sum(j2 - j1 for tag, i1, i2, j1, j2 in changed_blocks)

            print(f"  ── {canonical}")
            print(f"     lines: torrent={len(t_lines):,}  ftp={len(fp_lines):,}")
            print(f"     non-ASCII bytes: torrent={t_nonascii:,}  ftp={fp_nonascii:,}")
            print(f"     line_rstrip={line_match}  aggressive={agg_match}")
            print(f"     diff blocks: {len(changed_blocks)}  "
                  f"changed lines: torrent={changed_t_lines}  ftp={changed_f_lines}")

            # Show up to 3 changed blocks with surrounding context
            shown = 0
            for tag, i1, i2, j1, j2 in changed_blocks:
                if shown >= 3:
                    print(f"     ... ({len(changed_blocks) - shown} more blocks not shown)")
                    break
                ctx = 2
                t_lo, t_hi = max(0, i1 - ctx), min(len(t_lines), i2 + ctx)
                f_lo, f_hi = max(0, j1 - ctx), min(len(fp_lines), j2 + ctx)
                print(f"\n     Block {shown+1}: [{tag}] "
                      f"torrent lines {i1+1}-{i2} / ftp lines {j1+1}-{j2}")
                for ln in range(t_lo, t_hi):
                    marker = '!' if i1 <= ln < i2 else ' '
                    print(f"       t{marker} {ln+1:5}: {t_lines[ln]!r}")
                for ln in range(f_lo, f_hi):
                    marker = '!' if j1 <= ln < j2 else ' '
                    print(f"       f{marker} {ln+1:5}: {fp_lines[ln]!r}")
                shown += 1
            print()

        n = len(deep_diag_pairs)
        if n:
            print(f"  ── Summary across {n} sample pairs ──")
            print(f"  Resolved by per-line rstrip:      {agg_totals['line_rstrip']:>4} / {n}")
            print(f"  Resolved by aggressive norm:      {agg_totals['aggressive']:>4} / {n}")
            print(f"  Still differs:                    {agg_totals['still']:>4} / {n}")
            print(f"  Has non-ASCII (torrent):          {agg_totals['nonascii_t']:>4} / {n}")
            print(f"  Has non-ASCII (ftp):              {agg_totals['nonascii_f']:>4} / {n}")

    # ── 15. Torrent .txt files needing header strip ────────────────
    if RUN['torrent_txt_count']:
        separator("TORRENT .TXT FILES NEEDING HEADER STRIP")
        print("  Counting from unified index — no file reads needed.")
        print("  From sample: 100% of torrent .txt files had the ASSTR header.\n")

        # All torrent .txt canonical paths (regardless of whether other folders have them)
        torrent_txt_all = [
            canonical for canonical, sources in unified.items()
            if canonical.endswith('.txt')
            and any(f == 'torrent' for f, p, h in sources)
        ]

        # Torrent-only: no other folder has this path
        torrent_txt_only = [
            canonical for canonical in torrent_txt_all
            if {f for f, p, h in unified[canonical]} == {'torrent'}
        ]

        # Torrent + ftp conflict: ftp wins, torrent discarded (no strip needed at merge time)
        torrent_txt_has_ftp = [
            canonical for canonical in torrent_txt_all
            if any(f == 'ftp' for f, p, h in unified[canonical])
        ]

        # Torrent + other (non-ftp) conflict: torrent stripped version is the best we have
        torrent_txt_no_ftp = [
            canonical for canonical in torrent_txt_all
            if not any(f == 'ftp' for f, p, h in unified[canonical])
        ]

        print(f"  All torrent .txt canonical paths:       {len(torrent_txt_all):>10,}")
        print(f"  Also in ftp (ftp wins, no strip needed):{len(torrent_txt_has_ftp):>10,}")
        print(f"  NOT in ftp (torrent is best source):    {len(torrent_txt_no_ftp):>10,}")
        print(f"    of which unique to torrent only:      {len(torrent_txt_only):>10,}")
        print(f"    of which in torrent + other non-ftp:  {len(torrent_txt_no_ftp) - len(torrent_txt_only):>10,}")
        print(f"\n  → ~{len(torrent_txt_no_ftp):,} torrent .txt files will need header strip at merge time.")
