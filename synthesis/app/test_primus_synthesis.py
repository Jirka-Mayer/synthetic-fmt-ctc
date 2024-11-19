from pathlib import Path
from .primus.Primus2018Iterable import Primus2018Iterable
from .primus.start_primus_musicxml_iterator import \
    start_primus_musicxml_iterator
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
    primus = Primus2018Iterable(primus_tgz_path)
    primus_musicxml_iterator = start_primus_musicxml_iterator(
        primus_tgz_path=primus_tgz_path,
        tmp_folder=tmp_folder,
        musescore_batch_size=10
    )

    model = TestModel()

    for incipit in tqdm.tqdm(
        primus_musicxml_iterator,
        total=len(primus)
    ):
        incipit_id = incipit.original_incipit.incipit_id
        
        xml_path = problematic_xml_folder / (
            incipit_id.split("/")[2] + ".musicxml"
        )
        try:
            model(data=incipit.musicxml, format=".musicxml")
        except Exception as e:
            logging.exception(f"Incipit failed: {incipit_id}")

            with open(xml_path, "w") as f:
                f.write(incipit.musicxml)
            
            with open(xml_path.with_suffix(".log"), "w") as f:
                print(
                    '{}: {}'.format(type(e).__name__, e),
                    file=f
                )
                print(
                    "".join(traceback.format_exception(type(e), e, e.__traceback__)),
                    file=f
                )




# .venv/bin/python3 -m app.test_primus_synthesis
if __name__ == "__main__":
    from .config import DATA_FOLDER, PRIMUS_TGZ_PATH, TMP_FOLDER
    test_primus_synthesis(
        primus_tgz_path=PRIMUS_TGZ_PATH,
        tmp_folder=TMP_FOLDER,
        problematic_xml_folder=DATA_FOLDER / "primus_problematic"
    )

