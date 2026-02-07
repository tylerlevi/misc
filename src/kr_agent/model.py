from __future__ import annotations

from dataclasses import dataclass
import numpy as np


@dataclass(slots=True)
class Genome:
    w1: np.ndarray
    b1: np.ndarray
    w2: np.ndarray
    b2: np.ndarray
    fitness: float = 0.0

    @classmethod
    def random(cls, input_size: int, hidden_size: int, output_size: int, rng: np.random.Generator) -> "Genome":
        xavier_1 = np.sqrt(2.0 / (input_size + hidden_size))
        xavier_2 = np.sqrt(2.0 / (hidden_size + output_size))
        return cls(
            w1=rng.standard_normal((input_size, hidden_size)) * xavier_1,
            b1=np.zeros(hidden_size, dtype=np.float32),
            w2=rng.standard_normal((hidden_size, output_size)) * xavier_2,
            b2=np.zeros(output_size, dtype=np.float32),
        )

    def clone(self) -> "Genome":
        return Genome(self.w1.copy(), self.b1.copy(), self.w2.copy(), self.b2.copy(), self.fitness)


class PolicyNetwork:
    def __init__(self, genome: Genome, rng: np.random.Generator | None = None) -> None:
        self.genome = genome
        self.rng = rng if rng is not None else np.random.default_rng()

    def logits(self, state: np.ndarray) -> np.ndarray:
        hidden = np.tanh(state @ self.genome.w1 + self.genome.b1)
        return hidden @ self.genome.w2 + self.genome.b2

    def act(self, state: np.ndarray) -> int:
        return int(np.argmax(self.logits(state)))

    def act_explore(self, state: np.ndarray, epsilon: float, temperature: float) -> int:
        if self.rng.random() < epsilon:
            return int(self.rng.integers(0, self.genome.b2.shape[0]))
        logits = self.logits(state)
        probs = self._softmax(logits / max(temperature, 1e-5))
        return int(self.rng.choice(len(probs), p=probs))

    @staticmethod
    def _softmax(x: np.ndarray) -> np.ndarray:
        shifted = x - np.max(x)
        exp = np.exp(shifted)
        return exp / np.sum(exp)
