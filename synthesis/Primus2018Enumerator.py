from typing import Generator, Dict
from pathlib import Path
import tarfile
from dataclasses import dataclass


# NOTE: to list all files inside the PrIMuS dataset run:
# tar -tvf primusCalvoRizoAppliedSciences2018.tgz


SKIP_INCIPITS_CONTAINING = set([
    # super-whole notes and rests cannot be synthesized at all,
    # they break the measure structure
    "rest.quadruple_whole-L3",
    "note.quadruple_whole-",
    "note.double_whole-",

    # 32nd (and less) notes and rests cannot be synthesized
    # with only MUSCIMA++ glyphs
    "rest.thirty_second-L3",
    "note.thirty_second-",
    "rest.sixty_fourth-L3",
])

PROBLEMATIC_INCIPITS_CONTAINING = set([
    # gracenotes are not synthesized,
    # they should be removed after loading MEI
    "gracenote.",

    # multimeasure rests are not supported by the synthesizer,
    # they should be replaced by 1-measure rests after loading the MEI
    "multirest-L3",
    # "digit.", # digits indicate measure count, but also time signature

    # Fermatas are not synthesized, but there's just a few of them
    "fermata.above-S6",

    # Slurs and ties are not synthesized yet
    "slur.",
])


@dataclass
class Incipit:
    incipit_id: str = None
    mei: str = None
    agnostic: str = None

    def _is_complete(self) -> bool:
        return self.mei is not None and self.agnostic is not None
    
    def _is_empty(self) -> bool:
        return self.mei is None and self.agnostic is None
    
    def _should_be_skipped(self) -> bool:
        for forbidden_pattern in SKIP_INCIPITS_CONTAINING:
            if forbidden_pattern in self.agnostic:
                return True
        return False
    
    @staticmethod
    def name_to_incipit_id(name: str) -> str:
        """Converts primus filename to incipit ID"""
        return "/".join(name.split("/")[:3])
    
    def get_filename(self, format: str) -> str:
        i = self.incipit_id.split("/")[2]
        return f"{self.incipit_id}/{i}.{format}"
    
    def measure_count(self) -> int:
        return self.agnostic.count("barline-L1") + 1
    

class Primus2018Enumerator:
    """Provides access to the PrIMuS 2018 dataset as a list of
    Incipit instance."""

    def __init__(self, primus_tgz_path: Path):
        self.primus_tgz_path = primus_tgz_path

    def __len__(self) -> int:
        # return 87678 # the complete PrIMuS dataset
        return 84381 # without unsynthetisable note durations
    
        # other numbers:
        # return 67119 # without multi-measure rests only
        # return 74638 # without grace notes only

    def __iter__(self) -> Generator[Incipit, None, None]:
        # incipit_id to incipit instance
        buffer: Dict[str, Incipit] = {}

        with tarfile.open(str(self.primus_tgz_path), "r:gz") as archive:
            for item in archive:
                incipit_id = Incipit.name_to_incipit_id(item.name)

                if incipit_id not in buffer:
                    buffer[incipit_id] = Incipit(incipit_id=incipit_id)

                incipit = buffer[incipit_id]

                for format in ["agnostic", "mei"]:
                    if item.name != incipit.get_filename(format):
                        continue
                    with archive.extractfile(item) as f:
                        data = f.read().decode("utf-8")
                        setattr(incipit, format, data)
                
                if incipit._is_complete():
                    del buffer[incipit_id]
                    if not incipit._should_be_skipped():
                        yield incipit
                
                if incipit._is_empty():
                    del buffer[incipit_id]


# .venv/bin/python3 Primus2018Enumerator.py
if __name__ == "__main__":
    from collections import Counter
    from tqdm import tqdm

    data_folder = (Path(__file__).parent / ".." / "data").resolve()
    primus = Primus2018Enumerator(
        primus_tgz_path=data_folder / "primusCalvoRizoAppliedSciences2018.tgz",
    )
    
    vocabulary: Counter = Counter()
    measure_counts = Counter()
    total_incipits = 0

    for incipit in tqdm(primus):
        for token in incipit.agnostic.split():
            vocabulary.update({
                token: 1
            })

        measure_count = incipit.measure_count()
        measure_counts.update({
            measure_count: 1
        })

        total_incipits += 1

    print("Vocabulary")
    print("----------")
    for value, count in vocabulary.most_common():
        print(str(value).ljust(25), count)

    print()
    print("Measure counts")
    print("--------------")
    total_measures = 0
    for value, count in measure_counts.most_common():
        print(str(value) + ":", str(count) + "x")
        total_measures += value * count

    print()
    print("Total measures:", total_measures)
    print("Total incipits:", total_incipits)
