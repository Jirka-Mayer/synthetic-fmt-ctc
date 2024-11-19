from typing import List
from .remove_kern_comments import remove_kern_comments
from .remove_kern_leading_and_trailing_barlines import \
    remove_kern_leading_and_trailing_barlines
from .remove_kern_measure_numbers import remove_kern_measure_numbers
from .remove_excessive_kern_header_lines import \
    remove_excessive_kern_header_lines
from .set_skern_type import set_skern_type
from .remove_spine_termination import remove_spine_termination


def clean_up_music21_kern_output(kern: str) -> str:
    lines: List[str] = kern.splitlines(keepends=False)

    remove_kern_comments(lines)
    remove_kern_measure_numbers(lines)
    remove_kern_leading_and_trailing_barlines(lines)
    remove_excessive_kern_header_lines(lines)
    remove_spine_termination(lines)
    set_skern_type(lines)

    return "\n".join(lines)
