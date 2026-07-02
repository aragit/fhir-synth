import math
import random

from fhir_synth.models import TrendConfig


def linear_trend(t: list[int], slope: float, baseline: float) -> list[float]:
    return [baseline + slope * ti for ti in t]


def exponential_trend(
    t: list[int], half_life: float, baseline: float, asymptote: float
) -> list[float]:
    decay = math.log(2) / half_life
    return [asymptote + (baseline - asymptote) * math.exp(-decay * ti) for ti in t]


def step_trend(t: list[int], step_at: int, before: float, after: float) -> list[float]:
    return [after if ti >= step_at else before for ti in t]


def sinusoidal_trend(
    t: list[int], amplitude: float, period: float, baseline: float
) -> list[float]:
    freq = 2.0 * math.pi / period
    return [baseline + amplitude * math.sin(freq * ti) for ti in t]


def add_noise(values: list[float], std: float, rng: random.Random) -> list[float]:
    return [v + rng.gauss(0, std) for v in values]


def apply_dropout(
    values: list[float], rate: float, rng: random.Random
) -> list[float | None]:
    return [None if rng.random() < rate else v for v in values]


def clamp_values(
    values: list[float | None], min_v: float | None, max_v: float | None
) -> list[float | None]:
    result: list[float | None] = []
    for v in values:
        if v is not None:
            if min_v is not None:
                v = max(v, min_v)
            if max_v is not None:
                v = min(v, max_v)
        result.append(v)
    return result


def apply_trend(
    trend: TrendConfig, time_points: list[int], rng: random.Random
) -> list[float | None]:
    if trend.trend_type == "linear":
        slope = trend.slope if trend.slope is not None else 0.0
        values = linear_trend(time_points, slope, trend.baseline)
    elif trend.trend_type == "exponential":
        half_life = trend.half_life if trend.half_life is not None else 1.0
        asymptote = trend.baseline
        values = exponential_trend(time_points, half_life, trend.baseline, asymptote)
    elif trend.trend_type == "step":
        step_at = int(trend.slope if trend.slope is not None else 0)
        before = trend.baseline
        after = trend.amplitude if trend.amplitude is not None else before
        values = step_trend(time_points, step_at, before, after)
    elif trend.trend_type == "sinusoidal":
        amplitude = trend.amplitude if trend.amplitude is not None else 1.0
        period = trend.period_minutes if trend.period_minutes is not None else 60.0
        values = sinusoidal_trend(time_points, amplitude, period, trend.baseline)
    else:
        values = [trend.baseline] * len(time_points)

    if trend.noise_std > 0:
        values = add_noise(values, trend.noise_std, rng)
    if trend.dropout_rate > 0:
        values = apply_dropout(values, trend.dropout_rate, rng)
    if trend.min_value is not None or trend.max_value is not None:
        values = clamp_values(values, trend.min_value, trend.max_value)

    return values
