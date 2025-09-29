import re
import os
from pathlib import Path
from difflib import SequenceMatcher # slow
try:
    # Try using the faster C implementation
    from cydifflib import SequenceMatcher as FastMatcher
    SequenceMatcher = FastMatcher
    print("Using cydifflib for faster diffs")
except ImportError:
    # Fall back to the Python stdlib
    FastMatcher = None
    print("cydifflib not available, using standard difflib")

ENTRY_REGEX = re.compile(
    r'^(\S+)\s+-\s+[^\n]+\n*?(?:[\w{}<>()=:_\[\]\|\\\/#.!,;\'"\b\d\s+-@]+?)?\n*Supported Scopes:',
    re.MULTILINE
)

ENTRY_BLOCK_REGEX = re.compile(
    r'^(\S+)\s+-\s+[^\n]+\n(.*?)(?=\n\S+ - |\Z)',
    re.MULTILINE | re.DOTALL
)

def similar(a: str, b: str) -> float:
    return SequenceMatcher(None, a, b).ratio()

def detect_renames(old_blocks: dict, new_blocks: dict, threshold=0.74):
    renamed = []
    old_names = set(old_blocks) - set(new_blocks)
    new_names = set(new_blocks) - set(old_blocks)
    for old in old_names:
        for new in new_names:
            sim = similar(old_blocks[old], new_blocks[new])
            if sim >= threshold:
                renamed.append((old, new, sim))
    return renamed

def extract_blocks(file_path: Path) -> dict[str, str]:
    """
    Extracts a dictionary of {entry_name: description_block} from a log file.
    """
    if not file_path.exists():
        print(f"[!] File not found: {file_path}")
        return {}
    content = file_path.read_text(encoding='utf-8')
    matches = ENTRY_BLOCK_REGEX.findall(content)
    return {name: desc.strip() for name, desc in matches}

# def extract_entries(file_path: Path) -> set[str]:
#     if not file_path.exists():
#         print(f"[!] File not found: {file_path}")
#         return set()
#     content = file_path.read_text(encoding='utf-8')
#     return set(ENTRY_REGEX.findall(content))

def compare_sets(old_set: set[str], new_set: set[str]) -> tuple[set[str], set[str]]:
    added = new_set - old_set
    removed = old_set - new_set
    return added, removed

def write_markdown_report(path: Path, triggers_diff, effects_diff):
    def format_md_section(title: str, added: set[str], removed: set[str], renamed: set[str]) -> str:
        section = f"## {title} Comparison\n\n"

        if added:
            section += "### 🟢 Added\n"
            for a in sorted(added):
                section += f"- {a}\n"
            section += "\n"
        if removed:
            section += "### 🔴 Removed\n"
            for r in sorted(removed):
                section += f"- {r}\n"
            section += "\n"
        if renamed:
            section += "### 🔄 Possibly Renamed\n"
            for old, new, sim in renamed:
                section += f"- `{old}` ➜ `{new}` (similarity {sim:.2f})\n"
            section += "\n"

        if not added and not removed:
            section += "_No changes detected._\n\n"

        print(section)
        return section

    report = "# Stellaris Script Documentation Diff\n\n"
    report += format_md_section("Triggers", *triggers_diff)
    report += format_md_section("Effects", *effects_diff)

    path.write_text(report, encoding='utf-8')
    print(f"\n📄 Markdown report written to: {path.resolve()}")

def get_default_script_doc_path() -> Path:
    # Windows Steam installation user log path
    base_dir = Path(os.environ["USERPROFILE"])
    return base_dir / "Documents" / "Paradox Interactive" / "Stellaris" / "logs" / "script_documentation"

def main():
    # Input Paths
    base_path = get_default_script_doc_path()  # Base Game logs (treated as NEW)
    base_path = Path("d:\\GOG Games\\Settings\\Stellaris\\logs\\Stellaris.logs.4.0")  # Base Game logs (treated as NEW)
    mod_path = Path("d:\\GOG Games\\Settings\\Stellaris\\logs\\Stellaris.logs.3.14")  # Mod logs (treated as OLD)

    # Extracting blocks:
    old_triggers_blocks = extract_blocks(mod_path / 'triggers.log')
    new_triggers_blocks = extract_blocks(base_path / 'triggers.log')
    old_effects_blocks = extract_blocks(mod_path / 'effects.log')
    new_effects_blocks = extract_blocks(base_path / 'effects.log')

    # Triggers
    old_triggers = set(old_triggers_blocks)
    new_triggers = set(new_triggers_blocks)
    added_triggers, removed_triggers = compare_sets(old_triggers, new_triggers)
    renamed_triggers = detect_renames(old_triggers_blocks, new_triggers_blocks)

    # Effects
    old_effects = set(old_effects_blocks)
    new_effects = set(new_effects_blocks)
    added_effects, removed_effects = compare_sets(old_effects, new_effects)
    renamed_effects = detect_renames(old_effects_blocks, new_effects_blocks)

    # Filter out renamed pairs from added/removed
    ren_old_t = {o for o,_,_ in renamed_triggers}
    ren_new_t = {n for _,n,_ in renamed_triggers}
    added_triggers -= ren_new_t
    removed_triggers -= ren_old_t

    # Filter out renamed pairs from added/removed
    ren_old_e = {o for o,_,_ in renamed_effects}
    ren_new_e = {n for _,n,_ in renamed_effects}
    added_effects -= ren_new_e
    removed_effects -= ren_old_e

    # Write Markdown Report
    write_markdown_report(Path("diff_report.md"),
                          (added_triggers, removed_triggers, renamed_triggers),
                          (added_effects, removed_effects, renamed_effects))

if __name__ == '__main__':
    main()
