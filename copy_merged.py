import html
import os
import re
import sys
import time

# ── Config ────────────────────────────────────────────────────────────────────

MANIFEST = r"\\MYCLOUDPR4100\Public\asstr\merge_manifest.txt"
DEST     = r"\\MYCLOUDPR4100\Public\asstr_merged"
ERROR_LOG = os.path.join(DEST, "_copy_errors.txt")

# Report progress every this many files, or this many seconds — whichever comes first
PROGRESS_FILES   = 500
PROGRESS_SECONDS = 30

# ── ASSTR header stripping ────────────────────────────────────────────────────

ASSTR_HEADER_RE = re.compile(
    rb'<!--ADULTSONLY-->.*?<pre>\r?\n?',
    re.DOTALL | re.IGNORECASE,
)


def apply_transform(content, transform):
    if transform != 'strip_asstr_header':
        return content
    # Strip the HTML wrapper if present
    if content.lstrip().startswith(b'<!--ADULTSONLY-->'):
        content = ASSTR_HEADER_RE.sub(b'', content, count=1)
    # Decode HTML entities (e.g. &lt;I&gt; → <I>)
    text = content.decode('utf-8', errors='replace')
    text = html.unescape(text)
    return text.encode('utf-8')


# ── Helpers ───────────────────────────────────────────────────────────────────

def load_manifest(path):
    entries = []
    with open(path, 'r', encoding='utf-8') as f:
        for line in f:
            parts = line.rstrip('\n').split('\t')
            if len(parts) == 2:
                entries.append((parts[0], parts[1], None))
            elif len(parts) == 3:
                entries.append((parts[0], parts[1], parts[2]))
    return entries


def format_duration(seconds):
    seconds = int(seconds)
    if seconds < 60:
        return f"{seconds}s"
    if seconds < 3600:
        return f"{seconds // 60}m {seconds % 60:02d}s"
    h, rem = divmod(seconds, 3600)
    return f"{h}h {rem // 60:02d}m {rem % 60:02d}s"


def copy_one(canonical, source_path, transform, dest_root):
    """
    Copy a single file.  Returns 'skipped', 'copied', or raises on error.
    Writes to a .tmp file first then renames atomically so a crash mid-write
    never leaves a partial file at the destination path.
    """
    dest_path = os.path.join(dest_root, canonical.replace('/', os.sep))

    if os.path.exists(dest_path):
        return 'skipped'

    dest_parent = os.path.dirname(dest_path)
    try:
        os.makedirs(dest_parent, exist_ok=True)
    except OSError:
        # A component of the destination path already exists as a file rather than
        # a directory — this is a file/directory name collision in the manifest.
        # Re-run build_manifest.py to regenerate a collision-free manifest.
        raise RuntimeError(
            f"path component is a file, not a directory — "
            f"regenerate the manifest with build_manifest.py"
        )

    tmp_path = dest_path + '.tmp'
    try:
        with open(source_path, 'rb') as fh:
            content = fh.read()

        content = apply_transform(content, transform)

        with open(tmp_path, 'wb') as fh:
            fh.write(content)

        os.replace(tmp_path, dest_path)
        return 'copied'

    except Exception:
        if os.path.exists(tmp_path):
            try:
                os.unlink(tmp_path)
            except OSError:
                pass
        raise


# ── Main ──────────────────────────────────────────────────────────────────────

if __name__ == "__main__":

    print(f"Manifest : {MANIFEST}")
    print(f"Dest     : {DEST}")
    print(f"Error log: {ERROR_LOG}")

    print("\nLoading manifest...")
    try:
        entries = load_manifest(MANIFEST)
    except FileNotFoundError:
        print(f"ERROR: manifest not found: {MANIFEST}")
        sys.exit(1)
    total = len(entries)
    print(f"  {total:,} entries")

    os.makedirs(DEST, exist_ok=True)
    error_log = open(ERROR_LOG, 'a', encoding='utf-8')

    copied = skipped = errors = 0
    t_start     = time.monotonic()
    t_last      = t_start
    n_last      = 0

    print(f"\nStarting... (progress every {PROGRESS_FILES:,} files or {PROGRESS_SECONDS}s)\n")

    for i, (canonical, source_path, transform) in enumerate(entries, 1):
        try:
            result = copy_one(canonical, source_path, transform, DEST)
            if result == 'skipped':
                skipped += 1
            else:
                copied += 1
        except Exception as e:
            errors += 1
            msg = f"[{i}] {canonical}\t{source_path}\t{e}\n"
            error_log.write(msg)
            error_log.flush()
            # Print first few errors to console so they're visible
            if errors <= 10:
                print(f"  ERROR: {canonical}: {e}")
            elif errors == 11:
                print(f"  (further errors only written to {ERROR_LOG})")

        # Progress report
        now = time.monotonic()
        if i % PROGRESS_FILES == 0 or (now - t_last) >= PROGRESS_SECONDS:
            elapsed_total = now - t_start
            elapsed_since = now - t_last
            files_since   = i - n_last

            rate_overall  = i / elapsed_total if elapsed_total > 0 else 0
            rate_recent   = files_since / elapsed_since if elapsed_since > 0 else 0
            remaining     = total - i
            eta_sec       = remaining / rate_recent if rate_recent > 0 else 0

            print(
                f"  {i:>9,}/{total:,} ({100*i/total:.1f}%) | "
                f"copied={copied:,}  skipped={skipped:,}  errors={errors} | "
                f"rate={rate_recent:.0f}/s  ETA={format_duration(eta_sec)}"
            )
            t_last = now
            n_last = i

    error_log.close()

    elapsed = time.monotonic() - t_start
    print(f"\n{'='*60}")
    print(f"  Finished in {format_duration(elapsed)}")
    print(f"  Copied:  {copied:,}")
    print(f"  Skipped: {skipped:,}  (already existed — resume count)")
    print(f"  Errors:  {errors:,}")
    if errors:
        print(f"  See {ERROR_LOG} for details")
    print('='*60)
