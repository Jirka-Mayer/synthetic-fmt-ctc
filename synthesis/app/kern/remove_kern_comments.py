from typing import List


def remove_kern_comments(lines: List[str]):
    """Removes comment lines and empty lines"""
    indices_to_dump: List[int] = []
    for i, line in enumerate(lines):
        if line.startswith("!!") or line.strip() == "":
            indices_to_dump.append(i)
    
    # remove indices from the end (so that indexes remain permanent)
    for i in reversed(indices_to_dump):
        del lines[i]
