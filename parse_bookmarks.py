import html.parser
import os

INPUT = (
    r"C:\Users\greg\Downloads\bookmarks_5_7_26.html"
)
OUTPUT = (
    r"C:\Users\greg\Downloads\bookmarks_extracted.txt"
)
TARGET_FOLDERS = {"food", "Baking"}


class BookmarkParser(html.parser.HTMLParser):
    def __init__(self):
        super().__init__()
        # Stack of (folder_name, dl_depth_when_entered)
        # dl_depth_when_entered = DL depth at the time we pushed this folder
        self.folder_stack = []
        self.dl_depth = 0

        # Pending folder name (between <H3> and </H3>)
        self._pending_folder = None
        # dl_depth at the time <H3> was opened (the DL this folder belongs to)
        self._h3_dl_depth = None

        # Active link state
        self._link_href = None
        self._link_text_parts = []

        # Whether we're inside a target top-level folder
        self._in_target = False
        # Which top-level folder we're in
        self._top_folder = None
        # dl_depth when we entered the target top-level folder's <DL>
        self._target_entry_dl_depth = None

        self.results = []  # list of (folder_path, title, url)

    def handle_starttag(self, tag, attrs):
        attrs_dict = dict(attrs)
        if tag == "dl":
            self.dl_depth += 1
        elif tag == "h3":
            self._pending_folder = []
            self._h3_dl_depth = self.dl_depth
        elif tag == "a" and self._in_target:
            href = attrs_dict.get("href", "")
            self._link_href = href
            self._link_text_parts = []

    def handle_endtag(self, tag):
        if tag == "dl":
            # Pop any folders that were opened at this DL depth
            while self.folder_stack and self.folder_stack[-1][1] == self.dl_depth:
                self.folder_stack.pop()
            self.dl_depth -= 1
            # Check if we've exited the target top-level folder (after decrement)
            if (
                self._in_target
                and self._target_entry_dl_depth is not None
                and self.dl_depth < self._target_entry_dl_depth
            ):
                self._in_target = False
                self._top_folder = None
                self._target_entry_dl_depth = None
        elif tag == "h3" and self._pending_folder is not None:
            name = "".join(self._pending_folder).strip()
            # dl_depth right now is the DL the H3 lived in.
            # The subfolder DL will open at dl_depth + 1.
            self.folder_stack.append((name, self.dl_depth + 1))

            # Check if this is a top-level target folder.
            # Top-level means it's a direct child of the root bar (dl_depth == 1 or 2
            # depending on file structure). We detect it by checking if the name matches
            # and we're not already inside a target.
            if not self._in_target and name in TARGET_FOLDERS:
                self._in_target = True
                self._top_folder = name
                self._target_entry_dl_depth = self.dl_depth + 1

            self._pending_folder = None
            self._h3_dl_depth = None
        elif tag == "a" and self._in_target and self._link_href is not None:
            title = "".join(self._link_text_parts).strip()
            url = self._link_href
            # Build folder path starting from the target top-level folder
            all_parts = [f for f, _ in self.folder_stack]
            try:
                start = all_parts.index(self._top_folder)
            except ValueError:
                start = 0
            folder_path = " > ".join(all_parts[start:])
            self.results.append((self._top_folder, folder_path, title, url))
            self._link_href = None
            self._link_text_parts = []

    def handle_data(self, data):
        if self._pending_folder is not None:
            self._pending_folder.append(data)
        elif self._link_href is not None:
            self._link_text_parts.append(data)


def main():
    with open(INPUT, encoding="utf-8") as f:
        content = f.read()

    parser = BookmarkParser()
    parser.feed(content)

    os.makedirs(os.path.dirname(OUTPUT), exist_ok=True)

    counts = {}
    lines = []
    for top_folder, folder_path, title, url in parser.results:
        counts[top_folder] = counts.get(top_folder, 0) + 1
        lines.append(f"{folder_path} | {title} | {url}")

    with open(OUTPUT, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
        if lines:
            f.write("\n")

    print(f"Total bookmarks extracted: {len(lines)}")
    for folder, count in sorted(counts.items()):
        print(f"  {folder}: {count}")
    print(f"\nOutput written to:\n  {OUTPUT}")
    print(f"\nFirst 10 lines:")
    for line in lines[:10]:
        print(" ", line)


if __name__ == "__main__":
    main()
