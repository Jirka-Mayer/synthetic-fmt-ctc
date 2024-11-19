import converter21
import music21
import music21.stream.base

from .mei_remove_multirests import mei_remove_multirests
from .remove_problematic_notation import remove_problematic_notation


def mei_to_crude_musicxml(mei: str) -> str:
    """Converts a MEI XML string to MusicXML string"""
    
    # replace multimeasure rests with one-measure rests
    patched_mei = mei_remove_multirests(mei)

    # parse MEI to music21
    mei_converter = converter21.MEIConverter()
    score = mei_converter.parseData(patched_mei)
    assert type(score) is music21.stream.base.Score

    # remove grace notes and other mess
    remove_problematic_notation(score)

    # serialize music21 to music xml string
    # (cannot use score.write, because there's a bug in music21
    # that prohibits us from passing an io.StringIO object)
    musicxml_exporter = music21.musicxml.m21ToXml.GeneralObjectExporter()
    crude_musicxml = musicxml_exporter.parse(score).decode("utf-8")

    return crude_musicxml
