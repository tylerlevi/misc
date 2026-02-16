from pathlib import Path

import numpy as np

from kr_agent.checkpoint import load_genome, save_genome
from kr_agent.config import EvolutionConfig, VisionConfig, build_agent_config
from kr_agent.evolution import Evolver
from kr_agent.model import PolicyNetwork


def test_population_and_next_generation_shapes_and_decay():
    vision = VisionConfig(width=4, height=2, frame_stack=2)
    agent = build_agent_config(vision, output_size=3, action_repeat=2)
    evo = EvolutionConfig(
        population_size=10,
        elite_count=2,
        generations=2,
        episode_seconds=1,
        mutation_decay=0.9,
        min_mutation_std=0.05,
        immigrants_per_generation=2,
    )
    evolver = Evolver(agent, evo)

    pop = evolver.initial_population()
    assert len(pop) == 10
    assert pop[0].w1.shape == (vision.width * vision.height * vision.frame_stack, agent.hidden_size)

    for i, g in enumerate(pop):
        g.fitness = float(i)

    nxt = evolver.next_generation(pop)
    assert len(nxt) == 10
    assert 0.05 <= evolver.current_mutation_std <= agent.mutation_std


def test_policy_outputs_valid_action_index():
    vision = VisionConfig(width=3, height=2, frame_stack=1)
    agent = build_agent_config(vision, output_size=4, action_repeat=1)
    evo = EvolutionConfig(population_size=4, elite_count=1, generations=1, episode_seconds=1)
    evolver = Evolver(agent, evo)
    genome = evolver.initial_population()[0]

    policy = PolicyNetwork(genome)
    action = policy.act(np.zeros(agent.input_size))
    assert 0 <= action < 4


def test_checkpoint_roundtrip(tmp_path: Path):
    vision = VisionConfig(width=3, height=2, frame_stack=1)
    agent = build_agent_config(vision, output_size=2, action_repeat=1)
    evolver_genome = Evolver(
        agent,
        EvolutionConfig(population_size=2, elite_count=1, generations=1, episode_seconds=1),
    ).initial_population()[0]
    evolver_genome.fitness = 12.5

    out = tmp_path / "best.npz"
    save_genome(out, evolver_genome, generation=7)
    gen, loaded = load_genome(out)

    assert gen == 7
    assert loaded.fitness == 12.5
    assert loaded.w1.shape == evolver_genome.w1.shape
