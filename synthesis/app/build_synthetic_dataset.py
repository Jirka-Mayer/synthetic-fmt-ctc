from typing import Generator, Iterable, Tuple
from pathlib import Path
import converter21.mei
import music21
import converter21
import music21.stream.base
import cv2
from .Primus2018Enumerator import Primus2018Enumerator
from .mei_remove_multirests import mei_remove_multirests
from .remove_problematic_notation import remove_problematic_notation
from .AsIterable import AsIterable
from .MuseScoreRefiner import MuseScoreRefiner
from .ModelM import ModelM
import random
import logging


def build_synthetic_dataset(
    primus_tgz_path: Path,
    tmp_folder: Path
):
    xml_incipit_stream = prepare_xml_incipit_stream(
        primus_tgz_path=primus_tgz_path,
        tmp_folder=tmp_folder
    )

    rng = random.Random(42)
    
    model = ModelM()

    # start iteration
    xml_incipit_generator = iter(xml_incipit_stream)

    # generate 10 pages
    for i in range(10):
        score = pull_music21_score(
            xml_incipit_generator,
            measures_per_staff=(3, 5),
            staves=(3, 4),
            rng=rng
        )
        
        print("Synthesizing", i, "...")

        output_path = primus_tgz_path.parent / "test"
        output_path.mkdir(exist_ok=True, parents=True)

        kern_path = output_path / f"test_{i}.krn"
        png_path = output_path / f"test_{i}.png"
        xml_path = output_path / f"test_{i}.musicxml"
        
        # score to MusicXML string for the synthesizer
        exporter = music21.musicxml.m21ToXml.GeneralObjectExporter()
        xml = exporter.parse(score).decode("utf-8")

        # synthesis
        try:
            scene = model(data=xml, format=".musicxml")
            assert len(scene.pages) == 1, "Expected only one page"
            img = scene.render(scene.pages[0])
            cv2.imwrite(str(png_path), img)
        except:
            logging.exception("Synthesis crash:")
            continue

        # convert to kern
        # and write to a file
        score.write("krn", kern_path)

        # store the xml that goes into the synthesizer
        with open(xml_path, "w") as f:
            f.write(xml)


def pull_music21_score(
    xml_generator: Generator[str, None, None],
    measures_per_staff: Tuple[int, int], # from, to
    staves: Tuple[int, int], # from, to
    rng: random.Random
) -> music21.stream.base.Score:
    # get the desired measure schema first
    schema = []
    for _ in range(rng.randint(*staves)):
        schema.append(rng.randint(*measures_per_staff))
    desired_measure_count = sum(schema)
    
    # start with one incipit
    xml = next(xml_generator)
    score = music21.converter.parseData(xml, format="musicxml")
    assert type(score) is music21.stream.base.Score

    # add more incipits until we get the desired number of measures
    while len(score.parts[0].getElementsByClass(music21.stream.Measure)) \
            < desired_measure_count:
        xml = next(xml_generator)
        next_score = music21.converter.parseData(xml, format="musicxml")
        assert type(next_score) is music21.stream.base.Score

        # append the next score into the first score
        score.parts[0].append(next_score.parts[0].elements)
    
    # take the EXACT measures we want, not more
    score = score.measures(0, desired_measure_count - 1, indicesNotNumbers=True)
    
    # add system breaks according to the schema
    current_measure = 0
    for step in schema:
        current_measure += step
        m = score.parts[0].measure(current_measure, indicesNotNumbers=True)
        if m is not None:
            # remove system layout if already present
            # (which happens at incipit starts and that disables our break)
            m.removeByClass(music21.layout.SystemLayout)
            m.insert(0, music21.layout.SystemLayout(isNew=True))
    
    return score


def prepare_xml_incipit_stream(
    primus_tgz_path: Path,
    tmp_folder: Path
) -> Iterable[str]:
    # load the primus dataset as a sequence of incipits
    primus = Primus2018Enumerator(primus_tgz_path)

    # extract the MEI string from each primus incipit
    mei_stream = AsIterable(lambda: primus_to_mei(primus))

    # clean up the music notation (e.g. remove multirests)
    # and convert to crude music xml
    crude_xml_stream = AsIterable(lambda: mei_to_crude_xml(mei_stream))

    # refine the music xml (e.g. assign stem orientation)
    refined_xml_stream = MuseScoreRefiner(
        source=crude_xml_stream,
        tmp_folder=tmp_folder
    )

    return refined_xml_stream


def primus_to_mei(primus: Primus2018Enumerator) -> Generator[str, None, None]:
    for incipit in primus:
        yield incipit.mei


def mei_to_crude_xml(
    mei_stream: Iterable[str]
) -> Generator[str, None, None]:
    for mei in mei_stream:
        # replace multimeasure rests with one-measure rests
        patched_mei = mei_remove_multirests(mei)

        # parse MEI to music21
        score = music21.converter.parseData(patched_mei, format="mei")
        assert type(score) is music21.stream.base.Score

        # remove grace notes and other mess
        remove_problematic_notation(score)

        # serialize music21 to music xml string
        # (cannot use score.write, because there's a bug in music21
        # that prohibits us from passing an io.StringIO object)
        exporter = music21.musicxml.m21ToXml.GeneralObjectExporter()
        crude_xml = exporter.parse(score).decode("utf-8")

        yield crude_xml


# .venv/bin/python3 -m app.build_synthetic_dataset
if __name__ == "__main__":
    from .config import PRIMUS_TGZ_PATH, TMP_FOLDER
    converter21.register()
    build_synthetic_dataset(
        primus_tgz_path=PRIMUS_TGZ_PATH,
        tmp_folder=TMP_FOLDER
    )
