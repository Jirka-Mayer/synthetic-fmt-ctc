from typing import Generator, Tuple
from pathlib import Path
import converter21.mei
import music21
import converter21
from smashcima.orchestration.BaseHandwrittenModel import BaseHandwrittenModel
import cv2
from refine_musicxml_via_musescore import refine_musicxml_via_musescore
from Primus2018Enumerator import Primus2018Enumerator
from mei_remove_multirests import mei_remove_multirests
from remove_problematic_notation import remove_problematic_notation


def build_synthetic_dataset(primus_tgz_path: Path):
    primus = Primus2018Enumerator(primus_tgz_path)
    
    # synthesis
    model = BaseHandwrittenModel()

    counter = 0
    for incipit in primus:
        output_path = primus_tgz_path.parent / "test"
        output_path.mkdir(exist_ok=True, parents=True)

        mei_path = output_path / f"test_{counter}.mei"
        crude_xml_path = output_path / f"test_{counter}.crude.musicxml"
        crude_kern_path = output_path / f"test_{counter}.crude.krn"
        refined_xml_path = output_path / f"test_{counter}.refined.musicxml"
        refined_kern_path = output_path / f"test_{counter}.refined.krn"
        png_path = output_path / f"test_{counter}.png"

        # replace mulitmeasure rests
        patched_mei = mei_remove_multirests(incipit.mei)

        # write MEI
        with open(mei_path, "w") as f:
            f.write(patched_mei)
        
        # MEI to crude XML and kern
        score = music21.converter.parseData(patched_mei, format="mei")

        remove_problematic_notation(score)

        # # TODO: DEBUG:
        # score.show("text")
        
        # # TODO: DEBUG: try merging two parts
        # import copy
        # score.parts[0].append(copy.deepcopy(score.parts[0].elements))
        
        # # TODO: DEBUG: add a dummy linebreak
        # system_break = music21.layout.SystemLayout(isNew=True)
        # m = score.parts[0].measure(5)
        # m.insert(0, system_break)

        score.write("musicxml", crude_xml_path)
        score.write("krn", crude_kern_path)

        # refine XML
        # NOTE: refining is needed e.g. to re-introduce stem orientation
        refine_musicxml_via_musescore(
            conversions=[(crude_xml_path, refined_xml_path)],
            soft=False
        )

        # refined XML to kern
        score = music21.converter.parseFile(refined_xml_path, format="musicxml")
        score.write("krn", refined_kern_path)

        # synthesis
        model(str(refined_xml_path))
        img = model.render(page_index=0)
        cv2.imwrite(str(png_path), img)

        # only 100 samples
        # return
        counter += 1
        if counter >= 10:
            return


# .venv/bin/python3 build_synthetic_dataset.py
if __name__ == "__main__":
    converter21.register()
    data_folder = (Path(__file__).parent / ".." / "data").resolve()
    build_synthetic_dataset(
        primus_tgz_path=data_folder / "primusCalvoRizoAppliedSciences2018.tgz",
    )
