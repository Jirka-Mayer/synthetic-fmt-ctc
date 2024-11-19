from typing import List


def remove_kern_measure_numbers(lines: List[str]):
    for i, line in enumerate(lines):
        if line.startswith("="):
            lines[i] = "="
