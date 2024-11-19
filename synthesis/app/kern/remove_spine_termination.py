from typing import List


def remove_spine_termination(lines: List[str]):
    if lines[-1] == "*-":
        lines.pop()
