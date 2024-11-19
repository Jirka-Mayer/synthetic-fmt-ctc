from typing import List


def set_skern_type(lines: List[str]):
    # remove any existing type if present
    if lines[0].startswith("**"):
        del lines[0]
    
    # prepend the skern type line
    lines.insert(0, "**skern")
