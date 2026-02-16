from __future__ import annotations

from pathlib import Path
import numpy as np

from .model import Genome


def save_genome(path: Path, genome: Genome, generation: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(
        path,
        generation=generation,
        fitness=genome.fitness,
        w1=genome.w1,
        b1=genome.b1,
        w2=genome.w2,
        b2=genome.b2,
    )


def load_genome(path: Path) -> tuple[int, Genome]:
    data = np.load(path)
    genome = Genome(
        w1=data["w1"],
        b1=data["b1"],
        w2=data["w2"],
        b2=data["b2"],
        fitness=float(data["fitness"]),
    )
    return int(data["generation"]), genome
