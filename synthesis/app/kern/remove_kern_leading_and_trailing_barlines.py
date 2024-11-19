from typing import List, Iterable, Optional


def remove_kern_leading_and_trailing_barlines(lines: List[str]):
    """Removes barlines that are at the begging or end of the content"""
    # remove the leading barline
    index = _first_index_with_bar_before_content(lines)
    if index is not None:
        del lines[index]
    
    # remove the trailing barline
    index = _first_index_with_bar_before_content(
        reversed(lines)
    )
    if index is not None:
        del lines[-index - 1]


def _first_index_with_bar_before_content(
    lines: Iterable[str]
) -> Optional[int]:
    for i, line in enumerate(lines):
        
        # skip header lines and comments and empty lines
        if line.startswith("!!") \
            or line.startswith("*") \
            or line.strip() == "":
            continue

        # now we are hitting the first line with content,
        # if it's a barline, we have it

        if line.startswith("="):
            return i
        else:
            return None

    # there was no content
    return None
