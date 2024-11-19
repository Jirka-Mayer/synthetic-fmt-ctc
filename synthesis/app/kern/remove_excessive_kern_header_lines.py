from typing import List


BLACKLIST_PREFIXES = [
    "*part1",
    "*staff1",
    "*I\"Piano",
    "*I'Pno",
    "*met"
]


def remove_excessive_kern_header_lines(lines: List[str]):
    indices_to_remove: List[int] = []

    for i, line in enumerate(lines):
        for prefix in BLACKLIST_PREFIXES:
            if line.startswith(prefix):
                indices_to_remove.append(i)

    for i in reversed(indices_to_remove):
        del lines[i]
