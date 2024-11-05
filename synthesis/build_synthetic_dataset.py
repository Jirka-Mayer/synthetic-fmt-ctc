from typing import Generator, Tuple
from pathlib import Path, PosixPath
import xml.etree.ElementTree as ET
import tarfile
import music21
import converter21
from tqdm import tqdm
from enumerate_primus_mei import enumerate_primus_mei
from smashcima.orchestration.BaseHandwrittenModel import BaseHandwrittenModel
import cv2
from refine_musicxml_via_musescore import refine_musicxml_via_musescore


def build_synthetic_dataset(primus_tgz_path: Path):
    for item_path, mei in enumerate_primus_mei(primus_tgz_path):
        crude_xml_path = primus_tgz_path.parent / "test.crude.musicxml"
        crude_kern_path = primus_tgz_path.parent / "test.crude.krn"
        refined_xml_path = primus_tgz_path.parent / "test.refined.musicxml"
        refined_kern_path = primus_tgz_path.parent / "test.refined.krn"
        png_path = primus_tgz_path.parent / "test.png"
        
        # MEI to crude XML and kern
        score = music21.converter.parseData(mei, format="mei")
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
        model = BaseHandwrittenModel()
        model(str(refined_xml_path))
        img = model.render(page_index=0)
        cv2.imwrite(str(png_path), img)

        # only one sample
        return
    

# .venv/bin/python3 build_synthetic_dataset.py
if __name__ == "__main__":
    converter21.register()
    data_folder = (Path(__file__).parent / ".." / "data").resolve()
    build_synthetic_dataset(
        primus_tgz_path=data_folder / "primusCalvoRizoAppliedSciences2018.tgz",
    )
