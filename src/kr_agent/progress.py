from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TextIO


@dataclass(slots=True)
class ProgressMessage:
    generation: int
    best_fitness: float
    mean_fitness: float
    std_fitness: float
    epsilon: float
    temperature: float
    mutation_std: float
    novelty_archive: int
    note: str


class ProgressReporter:
    def __init__(self, path: Path | None) -> None:
        self.path = path
        self._handle: TextIO | None = None

    def __enter__(self) -> "ProgressReporter":
        if self.path is not None:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self._handle = self.path.open("a", encoding="utf-8")
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        if self._handle is not None:
            self._handle.close()
            self._handle = None

    def write(self, message: ProgressMessage) -> None:
        line = (
            f"gen={message.generation} best={message.best_fitness:.3f} mean={message.mean_fitness:.3f} "
            f"std={message.std_fitness:.3f} eps={message.epsilon:.3f} temp={message.temperature:.3f} "
            f"mut={message.mutation_std:.4f} archive={message.novelty_archive} note={message.note}\n"
        )
        if self._handle is not None:
            self._handle.write(line)
            self._handle.flush()
        print(line, end="")
