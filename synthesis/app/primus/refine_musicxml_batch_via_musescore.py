import json
import os
import subprocess
import tempfile
import uuid
from pathlib import Path
from typing import List, Sequence, Tuple

from ..config import MSCORE_COMMAND


def refine_musicxml_batch_via_musescore(
    musicxml_batch: Sequence[str],
    tmp_folder: Path
) -> List[str]:
    """Refines a list of musicxml strings by passing them through MuseScore
    
    This cleans up voice numbers, measure numbers, fills in stem orientations,
    and much more. Acts as MusicXML canonicalization for the synthesizer.
    """

    tmp_folder.mkdir(parents=True, exist_ok=True)

    # generate pairs of paths "crude_file", "refined_file"
    prefix = str(uuid.uuid4())
    conversions = [
        (
            tmp_folder / f"{prefix}_crude_{i}.musicxml",
            tmp_folder / f"{prefix}_refined_{i}.musicxml"
        )
        for i in range(len(musicxml_batch))
    ]

    # write the batch to filesystem
    for i, xml in enumerate(musicxml_batch):
        with open(conversions[i][0], "w") as f:
            f.write(xml)

    try:

        # execute musescore
        execute_musescore_conversions(
            conversions=conversions,
            soft=False
        )

        # load the refined batch
        refined_batch: List[str] = []
        for i, xml in enumerate(musicxml_batch):
            with open(conversions[i][1], "r") as f:
                refined_batch.append(f.read())
        
    finally:

        # delete all files
        for crude, refined in conversions:
            crude.unlink()
            refined.unlink()
    
    return refined_batch


def execute_musescore_conversions(
    conversions: List[Tuple[Path, Path]],
    soft: bool
):
    """Executes MuseScore on a conversions.json file"""

    # create the conversion json file
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

        result = subprocess.run(
            [MSCORE_COMMAND, "-j", tmp.name],
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            print("MUSESCORE STANDARD ERROR OUTPUT:")
            print(result.stderr)
            raise Exception("MuseScore did not terminate successfully")
    finally:
        tmp.close()
        os.unlink(tmp.name)
