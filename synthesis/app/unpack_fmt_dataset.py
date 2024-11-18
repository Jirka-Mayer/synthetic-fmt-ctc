from smashcima.assets.download_file import download_file
from pathlib import Path
import tarfile
import json
import cv2


def unpack_fmt_dataset(fmt_tgz_path: Path, fmt_folder: Path):
    """Goes through the fmt.tgz file and downloads the referenced images"""

    fmt_folder.mkdir(exist_ok=True)

    path_prefix = "./7851215372389577652707782/files/4/"
    path_suffix = ".jpg.json"
    
    # go through all items in the tar archive
    with tarfile.open(str(fmt_tgz_path), "r:gz") as archive:
        for item in archive:
            
            # skip non-important files
            if not item.name.startswith(path_prefix):
                continue

            # skip folders
            if not item.isfile():
                continue

            # skip files that are not JSON files
            if not item.name.endswith(path_suffix):
                continue

            # process all pages
            with archive.extractfile(item) as f:
                json_metadata = json.load(f)
                unpack_page(json_metadata, fmt_folder)


def get_partition(metadata: dict) -> str:
    """Returns 'C' or 'M' based on the FMT dataset partition name."""
    if "C" in metadata["filename"]:
        return "C"
    
    if "M" in metadata["filename"]:
        return "M"
    
    raise Exception("Cannot resolve partition name: " + metadata["filename"])


def unpack_page(metadata: dict, fmt_folder: Path):
    collection = metadata["collection"]
    page_id = metadata["id"]
    filename = metadata["filename"]
    url = metadata["url"]
    partition = get_partition(metadata)

    file_base_name = f"{collection}__{page_id}__{filename}"
    base_folder = fmt_folder / partition / "pages"
    output_json_path = base_folder / "json" / f"{file_base_name}.json"
    output_jpg_path = base_folder / "jpg" / file_base_name

    # skip if exists
    print(f"Processing {file_base_name} ...")
    if output_json_path.is_file():
        print(f"  Skipping since already done.")
        return

    # Download the image file
    output_jpg_path.parent.mkdir(exist_ok=True, parents=True)
    download_file(
        url=url,
        path=output_jpg_path
    )

    # Split up into staves
    extract_staves(
        metadata=metadata,
        fmt_folder=fmt_folder,
        jpg_path=output_jpg_path
    )

    # Write pretty-printed JSON
    output_json_path.parent.mkdir(exist_ok=True, parents=True)
    with open(output_json_path, "w") as f:
        json.dump(metadata, f, indent=2)


def extract_staves(metadata: dict, fmt_folder: Path, jpg_path: Path):
    collection = metadata["collection"]
    page_id = str(metadata["id"])
    partition = get_partition(metadata)
    base_folder = fmt_folder / partition / "staves"

    page_img = cv2.imread(str(jpg_path), cv2.IMREAD_ANYCOLOR)
    
    assert len(metadata["pages"]) == 1
    page_metadata = metadata["pages"][0]

    for region in page_metadata["regions"]:
        if region["type"] != "staff":
            continue

        # remove symbols from warning prints
        region = region.copy()
        if "symbols" in region:
            del region["symbols"]

        staff_id = str(region["id"])

        if "semantic_encoding" not in region:
            print(f"  Skipping region {staff_id}, missing semantic encoding:")
            print(region)
            continue
        
        skern = region["semantic_encoding"]
        bbox = region["bounding_box"]
        staff_img = page_img[
            bbox["fromY"]:bbox["toY"],
            bbox["fromX"]:bbox["toX"],
            :
        ]

        file_base_name = f"{collection}__{page_id}__{staff_id}"
        output_jpg_path = base_folder / "jpg" / (file_base_name + ".jpg")
        output_krn_path = base_folder / "krn" / (file_base_name + ".krn")
        
        # write kern
        output_krn_path.parent.mkdir(exist_ok=True, parents=True)
        with open(output_krn_path, "w") as f:
            f.write(skern)
        
        # write jpg
        output_jpg_path.parent.mkdir(exist_ok=True, parents=True)
        cv2.imwrite(str(output_jpg_path), staff_img)


# .venv/bin/python3 unpack_fmt_dataset.py
if __name__ == "__main__":
    data_folder = (Path(__file__).parent / ".." / "data").resolve()
    unpack_fmt_dataset(
        fmt_tgz_path=data_folder / "fmt.tgz",
        fmt_folder=data_folder / "FMT"
    )
