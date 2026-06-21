from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

import numpy as np

from src.logger import logger


@dataclass
class MonteCarloResult:
    median: float
    mean: float
    std: float
    percentile_10: float
    percentile_90: float
    confidence_interval: tuple[float, float]
    probability_positive: float
    iterations: int
    distribution: np.ndarray = field(default_factory=lambda: np.array([]))


class MonteCarloSimulator:
    def __init__(self, iterations: int = 1000, random_seed: int = 42) -> None:
        self.iterations = iterations
        self.rng = np.random.default_rng(random_seed)

    def simulate(
        self,
        base_value: float,
        volatility: float = 0.1,
        confidence_level: float = 0.8,
    ) -> MonteCarloResult:
        noise = self.rng.normal(0, volatility, self.iterations)
        results = base_value * (1 + noise)
        lower_pct = (1 - confidence_level) / 2 * 100
        upper_pct = (1 - (1 - confidence_level) / 2) * 100

        return MonteCarloResult(
            median=float(np.median(results)),
            mean=float(np.mean(results)),
            std=float(np.std(results)),
            percentile_10=float(np.percentile(results, 10)),
            percentile_90=float(np.percentile(results, 90)),
            confidence_interval=(float(np.percentile(results, lower_pct)), float(np.percentile(results, upper_pct))),
            probability_positive=float(np.mean(results > base_value)),
            iterations=self.iterations,
            distribution=results,
        )

    def simulate_complex(
        self,
        simulation_func: Callable[[dict[str, Any]], float],
        base_params: dict[str, Any],
        param_volatility: dict[str, float],
        confidence_level: float = 0.8,
    ) -> MonteCarloResult:
        results = np.zeros(self.iterations)
        for i in range(self.iterations):
            noisy_params = base_params.copy()
            for param_name, v in param_volatility.items():
                if param_name in noisy_params:
                    noisy_params[param_name] *= 1 + self.rng.normal(0, v)
            results[i] = simulation_func(noisy_params)

        lower_pct = (1 - confidence_level) / 2 * 100
        upper_pct = (1 - (1 - confidence_level) / 2) * 100
        base_result = simulation_func(base_params)

        return MonteCarloResult(
            median=float(np.median(results)),
            mean=float(np.mean(results)),
            std=float(np.std(results)),
            percentile_10=float(np.percentile(results, 10)),
            percentile_90=float(np.percentile(results, 90)),
            confidence_interval=(float(np.percentile(results, lower_pct)), float(np.percentile(results, upper_pct))),
            probability_positive=float(np.mean(results > base_result)),
            iterations=self.iterations,
            distribution=results,
        )
