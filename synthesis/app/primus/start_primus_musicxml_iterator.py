import itertools
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator
import tqdm

from .mei_to_crude_musicxml import mei_to_crude_musicxml
from .Primus2018Iterable import Incipit, Primus2018Iterable
from .refine_musicxml_batch_via_musescore import \
    refine_musicxml_batch_via_musescore


@dataclass
class MusicXmlIncipit:
    musicxml: str
    original_incipit: Incipit


def start_primus_musicxml_iterator(
    primus_tgz_path: Path,
    tmp_folder: Path,
    musescore_batch_size: int,
    with_tqdm: bool = False
) -> Iterator[MusicXmlIncipit]:
    """Returns an iterator that returns MusicXML incipits"""

    primus = Primus2018Iterable(primus_tgz_path)

    if with_tqdm:
        progress_bar = tqdm.tqdm(total=len(primus))

    primus_iterator = iter(primus)
    
    while incipit_batch := tuple(
        itertools.islice(primus_iterator, musescore_batch_size)
    ):
        crude_musicxml_batch = tuple(
            mei_to_crude_musicxml(incipit.mei)
            for incipit in incipit_batch
        )
        
        refined_musicxml_batch = refine_musicxml_batch_via_musescore(
            musicxml_batch=crude_musicxml_batch,
            tmp_folder=tmp_folder
        )

        for musicxml, incipit in zip(
            refined_musicxml_batch, incipit_batch
        ):
            if with_tqdm:
                progress_bar.update(1)

            yield MusicXmlIncipit(
                musicxml=musicxml,
                original_incipit=incipit
            )
    
    if with_tqdm:
        progress_bar.close()
