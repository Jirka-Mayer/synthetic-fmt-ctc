from pathlib import Path
from typing import Tuple, List
import json
import tempfile
import os


# the musescore command
MSCORE = str((
    Path(__file__).parent / ".." / "data" / "musescore.AppImage"
).resolve())


def refine_musicxml_via_musescore(
    conversions: List[Tuple[Path, Path]],
    soft: bool
):
    """We feed the crude musicxml files through musescore to normalize voice numbers,
    measure numbers, part IDs, etc. - to get the "canonical" MusicXML document."""

    # create the conversion json file
    print(f"Preparing musescore batch file...")
    batch_instructions = []
    for source_path, target_path in conversions:
        if soft and target_path.is_file():
            continue
        batch_instructions.append({
            "in": str(source_path),
            "out": str(target_path)
        })
    
    if len(batch_instructions) == 0:
        return

    # run musescore conversion
    tmp = tempfile.NamedTemporaryFile(mode="w", delete=False)
    try:
        json.dump(batch_instructions, tmp)
        tmp.close()

        assert os.system(
            f"{MSCORE} -j \"{tmp.name}\""
        ) == 0
    finally:
        tmp.close()
        os.unlink(tmp.name)