import random
from dataclasses import dataclass
from typing import List, Tuple


@dataclass
class PageLayout:
    """Describes how many staves and measures are where on the page"""

    measures_per_staff: List[int]
    "One integer for each staff, representing the number of measures"

    @property
    def total_measures(self) -> int:
        """How many measures are needed for the page"""
        return sum(self.measures_per_staff)
    
    @staticmethod
    def sample(
        rng: random.Random,
        staves: Tuple[int, int],
        measures_per_staff: Tuple[int, int],
    ) -> "PageLayout":
        return PageLayout(
            measures_per_staff=[
                rng.randint(*measures_per_staff)
                for _ in range(rng.randint(*staves))
            ]
        )

    @staticmethod
    def sample_M_domain(rng: random.Random) -> "PageLayout":
        return PageLayout.sample(
            rng,
            staves=(3, 4),
            measures_per_staff=(3, 5),
        )

    @staticmethod
    def sample_C_domain(rng: random.Random) -> "PageLayout":
        raise NotImplementedError
