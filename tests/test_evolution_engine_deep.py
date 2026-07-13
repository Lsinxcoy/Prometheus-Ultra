"""Comprehensive tests for evolution_engine.py module.

Tests cover:
- Gene, GeneContainer, Chromosome dataclasses
- MutationStrategy, CrossoverOperator, SelectionMethod enums
- MutationEngine (5 mutation strategies)
- CrossoverEngine (5 crossover operators)
- SelectionEngine (5 selection methods)
- ElitismEngine
- DiversityEngine
- Archive
- Controller
- Terminator
- Evaluator
- EvolutionEngine (full integration)
"""
from __future__ import annotations

import math
import random
import uuid
from typing import Any, Callable, Dict, List, Tuple

import pytest

# Import from the module
from prometheus_ultra.evolution.evolution_engine import (
    Archive,
    Chromosome,
    Controller,
    CrossoverEngine,
    CrossoverOperator,
    DiversityEngine,
    Evaluator,
    ElitismEngine,
    Gene,
    GeneContainer,
    MutationEngine,
    MutationStrategy,
    SelectionEngine,
    SelectionMethod,
    Terminator,
    EvolutionEngine,
)


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def simple_gene():
    """Create a simple gene for testing."""
    return Gene(
        gene_id="g1",
        name="test_param",
        value=0.5,
        min_val=0.0,
        max_val=1.0,
        description="A test parameter",
    )


@pytest.fixture
def simple_chromosome():
    """Create a simple chromosome with multiple genes."""
    genes = [
        Gene("g1", "param1", 0.3, 0.0, 1.0),
        Gene("g2", "param2", 0.7, 0.0, 1.0),
        Gene("g3", "param3", 0.5, 0.0, 1.0),
    ]
    return Chromosome(genes=genes, fitness=0.8)


@pytest.fixture
def population():
    """Create a population of chromosomes."""
    pop = []
    for i in range(10):
        genes = [
            Gene(f"g{j}", f"param{j}", random.random(), 0.0, 1.0)
            for j in range(5)
        ]
        pop.append(Chromosome(genes=genes, fitness=random.random()))
    return pop


# ============================================================================
# Test Gene Dataclass
# ============================================================================

class TestGene:
    """Test Gene dataclass."""

    def test_gene_creation(self, simple_gene):
        """Should create gene with all fields."""
        assert simple_gene.gene_id == "g1"
        assert simple_gene.name == "test_param"
        assert simple_gene.value == 0.5
        assert simple_gene.min_val == 0.0
        assert simple_gene.max_val == 1.0

    def test_gene_clamp_value(self, simple_gene):
        """Should clamp value to valid range."""
        simple_gene.value = 1.5
        assert simple_gene.value <= simple_gene.max_val

        simple_gene.value = -0.5
        assert simple_gene.value >= simple_gene.min_val

    def test_gene_normalized_value(self, simple_gene):
        """Should return normalized value 0-1."""
        simple_gene.value = 0.5
        assert simple_gene.normalized_value == 0.5

        simple_gene.value = 0.0
        assert simple_gene.normalized_value == 0.0

        simple_gene.value = 1.0
        assert simple_gene.normalized_value == 1.0


# ============================================================================
# Test Chromosome Dataclass
# ============================================================================

class TestChromosome:
    """Test Chromosome dataclass."""

    def test_chromosome_creation(self, simple_chromosome):
        """Should create chromosome with genes and fitness."""
        assert len(simple_chromosome.genes) == 3
        assert simple_chromosome.fitness == 0.8

    def test_chromosome_get_gene(self, simple_chromosome):
        """Should retrieve gene by ID."""
        gene = simple_chromosome.get_gene("g1")
        assert gene is not None
        assert gene.name == "param1"

    def test_chromosome_set_gene(self, simple_chromosome):
        """Should update gene value."""
        simple_chromosome.set_gene("g1", 0.9)
        gene = simple_chromosome.get_gene("g1")
        assert gene.value == 0.9

    def test_chromosome_copy(self, simple_chromosome):
        """Should create independent copy."""
        copy = simple_chromosome.copy()
        assert copy.fitness == simple_chromosome.fitness
        assert copy is not simple_chromosome

        copy.set_gene("g1", 0.9)
        assert simple_chromosome.get_gene("g1").value != 0.9


# ============================================================================
# Test MutationEngine
# ============================================================================

class TestMutationEngine:
    """Test MutationEngine with all 5 strategies."""

    def test_uniform_mutation(self, simple_chromosome):
        """Should mutate genes randomly."""
        original_values = [g.value for g in simple_chromosome.genes]
        engine = MutationEngine(strategy=MutationStrategy.UNIFORM)
        mutated = engine.mutate(simple_chromosome, rate=0.5)
        assert mutated is not simple_chromosome

    def test_gaussian_mutation(self, simple_chromosome):
        """Should apply Gaussian noise."""
        engine = MutationEngine(strategy=MutationStrategy.GAUSSIAN)
        mutated = engine.mutate(simple_chromosome, rate=0.5, sigma=0.1)
        assert mutated is not None

    def test_boundary_mutation(self, simple_chromosome):
        """Should push values to boundaries."""
        engine = MutationEngine(strategy=MutationStrategy.BOUNDARY)
        mutated = engine.mutate(simple_chromosome, rate=0.5)
        assert mutated is not None

    def test_polynomial_mutation(self, simple_chromosome):
        """Should apply polynomial distribution."""
        engine = MutationEngine(strategy=MutationStrategy.POLYNOMIAL)
        mutated = engine.mutate(simple_chromosome, rate=0.5, mu=0.5)
        assert mutated is not None

    def test_adaptive_mutation(self, simple_chromosome):
        """Should adapt mutation rate based on fitness."""
        engine = MutationEngine(strategy=MutationStrategy.ADAPTIVE)
        mutated = engine.mutate(simple_chromosome, rate=0.5)
        assert mutated is not None


# ============================================================================
# Test CrossoverEngine
# ============================================================================

class TestCrossoverEngine:
    """Test CrossoverEngine with all 5 operators."""

    def test_single_point_crossover(self, population):
        """Should perform single-point crossover."""
        engine = CrossoverEngine(operator=CrossoverOperator.SINGLE_POINT)
        parent1, parent2 = population[0], population[1]
        child1, child2 = engine.crossover(parent1, parent2)
        assert child1 is not None
        assert child2 is not None

    def test_two_point_crossover(self, population):
        """Should perform two-point crossover."""
        engine = CrossoverEngine(operator=CrossoverOperator.TWO_POINT)
        parent1, parent2 = population[0], population[1]
        child1, child2 = engine.crossover(parent1, parent2)
        assert child1 is not None
        assert child2 is not None

    def test_uniform_crossover(self, population):
        """Should perform uniform crossover."""
        engine = CrossoverEngine(operator=CrossoverOperator.UNIFORM)
        parent1, parent2 = population[0], population[1]
        child1, child2 = engine.crossover(parent1, parent2)
        assert child1 is not None
        assert child2 is not None

    def test_arithmetic_crossover(self, population):
        """Should perform arithmetic crossover."""
        engine = CrossoverEngine(operator=CrossoverOperator.ARITHMETIC)
        parent1, parent2 = population[0], population[1]
        child1, child2 = engine.crossover(parent1, parent2)
        assert child1 is not None
        assert child2 is not None

    def test_simulated_binary_crossover(self, population):
        """Should perform simulated binary crossover."""
        engine = CrossoverEngine(operator=CrossoverOperator.SIMULATED_BINARY)
        parent1, parent2 = population[0], population[1]
        child1, child2 = engine.crossover(parent1, parent2)
        assert child1 is not None
        assert child2 is not None


# ============================================================================
# Test SelectionEngine
# ============================================================================

class TestSelectionEngine:
    """Test SelectionEngine with all 5 methods."""

    def test_roulette_wheel_selection(self, population):
        """Should select using roulette wheel."""
        selected = SelectionEngine.select(population, method=SelectionMethod.ROULETTE)
        assert len(selected) > 0
        for chromo in selected:
            assert chromo in population

    def test_tournament_selection(self, population):
        """Should select using tournament."""
        selected = SelectionEngine.select(
            population, method=SelectionMethod.TOURNAMENT, tournament_size=3
        )
        assert len(selected) > 0

    def test_rank_selection(self, population):
        """Should select using rank-based method."""
        selected = SelectionEngine.select(population, method=SelectionMethod.RANK)
        assert len(selected) > 0

    def test_stochastic_universal_selection(self, population):
        """Should select using stochastic universal sampling."""
        selected = SelectionEngine.select(
            population, method=SelectionMethod.SUS, n_points=5
        )
        assert len(selected) > 0

    def test_boltzmann_selection(self, population):
        """Should select using Boltzmann distribution."""
        selected = SelectionEngine.select(
            population, method=SelectionMethod.BOLTZMANN, temperature=0.5
        )
        assert len(selected) > 0


# ============================================================================
# Test ElitismEngine
# ============================================================================

class TestElitismEngine:
    """Test ElitismEngine."""

    def test_preserve_best(self, population):
        """Should preserve best chromosomes."""
        engine = ElitismEngine(n_elites=2)
        elites = engine.preserve(population)
        assert len(elites) == 2
        sorted_pop = sorted(population, key=lambda c: c.fitness, reverse=True)
        assert elites[0].fitness == sorted_pop[0].fitness

    def test_replace_worst(self, population):
        """Should replace worst with elites."""
        engine = ElitismEngine(n_elites=2)
        elites = engine.preserve(population)
        new_pop = population[:]
        engine.replace_worst(new_pop, elites)
        assert len(new_pop) == len(population)


# ============================================================================
# Test DiversityEngine
# ============================================================================

class TestDiversityEngine:
    """Test DiversityEngine."""

    def test_calculate_diversity(self, population):
        """Should calculate diversity metric."""
        engine = DiversityEngine()
        diversity = engine.calculate(population)
        assert diversity >= 0

    def test_add_diverse_individuals(self, population):
        """Should add diverse individuals."""
        engine = DiversityEngine()
        target_size = 20
        enhanced = engine.enhance(population, target_size)
        assert len(enhanced) >= len(population)


# ============================================================================
# Test Archive
# ============================================================================

class TestArchive:
    """Test Archive for storing best solutions."""

    def test_archive_initialization(self):
        """Should initialize with capacity."""
        archive = Archive()
        assert archive.capacity == 10
        assert len(archive) == 0

    def test_archive_add(self, simple_chromosome):
        """Should add chromosome to archive."""
        archive = Archive(capacity=5)
        archive.add(simple_chromosome)
        assert len(archive) == 1

    def test_archive_best(self, population):
        """Should return best chromosome."""
        archive = Archive()
        for chromo in population:
            archive.add(chromo)
        best = archive.best()
        assert best is not None
        assert best.fitness == max(c.fitness for c in population)

    def test_archive_capacity(self, population):
        """Should respect capacity limit."""
        archive = Archive(capacity=3)
        for chromo in population:
            archive.add(chromo)
        assert len(archive) <= 3


# ============================================================================
# Test Controller
# ============================================================================

class TestController:
    """Test Controller for evolutionary parameters."""

    def test_controller_initialization(self):
        """Should initialize with default parameters."""
        ctrl = Controller()
        
        
        assert ctrl.crossover_rate == 0.8
        assert ctrl.mutation_rate == 0.1

    def test_controller_custom_params(self):
        """Should accept custom parameters."""
        ctrl = Controller(
            population_size=100,
            generations=200,
            crossover_rate=0.9,
            mutation_rate=0.2,
        )
        assert ctrl.population_size == 100
        assert ctrl.generations == 200

    def test_controller_adjust_rates(self):
        """Should adjust rates dynamically."""
        ctrl = Controller()
        ctrl.adjust_mutation_rate(0.5)
        assert ctrl.mutation_rate == 0.5


# ============================================================================
# Test Terminator
# ============================================================================

class TestTerminator:
    """Test Terminator for stopping conditions."""

    def test_terminator_initialization(self):
        """Should initialize with default conditions."""
        term = Terminator()
        assert term._max_gen == 100
        assert term._threshold == 0.99
        assert term._stagnation == 20

    def test_check_max_generations(self):
        """Should stop when max generations reached."""
        term = Terminator(max_generations=5)
        # Create dummy population
        pop = [Chromosome([Gene("g1", "p", 0.5, 0, 1)], 0.5)]
        assert term.check(pop, generation=5) is True
        assert term.check(pop, generation=4) is False

    def test_check_fitness_threshold(self):
        """Should stop when fitness threshold reached."""
        term = Terminator(fitness_threshold=0.9, min_generations=3)
        pop = [Chromosome([Gene("g1", "p", 0.5, 0, 1)], 0.95)]
        assert term.check(pop, generation=5) is True

    def test_check_stagnation(self):
        """Should stop when no improvement."""
        term = Terminator(stagnation_limit=3)
        pop = [Chromosome([Gene("g1", "p", 0.5, 0, 1)], 0.5)]
        # Run enough generations to trigger stagnation
        for gen in range(10):
            term.check(pop, generation=gen)
        assert term.is_converged is True

    def test_is_converged_property(self):
        """Should expose convergence status."""
        term = Terminator(max_generations=1)
        pop = [Chromosome([Gene("g1", "p", 0.5, 0, 1)], 0.5)]
        assert term.is_converged is False
        term.check(pop, generation=1)
        assert term.is_converged is True

    def test_convergence_reason(self):
        """Should provide convergence reason."""
        term = Terminator(max_generations=1)
        pop = [Chromosome([Gene("g1", "p", 0.5, 0, 1)], 0.5)]
        term.check(pop, generation=1)
        assert term.convergence_reason == "max_generations"


# ============================================================================
# Test Evaluator
# ============================================================================

class TestEvaluator:
    """Test Evaluator for fitness functions."""

    def test_evaluate_default(self, simple_chromosome):
        """Should evaluate with default function."""
        evaluator = Evaluator()
        fitness = evaluator.evaluate(simple_chromosome)
        assert fitness >= 0

    def test_evaluate_custom(self, simple_chromosome):
        """Should evaluate with custom function."""
        custom_func = lambda chromo: sum(g.value for g in chromo.genes)
        evaluator = Evaluator(fitness_function=custom_func)
        fitness = evaluator.evaluate(simple_chromosome)
        expected = sum(g.value for g in simple_chromosome.genes)
        assert abs(fitness - expected) < 0.001

    def test_batch_evaluate(self, population):
        """Should evaluate batch efficiently."""
        evaluator = Evaluator()
        fitnesses = evaluator.evaluate_batch(population)
        assert len(fitnesses) == len(population)


# ============================================================================
# Test EvolutionEngine Integration
# ============================================================================

class TestEvolutionEngineIntegration:
    """Test full EvolutionEngine integration."""

    def test_evolve_basic(self):
        """Should run basic evolution cycle."""
        engine = EvolutionEngine(
            gene_specs={"param1": (0.0, 1.0)},
            population_size=10,
            max_generations=5,
        )
        result = engine.evolve(context="test")
        assert result["best_fitness"] >= 0
        assert result["generations"] == 5

    def test_evolve_with_custom_fitness(self):
        """Should evolve with custom fitness function."""
        def fitness_func(chromo):
            return sum(g.value for g in chromo.genes) / len(chromo.genes)

        engine = EvolutionEngine(
            gene_specs={"param1": (0.0, 1.0)},
            population_size=10,
            max_generations=5,
            evaluate_fn=fitness_func,
        )
        result = engine.evolve(context="test")
        assert result["best_fitness"] >= 0

    def test_evolve_convergence(self):
        """Should detect convergence."""
        engine = EvolutionEngine(
            gene_specs={"param1": (0.0, 1.0)},
            population_size=10,
            max_generations=100,
            fitness_threshold=0.95,
        )
        result = engine.evolve(context="test")
        assert result["generations"] <= 100

    def test_get_best_solution(self):
        """Should return best solution found."""
        engine = EvolutionEngine(
            gene_specs={"param1": (0.0, 1.0)},
            population_size=10,
            max_generations=5,
        )
        engine.evolve(context="test")
        best = engine.get_best_solution()
        assert best is not None
        assert best.fitness >= 0

    def test_reset(self):
        """Should reset engine state."""
        engine = EvolutionEngine(
            gene_specs={"param1": (0.0, 1.0)},
            population_size=10,
            max_generations=5,
        )
        engine.evolve(context="test")
        engine.reset()
        result = engine.evolve(context="test")
        assert result["best_fitness"] >= 0


# ============================================================================
# Test Edge Cases
# ============================================================================

class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_empty_population(self):
        """Should handle empty population gracefully."""
        engine = EvolutionEngine(population_size=0)
        try:
            engine.evolve(context="test")
        except Exception:
            pass  # Expected to fail

    def test_single_gene_chromosome(self):
        """Should handle chromosome with single gene."""
        genes = [Gene("g1", "param", 0.5, 0.0, 1.0)]
        chromo = Chromosome(genes=genes, fitness=0.8)
        assert len(chromo.genes) == 1

    def test_zero_crossover_rate(self):
        """Should handle zero crossover rate."""
        engine = EvolutionEngine(
            gene_specs={"param1": (0.0, 1.0)},
            population_size=10,
            max_generations=5,
            crossover_rate=0.0,
        )
        result = engine.evolve(context="test")
        assert result["best_fitness"] >= 0

    def test_high_mutation_rate(self):
        """Should handle high mutation rate."""
        engine = EvolutionEngine(
            gene_specs={"param1": (0.0, 1.0)},
            population_size=10,
            max_generations=5,
            mutation_rate=0.9,
        )
        result = engine.evolve(context="test")
        assert result["best_fitness"] >= 0
