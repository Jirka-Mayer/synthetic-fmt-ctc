import io
import sys
from typing import Iterator, List, Optional

import music21
import music21.stream.base
import smashcima as sc
from converter21.humdrum.humdrumwriter import HumdrumWriter

from ..primus.start_primus_musicxml_iterator import MusicXmlIncipit
from .PageContent import PageContent
from .PageLayout import PageLayout


def pull_page_from_musicxml_iterator(
    primus_musicxml_iterator: Iterator[MusicXmlIncipit],
    page_layout: PageLayout
) -> Optional[PageContent]:
    """Pulls incipits from an iterator to build the desired page content"""
    
    incipits: List[MusicXmlIncipit] = []
    music21_scores: List[music21.stream.base.Score] = []
    taken_measures = 0

    # take incipits until we have desired measure count
    for incipit in primus_musicxml_iterator:
        incipits.append(incipit)
        music21_score = _parse_to_music21(incipit.musicxml)
        taken_measures += _count_measures(music21_score)
        music21_scores.append(music21_score)

        if taken_measures >= page_layout.total_measures:
            break

    # no more incipits available
    if taken_measures == 0:
        return None
    
    # build the complete music21 score
    music21_score = _concatenate_music21_scores_and_clip(
        music21_scores,
        desired_measures=page_layout.total_measures
    )
    _introduce_system_breaks(music21_score, page_layout)

    # get the complete score MusicXML
    musicxml_exporter = music21.musicxml.m21ToXml.GeneralObjectExporter()
    musicxml = musicxml_exporter.parse(music21_score).decode("utf-8")

    # parse to smashcima score
    smashcima_loader = sc.loading.MusicXmlLoader(errout=sys.stdout)
    smashcima_score = smashcima_loader.load_xml(musicxml)

    # export the score to kern
    kern = _music21_to_kern(music21_score)

    # TODO: clean up the output kern here

    return PageContent(
        identifier=_build_page_identifier(incipits),
        layout=page_layout,
        incipits=incipits,
        music21_score=music21_score,
        musicxml=musicxml,
        smashcima_score=smashcima_score,
        kern=kern
    )


def _parse_to_music21(musicxml: str) -> music21.stream.base.Score:
    score = music21.converter.parseData(musicxml, format="musicxml")
    assert type(score) is music21.stream.base.Score
    return score


def _count_measures(score: music21.stream.base.Score) -> int:
    return len(
        score.parts[0].getElementsByClass(music21.stream.Measure)
    )


def _concatenate_music21_scores_and_clip(
    scores: List[music21.stream.base.Score],
    desired_measures: int
) -> music21.stream.base.Score:
    assert len(scores) > 0
    
    out_score = scores[0]
    
    for score in scores[1:]:
        # remove the system layout element from the first measure,
        # as that introduces problems when inserting our breaks
        first_measure = score.parts[0].measure(0, indicesNotNumbers=True)
        assert first_measure is not None
        first_measure.removeByClass(music21.layout.SystemLayout)

        # append
        out_score.parts[0].append(score.parts[0].elements)
    
    # clip the desired measure count and return
    return out_score.measures(
        0,
        desired_measures - 1,
        indicesNotNumbers=True
    )


def _introduce_system_breaks(
    score: music21.stream.base.Score,
    layout: PageLayout
):
    current_measure = 0
    for step in layout.measures_per_staff:
        current_measure += step
        measure = score.parts[0].measure(
            current_measure,
            indicesNotNumbers=True
        )
        if measure is not None:
            measure.insert(0, music21.layout.SystemLayout(isNew=True))


def _music21_to_kern(score: music21.stream.base.Score) -> str:
    dummy_file = io.StringIO()
    kern_writer = HumdrumWriter(score)
    kern_writer.write(dummy_file)
    dummy_file.seek(0)
    return dummy_file.read()

def _build_page_identifier(incipits: List[MusicXmlIncipit]) -> str:
    id = incipits[0].original_incipit.incipit_id
    id = id.replace(".", "")
    id = id.strip("/").replace("/", "_")
    return id + "_len" + str(len(incipits))
