from typing import Generator, Iterable
from pathlib import Path
import converter21.mei
import music21
import converter21
from smashcima.orchestration.BaseHandwrittenModel import BaseHandwrittenModel
import cv2
from Primus2018Enumerator import Primus2018Enumerator
from mei_remove_multirests import mei_remove_multirests
from remove_problematic_notation import remove_problematic_notation
from AsIterable import AsIterable
from MuseScoreRefiner import MuseScoreRefiner
import uuid


def build_synthetic_dataset(
    primus_tgz_path: Path,
    tmp_folder: Path
):
    xml_stream = prepare_xml_incipit_stream(
        primus_tgz_path=primus_tgz_path,
        tmp_folder=tmp_folder
    )
    
    model = BaseHandwrittenModel()

    for i, xml in enumerate(xml_stream):
        # HACK: only 10 samples
        if i >= 10:
            return
        
        print("Synthesizing", i, "...")

        output_path = primus_tgz_path.parent / "test"
        output_path.mkdir(exist_ok=True, parents=True)

        xml_path = output_path / f"test_{i}.musicxml"
        kern_path = output_path / f"test_{i}.krn"
        png_path = output_path / f"test_{i}.png"
        
        # # TODO: DEBUG:
        # score.show("text")
        
        # # TODO: DEBUG: try merging two parts
        # import copy
        # score.parts[0].append(copy.deepcopy(score.parts[0].elements))
        
        # # TODO: DEBUG: add a dummy linebreak
        # system_break = music21.layout.SystemLayout(isNew=True)
        # m = score.parts[0].measure(5)
        # m.insert(0, system_break)

        # parse the score
        score = music21.converter.parseData(xml, format="musicxml")
        
        # gets the measure count
        # print(
        #     len(
        #         score.parts[0].getElementsByClass(music21.stream.Measure)
        #     )
        # )

        # convert to kern
        # and write to a file
        score.write("krn", kern_path)

        # HACK: write refined xml to file
        # (because the synthesizer loads it from a file)
        with open(xml_path, "w") as f:
            f.write(xml)

        # synthesis
        model(str(xml_path))
        img = model.render(page_index=0)
        cv2.imwrite(str(png_path), img)


def prepare_xml_incipit_stream(
    primus_tgz_path: Path,
    tmp_folder: Path
) -> Iterable[str]:
    # load the primus dataset as a sequence of incipits
    primus = Primus2018Enumerator(primus_tgz_path)

    # extract the MEI string from each primus incipit
    mei_stream = AsIterable(lambda: (yield from (
        incipit.mei for incipit in primus
    )))

    # clean up the music notation (e.g. remove multirests)
    # and convert to crude music xml
    crude_xml_stream = AsIterable(lambda: mei_to_crude_xml(mei_stream))

    # refine the music xml (e.g. assign stem orientation)
    refined_xml_stream = MuseScoreRefiner(
        source=crude_xml_stream,
        tmp_folder=tmp_folder
    )

    return refined_xml_stream


def mei_to_crude_xml(
    mei_stream: Iterable[str]
) -> Generator[str, None, None]:
    for mei in mei_stream:
        # replace multimeasure rests with one-measure rests
        patched_mei = mei_remove_multirests(mei)

        # parse MEI to music21
        score = music21.converter.parseData(patched_mei, format="mei")

        # remove grace notes and other mess
        remove_problematic_notation(score)

        # serialize music21 to music xml string
        # (cannot use score.write, because there's a bug in music21
        # that prohibits us from passing an io.StringIO object)
        exporter = music21.musicxml.m21ToXml.GeneralObjectExporter()
        crude_xml = exporter.parse(score).decode("utf-8")

        yield crude_xml


# .venv/bin/python3 build_synthetic_dataset.py
if __name__ == "__main__":
    converter21.register()
    data_folder = (Path(__file__).parent / ".." / "data").resolve()
    build_synthetic_dataset(
        primus_tgz_path=data_folder / "primusCalvoRizoAppliedSciences2018.tgz",
        tmp_folder=data_folder / "tmp"
    )
