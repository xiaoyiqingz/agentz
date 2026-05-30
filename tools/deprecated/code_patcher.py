import os
import re
from typing import List


def apply_patch(patch_string: str, file_path: str, backup: bool = True) -> bool:
    """
    Apply a patch string to a file, similar to the patch command.

    Args:
        patch_string: The patch content in unified diff format
        file_path: Path to the target file to patch
        backup: Whether to create a backup file before applying the patch

    Returns:
        bool: True if patch was applied successfully, False otherwise
    """
    # print(f"Applying patch to {file_path}")
    # print(f"Patch string: {patch_string}")
    try:
        # Parse the patch
        hunks = _parse_patch(patch_string)
        if not hunks:
            return False

        # Read the original file
        if not os.path.exists(file_path):
            return False

        with open(file_path, "r", encoding="utf-8") as f:
            original_lines = f.readlines()

        # Create backup if requested
        if backup:
            backup_path = file_path + ".orig"
            with open(backup_path, "w", encoding="utf-8") as f:
                f.writelines(original_lines)

        # Apply hunks to the file
        patched_lines = _apply_hunks(original_lines, hunks)

        # Write the patched content
        with open(file_path, "w", encoding="utf-8") as f:
            f.writelines(patched_lines)

        return True

    except Exception as e:
        print(f"Error applying patch: {e}")
        return False


def _parse_patch(patch_string: str) -> List[dict]:
    """
    Parse a patch string and extract hunks.

    Args:
        patch_string: The patch content

    Returns:
        List of hunk dictionaries containing line numbers and changes
    """
    lines = patch_string.split("\n")
    hunks = []
    current_hunk = None

    for line in lines:
        # Match hunk header: @@ -start,count +start,count @@
        hunk_match = re.match(r"@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@", line)
        if hunk_match:
            if current_hunk:
                hunks.append(current_hunk)

            old_start = int(hunk_match.group(1))
            old_count = int(hunk_match.group(2)) if hunk_match.group(2) else 1
            new_start = int(hunk_match.group(3))
            new_count = int(hunk_match.group(4)) if hunk_match.group(4) else 1

            current_hunk = {
                "old_start": old_start,
                "old_count": old_count,
                "new_start": new_start,
                "new_count": new_count,
                "changes": [],
            }
        elif current_hunk and line.startswith((" ", "+", "-")):
            current_hunk["changes"].append(line)

    if current_hunk:
        hunks.append(current_hunk)

    return hunks


def _apply_hunks(original_lines: List[str], hunks: List[dict]) -> List[str]:
    """
    Apply hunks to the original file lines.

    Args:
        original_lines: Original file content as list of lines
        hunks: List of hunk dictionaries

    Returns:
        Modified file content as list of lines
    """
    result_lines = original_lines.copy()

    # Process hunks in reverse order to maintain line number accuracy
    for hunk in reversed(hunks):
        old_start = hunk["old_start"] - 1  # Convert to 0-based index
        old_count = hunk["old_count"]
        changes = hunk["changes"]

        # Remove the old lines
        del result_lines[old_start : old_start + old_count]

        # Insert new lines
        new_lines = []
        for change in changes:
            if change.startswith("+"):
                new_lines.append(change[1:] + "\n")
            elif change.startswith(" "):
                new_lines.append(change[1:] + "\n")

        # Insert the new lines
        for i, new_line in enumerate(new_lines):
            result_lines.insert(old_start + i, new_line)

    return result_lines


def create_patch(old_file: str, new_file: str) -> str:
    """
    Create a patch string from two file contents.

    Args:
        old_file: Path to the original file
        new_file: Path to the modified file

    Returns:
        Patch string in unified diff format
    """
    try:
        with open(old_file, "r", encoding="utf-8") as f:
            old_lines = f.readlines()
        with open(new_file, "r", encoding="utf-8") as f:
            new_lines = f.readlines()

        return _generate_unified_diff(old_lines, new_lines, old_file, new_file)
    except Exception as e:
        print(f"Error creating patch: {e}")
        return ""


def _generate_unified_diff(
    old_lines: List[str], new_lines: List[str], old_file: str, new_file: str
) -> str:
    """
    Generate a unified diff between two file contents.

    Args:
        old_lines: Original file lines
        new_lines: Modified file lines
        old_file: Original file path
        new_file: Modified file path

    Returns:
        Unified diff string
    """
    # Simple diff implementation - in practice, you might want to use difflib
    diff_lines = []
    diff_lines.append(f"--- {old_file}")
    diff_lines.append(f"+++ {new_file}")

    # Find differences (simplified implementation)
    old_len = len(old_lines)
    new_len = len(new_lines)
    max_len = max(old_len, new_len)

    changes = []
    for i in range(max_len):
        old_line = old_lines[i] if i < old_len else ""
        new_line = new_lines[i] if i < new_len else ""

        if old_line != new_line:
            if old_line:
                changes.append(f"-{old_line.rstrip()}")
            if new_line:
                changes.append(f"+{new_line.rstrip()}")
        else:
            changes.append(f" {old_line.rstrip()}")

    if changes:
        diff_lines.append(f"@@ -1,{old_len} +1,{new_len} @@")
        diff_lines.extend(changes)

    return "\n".join(diff_lines)


# Example usage and test function
def test_patch_functionality():
    """
    Test the patch functionality with the example from the user query.
    """
    # Create test files
    test_file = "./info.py"
    patch_content = """--- info.py     2025-09-18 20:47:45
+++ info1.py    2025-09-17 23:25:48
@@ -11,9 +11,9 @@
 def get_current_info() -> Dict[str, str]:
     now = datetime.datetime.now()
     return {
-        "time": now.strftime("%Y-%m-%d %H:%M:%S"),
+        "time": now.strftime("%Y-%m-%d %H:%M:%S"),  # 当前时间
         "date": now.strftime("%Y年%m月%d日"),
-        "weekday": now.strftime("%A"),
+        "weekday": now.strftime("%A"),  # 当前星期
         "timestamp": str(int(now.timestamp())),
     }"""

    print("Original file content:")
    with open(test_file, "r") as f:
        print(f.read())

    # Apply patch
    success = apply_patch(patch_content, test_file)
    print(f"\nPatch applied successfully: {success}")

    print("\nPatched file content:")
    with open(test_file, "r") as f:
        print(f.read())

    # Clean up
    # if os.path.exists(test_file):
    #     os.remove(test_file)
    # if os.path.exists(test_file + ".orig"):
    #     os.remove(test_file + ".orig")


if __name__ == "__main__":
    test_patch_functionality()
