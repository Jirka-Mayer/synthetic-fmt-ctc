from typing import Iterable, Generator, List, Tuple
from pathlib import Path
import uuid
import json
import tempfile
import os
from .config import MSCORE_COMMAND


class MuseScoreRefiner:
    """Processes a MusicXML string-file stream and refines the
    MusicXML by passing it through MuseScore in batches."""
    def __init__(
        self,
        source: Iterable[str],
        tmp_folder: Path,
        batch_size=10
    ):
        self.source = source
        self.tmp_folder = tmp_folder
        self.batch_size = batch_size

    def __iter__(self) -> Generator[str, None, None]:
        self.tmp_folder.mkdir(parents=True, exist_ok=True)

        batch: List[str] = []
        
        # go through all the files in the input stream
        for source_xml in self.source:
            
            # stack up a batch of work
            if len(batch) < self.batch_size:
                batch.append(source_xml)
                continue

            # process the batch and yield it
            yield from self._refine_batch(batch)
            batch = []
        
        # process the remainder and yield it
        yield from self._refine_batch(batch)
    
    def _refine_batch(self, batch: List[str]) -> List[str]:
        if len(batch) == 0:
            return []
        
        # generate pairs of paths "crude_file", "refined_file"
        prefix = str(uuid.uuid4())
        conversions = [
            (
                self.tmp_folder / f"{prefix}_crude_{i}.musicxml",
                self.tmp_folder / f"{prefix}_refined_{i}.musicxml"
            )
            for i in range(len(batch))
        ]

        # write the batch to filesystem
        for i, xml in enumerate(batch):
            with open(conversions[i][0], "w") as f:
                f.write(xml)

        # execute musescore
        refine_musicxml_via_musescore(
            conversions=conversions,
            soft=False
        )

        # load the refined batch
        refined_batch: List[str] = []
        for i, xml in enumerate(batch):
            with open(conversions[i][1], "r") as f:
                refined_batch.append(f.read())
        
        # delete all files
        for crude, refined in conversions:
            crude.unlink()
            refined.unlink()
        
        return refined_batch


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
            f"{MSCORE_COMMAND} -j \"{tmp.name}\""
        ) == 0
    finally:
        tmp.close()
        os.unlink(tmp.name)
