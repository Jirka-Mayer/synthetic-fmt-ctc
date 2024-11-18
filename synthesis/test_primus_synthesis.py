import converter21
from pathlib import Path
from build_synthetic_dataset import prepare_xml_incipit_stream
from Primus2018Enumerator import Primus2018Enumerator
import smashcima as sc
import logging
import traceback
import tqdm


class TestModel(sc.orchestration.BaseHandwrittenModel):
    def register_services(self):
        super().register_services()
        
        # disable fancy background to speed up synthesis
        self.container.interface(
            sc.synthesis.PaperSynthesizer,
            sc.synthesis.SolidColorPaperSynthesizer
        )


def test_primus_synthesis(
    primus_tgz_path: Path,
    tmp_folder: Path,
    problematic_xml_folder: Path
):
    """Goes through the primus dataset and tries synthesizing each incipit,
    logging those that fail and their corresponding exceptions"""
    
    problematic_xml_folder.mkdir(exist_ok=True, parents=True)

    # load the primus dataset as a sequence of incipits
    primus = Primus2018Enumerator(primus_tgz_path)
    xml_incipit_stream = prepare_xml_incipit_stream(
        primus_tgz_path=primus_tgz_path,
        tmp_folder=tmp_folder
    )

    model = TestModel()

    for incipit, xml in zip(tqdm.tqdm(primus), xml_incipit_stream):
        xml_path = problematic_xml_folder / (
            incipit.incipit_id.split("/")[2] + ".musicxml"
        )
        try:
            model(data=xml, format=".musicxml")
        except Exception as e:
            logging.exception(f"Incipit failed: {incipit.incipit_id}")

            with open(xml_path, "w") as f:
                f.write(xml)
            
            with open(xml_path.with_suffix(".log"), "w") as f:
                print(
                    '{}: {}'.format(type(e).__name__, e),
                    file=f
                )
                print(
                    "".join(traceback.format_exception(type(e), e, e.__traceback__)),
                    file=f
                )




# .venv/bin/python3 test_primus_synthesis.py
if __name__ == "__main__":
    converter21.register()
    data_folder = (Path(__file__).parent / ".." / "data").resolve()
    test_primus_synthesis(
        primus_tgz_path=data_folder / "primusCalvoRizoAppliedSciences2018.tgz",
        tmp_folder=data_folder / "tmp",
        problematic_xml_folder=data_folder / "primus_problematic"
    )

