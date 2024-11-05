from typing import Generator, Tuple
from pathlib import Path, PosixPath
import tarfile
from tqdm import tqdm


def enumerate_primus_mei(
    primus_tgz_path: Path
) -> Generator[Tuple[Path, str], None, None]:
    with tarfile.open(str(primus_tgz_path), "r:gz") as archive:
        for item in tqdm(archive):
            if not item.name.endswith(".mei"):
                continue

            item_path = PosixPath(item.name)

            # skip the MAC OS meta files starting with dot
            if item_path.name.startswith("."):
                continue

            # load MEI string and yield
            with archive.extractfile(item) as f:
                yield item_path, f.read().decode("utf-8")


# .venv/bin/python3 enumerate_primus_mei.py
if __name__ == "__main__":
    data_folder = (Path(__file__).parent / ".." / "data").resolve()
    for item_path, mei in enumerate_primus_mei(
        primus_tgz_path=data_folder / "primusCalvoRizoAppliedSciences2018.tgz",
    ):
        print(item_path)
        print("----------------")
        print(mei)
