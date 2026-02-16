from __future__ import annotations

import numpy as np

from .config import AgentConfig, EvolutionConfig
from .model import Genome


class Evolver:
    def __init__(self, agent_cfg: AgentConfig, evo_cfg: EvolutionConfig) -> None:
        self.agent_cfg = agent_cfg
        self.evo_cfg = evo_cfg
        self.rng = np.random.default_rng(evo_cfg.random_seed)
        self.current_mutation_std = agent_cfg.mutation_std

    def initial_population(self) -> list[Genome]:
        population_size = max(1, self.evo_cfg.population_size)
        return [self._random_genome() for _ in range(population_size)]

    def next_generation(self, population: list[Genome]) -> list[Genome]:
        population_size = max(1, self.evo_cfg.population_size)
        elite_count = min(self.evo_cfg.elite_count, population_size)
        immigrants = min(self.evo_cfg.immigrants_per_generation, population_size - elite_count)

        ranked = sorted(population, key=lambda g: g.fitness, reverse=True)
        elite = [g.clone() for g in ranked[:elite_count]]

        self.current_mutation_std = max(
            self.evo_cfg.min_mutation_std,
            self.current_mutation_std * self.evo_cfg.mutation_decay,
        )

        children: list[Genome] = elite.copy()
        target_children = population_size - immigrants

        while len(children) < target_children:
            p1, p2 = self._select_pair(ranked)
            child = self._crossover(p1, p2)
            self._mutate(child)
            children.append(child)

        for _ in range(immigrants):
            children.append(self._random_genome())

        return children[:population_size]

    def _random_genome(self) -> Genome:
        return Genome.random(self.agent_cfg.input_size, self.agent_cfg.hidden_size, self.agent_cfg.output_size, self.rng)

    def _tournament_pick(self, ranked: list[Genome]) -> Genome:
        k = min(self.evo_cfg.tournament_size, len(ranked))
        idx = self.rng.choice(len(ranked), size=k, replace=False)
        contestants = [ranked[int(i)] for i in idx]
        return max(contestants, key=lambda g: g.fitness)

    def _select_pair(self, ranked: list[Genome]) -> tuple[Genome, Genome]:
        return self._tournament_pick(ranked), self._tournament_pick(ranked)

    def _crossover(self, a: Genome, b: Genome) -> Genome:
        def choose(x: np.ndarray, y: np.ndarray) -> np.ndarray:
            mask = self.rng.random(x.shape) < self.agent_cfg.crossover_rate
            return np.where(mask, x, y)

        return Genome(
            w1=choose(a.w1, b.w1),
            b1=choose(a.b1, b.b1),
            w2=choose(a.w2, b.w2),
            b2=choose(a.b2, b.b2),
        )

    def _mutate(self, g: Genome) -> None:
        for arr in (g.w1, g.b1, g.w2, g.b2):
            noise = self.rng.standard_normal(arr.shape) * self.current_mutation_std
            arr += noise
