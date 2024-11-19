from dataclasses import dataclass
from typing import List
import music21.stream.base

import smashcima as sc

from ..primus.start_primus_musicxml_iterator import MusicXmlIncipit
from .PageLayout import PageLayout


@dataclass
class PageContent:
    """Semantic content of a synthesized page"""

    identifier: str
    """String identifier of the page, used for resulting file names"""
    
    layout: PageLayout
    """Layout of the page"""

    incipits: List[MusicXmlIncipit]
    """Primus MusicXml incipits that make up the content of this page"""

    music21_score: music21.stream.base.Score
    """The Music21 score of the content"""

    musicxml: str
    """MusicXML contents of the page"""

    smashcima_score: sc.Score
    """The smashcima score of the content"""

    kern: str
    """The kern contents of the page"""
