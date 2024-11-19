import csv
import hashlib
import itertools
import logging
import random
import traceback
from pathlib import Path
from typing import Any, Callable, Iterable, List, Optional

import cv2
import numpy as np
import smashcima as sc

from .kern.slice_kern_measures import slice_kern_measures
from .synthesis.ModelC import ModelC
from .synthesis.ModelM import ModelM
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
    
    M_model = ModelM(rng)
    C_model = ModelC(rng)

    # iterate over primus incipits in MusicXML form
    primus_musicxml_iterator = start_primus_musicxml_iterator(
        primus_tgz_path=primus_tgz_path,
        tmp_folder=tmp_folder,
        musescore_batch_size=100,
        with_tqdm=True
    )

    # slice the stream to only selected incipits
    # primus_musicxml_iterator = itertools.islice(
    #     primus_musicxml_iterator, 10
    # )

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
            dataset_domain = rng.choice(["C", "M"])
            
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
                rng=rng
            )


def synthesize_page(
    dataset_domain: str,
    page_content: PageContent,
    output_folder: Path,
    pages_csv_writerow: Callable[[Iterable[Any]], None],
    staves_csv_writerow: Callable[[Iterable[Any]], None],
    model: sc.orchestration.BaseHandwrittenModel,
    rng: random.Random
):
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
    crashed_musicxml_path = (
        output_folder / "crashed_musicxml" / (
            page_content.identifier + ".musicxml"
        )
    )

    # create folders
    page_kern_path.parent.mkdir(parents=True, exist_ok=True)
    page_jpg_path.parent.mkdir(parents=True, exist_ok=True)
    crashed_musicxml_path.parent.mkdir(parents=True, exist_ok=True)

    # synthesis
    try:
        scene = model(
            score=page_content.smashcima_score,
            clone_score=False
        )
        assert len(scene.pages) == 1, "Expected only one page"
        scene_page = scene.pages[0]
        page_bitmap = scene.render(scene_page)

    # handle synthesis crash
    except Exception as e:
        logging.exception("Synthesis crash:")
        with open(crashed_musicxml_path, "w") as f:
            f.write(page_content.musicxml)
        with open(crashed_musicxml_path.with_suffix(".log"), "w") as f:
            print('{}: {}'.format(type(e).__name__, e), file=f)
            print("".join(traceback.format_exception(
                type(e), e, e.__traceback__
            )), file=f)
        return

    # store the bitmap for the file
    cv2.imwrite(str(page_jpg_path), page_bitmap)

    # store the kern output for the file
    with open(page_kern_path, "w") as f:
        f.write(page_content.kern)
    
    # write CSV page record
    pages_csv_writerow([
        str(page_jpg_path.relative_to(output_folder)),
        str(page_kern_path.relative_to(output_folder))
    ])

    for staff_index, staff in enumerate(scene_page.staves):
        extract_staff_sample(
            staff=staff,
            staff_index=staff_index,
            page_bitmap=page_bitmap,
            page_content=page_content,
            scene_page=scene_page,
            part_measures=scene.score.parts[0].measures,
            output_folder=output_folder,
            dataset_domain=dataset_domain,
            staves_csv_writerow=staves_csv_writerow,
            rng=rng
        )


def extract_staff_sample(
    staff: sc.StaffVisual,
    staff_index: int,
    page_bitmap: np.ndarray,
    page_content: PageContent,
    scene_page: sc.Page,
    part_measures: List[sc.Measure],
    output_folder: Path,
    dataset_domain: str,
    staves_csv_writerow: Callable[[Iterable[Any]], None],
    rng: random.Random
):
    # extract measure range
    measure_indices = list(sorted(
        part_measures.index(staff_measure.measure)
        for staff_measure
        in sc.StaffMeasure.many_of_staff_visual(staff)
    ))

    if len(measure_indices) == 0:
        return # no measures on this staff, ignore it

    start_measure_index = min(measure_indices)
    end_measure_index = max(measure_indices)
    assert list(range(start_measure_index, end_measure_index + 1)) \
        == measure_indices, "Measure indicies are not continous"
    
    # compute the bitmap crop box
    staff_bbox = staff.glyph.region.get_bbox_in_space(scene_page.space)
    dilate_by = staff.staff_height * rng.uniform(0.6, 1.0)
    dilated_box = staff_bbox.dilate(dilate_by)
    dilated_box.y += staff.staff_height * rng.uniform(-0.5, 0.1)
    pixels_box = dilated_box \
        .relativize_to(scene_page.view_box.rectangle) \
        .intersect_with(sc.Rectangle(0, 0, 1, 1)) \
        .absolutize_to(
            sc.Rectangle(0, 0, page_bitmap.shape[1], page_bitmap.shape[0])
        ) \
        .snap_shrink()
    
    # crop out data
    staff_bitmap = page_bitmap[
        int(pixels_box.top):int(pixels_box.bottom),
        int(pixels_box.left):int(pixels_box.right),
        :
    ]
    staff_kern = slice_kern_measures(
        kern=page_content.kern,
        start_measure_index=start_measure_index,
        end_measure_index=end_measure_index
    )

    # write to filesystem
    staff_kern_path = file_path(
        output_folder=output_folder,
        dataset_domain=dataset_domain,
        page_identifier=page_content.identifier,
        staff_index=staff_index,
        format="krn",
    )
    staff_jpg_path = file_path(
        output_folder=output_folder,
        dataset_domain=dataset_domain,
        page_identifier=page_content.identifier,
        staff_index=staff_index,
        format="jpg",
    )

    staff_kern_path.parent.mkdir(exist_ok=True, parents=True)
    staff_jpg_path.parent.mkdir(exist_ok=True, parents=True)

    cv2.imwrite(str(staff_jpg_path), staff_bitmap)

    with open(staff_kern_path, "w") as f:
        f.write(staff_kern)

    # write to CSV
    staves_csv_writerow([
        str(staff_jpg_path.relative_to(output_folder)),
        str(staff_kern_path.relative_to(output_folder))
    ])


def file_path(
    output_folder: Path,
    dataset_domain: str,
    page_identifier: str,
    staff_index: Optional[int],
    format: str,
) -> Path:
    bucket_count = 10
    identifier_hash_sum = sum(
        hashlib.md5(page_identifier.encode("utf-8")).digest()
    )
    id_hash = str(identifier_hash_sum % bucket_count).zfill(2)
    
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
