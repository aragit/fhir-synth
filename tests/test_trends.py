import math
import random

import pytest

from fhir_synth.models import TrendConfig
from fhir_synth.trends import (
    add_noise,
    apply_dropout,
    apply_trend,
    clamp_values,
    exponential_trend,
    linear_trend,
    sinusoidal_trend,
    step_trend,
)


class TestLinearTrend:
    def test_positive_slope(self):
        t = [0, 1, 2, 3, 4, 5]
        result = linear_trend(t, slope=2.0, baseline=10)
        assert result == [10.0, 12.0, 14.0, 16.0, 18.0, 20.0]

    def test_negative_slope(self):
        t = [0, 1, 2, 3]
        result = linear_trend(t, slope=-5.0, baseline=100)
        assert result == [100.0, 95.0, 90.0, 85.0]

    def test_zero_slope(self):
        t = [0, 10, 100]
        result = linear_trend(t, slope=0, baseline=42)
        assert result == [42.0, 42.0, 42.0]

    def test_empty(self):
        assert linear_trend([], slope=1, baseline=0) == []


class TestExponentialTrend:
    def test_decay(self):
        t = [0, 1, 2]
        hl = 1.0
        result = exponential_trend(t, hl, 100, 0)
        assert abs(result[0] - 100.0) < 1e-9
        assert abs(result[1] - 50.0) < 0.1
        assert abs(result[2] - 25.0) < 0.1

    def test_to_asymptote(self):
        t = [0, 5, 10]
        hl = 2.0
        result = exponential_trend(t, hl, 50, 30)
        assert abs(result[0] - 50.0) < 1e-9
        assert result[1] > 30
        assert result[2] > 30

    def test_empty(self):
        assert exponential_trend([], 1.0, 0, 0) == []


class TestStepTrend:
    def test_step_up(self):
        t = [0, 1, 2, 3, 4, 5]
        result = step_trend(t, step_at=3, before=10, after=20)
        assert result == [10.0, 10.0, 10.0, 20.0, 20.0, 20.0]

    def test_step_down(self):
        t = [0, 5, 10]
        result = step_trend(t, step_at=5, before=100, after=0)
        assert result == [100.0, 0.0, 0.0]

    def test_at_zero(self):
        t = [0]
        result = step_trend(t, step_at=0, before=1, after=2)
        assert result == [2.0]

    def test_empty(self):
        assert step_trend([], 0, 0, 0) == []


class TestSinusoidalTrend:
    def test_sine(self):
        t = [0, 15, 30, 45, 60]
        result = sinusoidal_trend(t, amplitude=10, period=60, baseline=50)
        assert abs(result[0] - 50.0) < 1e-9
        assert abs(result[2] - 50.0) < 1e-9
        assert abs(result[1] - 60.0) < 1e-9
        assert abs(result[3] - 40.0) < 1e-9

    def test_empty(self):
        assert sinusoidal_trend([], 1, 60, 0) == []


class TestNoise:
    def test_mean_approx_zero(self):
        rng = random.Random(42)
        values = [50.0] * 10000
        noisy = add_noise(values, 5.0, rng)
        mean = sum(noisy) / len(noisy)
        assert abs(mean - 50.0) < 0.3

    def test_std_approx(self):
        rng = random.Random(123)
        values = [0.0] * 10000
        noisy = add_noise(values, 3.0, rng)
        variance = sum((x - 0.0) ** 2 for x in noisy) / len(noisy)
        std = math.sqrt(variance)
        assert abs(std - 3.0) < 0.15

    def test_empty(self):
        rng = random.Random(0)
        assert add_noise([], 1.0, rng) == []


class TestDropout:
    def test_rate_zero(self):
        rng = random.Random(42)
        values = [1.0, 2.0, 3.0]
        result = apply_dropout(values, 0.0, rng)
        assert result == [1.0, 2.0, 3.0]

    def test_rate_one(self):
        rng = random.Random(42)
        values = [1.0, 2.0, 3.0]
        result = apply_dropout(values, 1.0, rng)
        assert result == [None, None, None]

    def test_rate_accuracy(self):
        rng = random.Random(42)
        n = 10000
        values = [1.0] * n
        result = apply_dropout(values, 0.2, rng)
        none_count = sum(1 for v in result if v is None)
        assert abs(none_count / n - 0.2) < 0.02

    def test_empty(self):
        rng = random.Random(0)
        assert apply_dropout([], 0.5, rng) == []


class TestClamp:
    def test_clamp_both(self):
        result = clamp_values([-10.0, 5.0, 50.0, 100.0], 0.0, 30.0)
        assert result == [0.0, 5.0, 30.0, 30.0]

    def test_clamp_min_only(self):
        result = clamp_values([-5.0, 0.0, 10.0], min_v=0.0, max_v=None)
        assert result == [0.0, 0.0, 10.0]

    def test_clamp_max_only(self):
        result = clamp_values([5.0, 10.0, 15.0], min_v=None, max_v=10.0)
        assert result == [5.0, 10.0, 10.0]

    def test_preserves_none(self):
        result = clamp_values([None, 5.0, None], 0.0, 10.0)
        assert result == [None, 5.0, None]

    def test_empty(self):
        assert clamp_values([], None, None) == []


class TestApplyTrend:
    def test_linear(self):
        rng = random.Random(42)
        cfg = TrendConfig(trend_type="linear", baseline=10, slope=2)
        result = apply_trend(cfg, [0, 1, 2, 3], rng)
        assert len(result) == 4
        assert abs(result[0] - 10.0) < 1
        assert abs(result[3] - 16.0) < 1

    def test_linear_with_noise_clamp(self):
        rng = random.Random(42)
        cfg = TrendConfig(
            trend_type="linear",
            baseline=100,
            slope=-5,
            noise_std=2.0,
            min_value=0,
            max_value=100,
        )
        result = apply_trend(cfg, [0, 5, 10, 20, 30], rng)
        for v in result:
            if v is not None:
                assert 0 <= v <= 100

    def test_exponential(self):
        rng = random.Random(42)
        cfg = TrendConfig(trend_type="exponential", baseline=100, half_life=1.0)
        result = apply_trend(cfg, [0, 1, 2], rng)
        assert abs(result[0] - 100.0) < 1

    def test_step(self):
        rng = random.Random(42)
        cfg = TrendConfig(
            trend_type="step", baseline=10, slope=5, amplitude=20
        )
        result = apply_trend(cfg, [0, 1, 2, 3, 4, 5], rng)
        assert len(result) == 6

    def test_sinusoidal(self):
        rng = random.Random(42)
        cfg = TrendConfig(
            trend_type="sinusoidal",
            baseline=50,
            amplitude=10,
            period_minutes=60,
        )
        result = apply_trend(cfg, [0, 30, 60], rng)
        assert abs(result[0] - 50.0) < 2
        assert abs(result[2] - 50.0) < 2

    def test_dropout(self):
        rng = random.Random(42)
        cfg = TrendConfig(
            trend_type="linear",
            baseline=100,
            slope=0,
            dropout_rate=0.5,
        )
        result = apply_trend(cfg, [0] * 100, rng)
        none_count = sum(1 for v in result if v is None)
        assert none_count > 0

    def test_empty_timepoints(self):
        rng = random.Random(42)
        cfg = TrendConfig(trend_type="linear", baseline=0)
        assert apply_trend(cfg, [], rng) == []

    def test_clamp_works(self):
        rng = random.Random(42)
        cfg = TrendConfig(
            trend_type="linear",
            baseline=50,
            slope=100,
            min_value=0,
            max_value=100,
        )
        result = apply_trend(cfg, [0, 1, 2], rng)
        for v in result:
            if v is not None:
                assert 0 <= v <= 100

    def test_unknown_trend_type(self):
        rng = random.Random(42)
        cfg = TrendConfig.model_construct(
            trend_type="unknown",
            baseline=100.0,
            noise_std=0.0,
            dropout_rate=0.0,
        )
        result = apply_trend(cfg, [0, 1, 2], rng)
        assert all(v == 100.0 for v in result)
