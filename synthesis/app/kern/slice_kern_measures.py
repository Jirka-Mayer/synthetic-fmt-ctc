from typing import List
from .remove_kern_leading_and_trailing_barlines import \
    remove_kern_leading_and_trailing_barlines
from .set_skern_type import set_skern_type


def slice_kern_measures(
    kern: str,
    start_measure_index: int,
    end_measure_index: int
) -> str:
    # assumes cleaned up kern for the whole page as input
    assert end_measure_index >= start_measure_index
    
    current_measure = 0

    out_lines: List[str] = []

    for line in kern.splitlines():
        if line.startswith("="):
            current_measure += 1
        if current_measure >= start_measure_index \
            and current_measure <= end_measure_index:
            out_lines.append(line)
    
    remove_kern_leading_and_trailing_barlines(out_lines)
    set_skern_type(out_lines)

    return "\n".join(out_lines)
