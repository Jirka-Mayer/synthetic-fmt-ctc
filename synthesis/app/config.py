from pathlib import Path


DATA_FOLDER = (Path(__file__).parent / ".." / ".." / "data").resolve()

PRIMUS_TGZ_PATH = DATA_FOLDER / "primusCalvoRizoAppliedSciences2018.tgz"

TMP_FOLDER = DATA_FOLDER / "tmp"

FMT_SYNTHETIC = DATA_FOLDER / "FMT-synthetic"

MSCORE_COMMAND = str((
    DATA_FOLDER / "musescore.AppImage"
).resolve())
