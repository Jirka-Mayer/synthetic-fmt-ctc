import csv
import itertools
import logging
import random
from pathlib import Path
from typing import Any, Callable, Iterable, Optional

import cv2
import smashcima as sc

from .ModelM import ModelM
from .primus.start_primus_musicxml_iterator import \
    start_primus_musicxml_iterator
from .semantic.PageContent import PageContent
from .semantic.PageLayout import PageLayout
from .semantic.pull_page_from_musicxml_iterator import \
    pull_page_from_musicxml_iterator


def build_synthetic_dataset(
    primus_tgz_path: Path,
    tmp_folder: Path,
    output_folder: Path
):
    rng = random.Random(42)
    
    # TODO: pass rng into the model
    M_model = ModelM()
    C_model = None # TODO: define C model

    # iterate over primus incipits in MusicXML form
    primus_musicxml_iterator = start_primus_musicxml_iterator(
        primus_tgz_path=primus_tgz_path,
        tmp_folder=tmp_folder,
        musescore_batch_size=10
    )

    # slice the stream to only selected incipits
    primus_musicxml_iterator = itertools.islice(
        primus_musicxml_iterator, 10
    )

    # open all the output CSV files (pages and staves for both domains)
    output_folder.mkdir(parents=True, exist_ok=True)
    with open(output_folder / "M_pages_all.csv", "w") as M_pages_csv_file, \
        open(output_folder / "M_staves_all.csv", "w") as M_staves_csv_file, \
        open(output_folder / "C_pages_all.csv", "w") as C_pages_csv_file, \
        open(output_folder / "C_staves_all.csv", "w") as C_staves_csv_file:
        M_pages_csv = csv.writer(M_pages_csv_file)
        M_staves_csv = csv.writer(M_staves_csv_file)
        C_pages_csv = csv.writer(C_pages_csv_file)
        C_staves_csv = csv.writer(C_staves_csv_file)

        # until incipits get exhausted
        while True:
            # dataset_domain = rng.choice(["C", "M"])
            dataset_domain = "M" # TODO: DEBUG: sample M only for now
            
            page_layout = (
                PageLayout.sample_M_domain(rng)
                if dataset_domain == "M"
                else PageLayout.sample_C_domain(rng)
            )

            page_content = pull_page_from_musicxml_iterator(
                primus_musicxml_iterator=primus_musicxml_iterator,
                page_layout=page_layout
            )

            if page_content is None:
                break

            use_M = (dataset_domain == "M")
            synthesize_page(
                dataset_domain=dataset_domain,
                page_content=page_content,
                output_folder=output_folder,
                pages_csv_writerow=(
                    M_pages_csv.writerow
                    if use_M else C_pages_csv.writerow
                ),
                staves_csv_writerow=(
                    M_staves_csv.writerow
                    if use_M else C_staves_csv.writerow
                ),
                model=(M_model if use_M else C_model),
            )


def synthesize_page(
    dataset_domain: str,
    page_content: PageContent,
    output_folder: Path,
    pages_csv_writerow: Callable[[Iterable[Any]], None],
    staves_csv_writerow: Callable[[Iterable[Any]], None],
    model: sc.orchestration.BaseHandwrittenModel
):
    print("Synthesizing page", page_content.identifier)

    page_kern_path = file_path(
        output_folder=output_folder,
        dataset_domain=dataset_domain,
        page_identifier=page_content.identifier,
        staff_index=None,
        format="krn",
    )
    page_jpg_path = file_path(
        output_folder=output_folder,
        dataset_domain=dataset_domain,
        page_identifier=page_content.identifier,
        staff_index=None,
        format="jpg",
    )

    # create folders
    page_kern_path.parent.mkdir(parents=True, exist_ok=True)
    page_jpg_path.parent.mkdir(parents=True, exist_ok=True)

    # synthesis
    try:
        scene = model(
            score=page_content.smashcima_score,
            clone_score=False
        )
        assert len(scene.pages) == 1, "Expected only one page"
        img = scene.render(scene.pages[0])
        cv2.imwrite(str(page_jpg_path), img)
    except:
        logging.exception("Synthesis crash:")
        return

    # store the kern output for the file
    with open(page_kern_path, "w") as f:
        f.write(page_content.kern)
    
    # write CSV page record
    pages_csv_writerow([
        str(page_jpg_path.relative_to(output_folder)),
        str(page_kern_path.relative_to(output_folder))
    ])

    # TODO: process staves here somehow
    # get measure indices for each synthesized staff
    # part_measures = scene.score.parts[0].measures
    # for i, staff in enumerate(scene.pages[0].staves):
    #     print("STAFF:", i)
    #     for sm in sc.scene.StaffMeasure.many_of_staff_visual(staff):
    #         measure_index = part_measures.index(sm.measure)
    #         print("MI:", measure_index)


def file_path(
    output_folder: Path,
    dataset_domain: str,
    page_identifier: str,
    staff_index: Optional[int],
    format: str,
) -> Path:
    bucket_count = 10
    id_hash = str(hash(page_identifier) % bucket_count).zfill(2)
    
    page_or_staff = "page" if staff_index is None else "staff"
    
    staff_number = ""
    if staff_index is not None:
        staff_number = "_s" + str(staff_number)

    return (
        output_folder / dataset_domain / page_or_staff /
        id_hash / (page_identifier + staff_number + "." + format)
    )


# .venv/bin/python3 -m app.build_synthetic_dataset
if __name__ == "__main__":
    from .config import FMT_SYNTHETIC, PRIMUS_TGZ_PATH, TMP_FOLDER
    build_synthetic_dataset(
        primus_tgz_path=PRIMUS_TGZ_PATH,
        tmp_folder=TMP_FOLDER,
        output_folder=FMT_SYNTHETIC
    )
