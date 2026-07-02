import argparse
import json
import sys

from fhir_synth import build_timeline, assemble_fhir_bundle, SynthConfig
from fhir_synth.timeline import list_scenarios


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description="fhir-synth — Deterministic FHIR R4 Synthetic Data Generator"
    )
    parser.add_argument(
        "--scenario",
        type=str,
        default="normal",
        help="Clinical scenario to simulate",
    )
    parser.add_argument(
        "--duration",
        type=int,
        default=240,
        help="Duration in minutes",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Random seed for reproducibility",
    )
    parser.add_argument(
        "--backends",
        type=str,
        default="observation,patient,encounter",
        help="Comma-separated list of backends",
    )
    parser.add_argument(
        "--output",
        type=str,
        choices=["json", "pretty"],
        default="json",
        help="Output format",
    )
    parser.add_argument(
        "--list-scenarios",
        action="store_true",
        help="List available scenarios and exit",
    )

    args = parser.parse_args(argv)

    if args.list_scenarios:
        for name in list_scenarios():
            print(name)
        return

    config = SynthConfig(
        duration_minutes=args.duration,
        backends=[b.strip() for b in args.backends.split(",")],
    )

    try:
        timeline = build_timeline(args.scenario, config, seed=args.seed)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

    bundle = assemble_fhir_bundle(timeline, config)

    if args.output == "pretty":
        print(json.dumps(bundle, indent=2))
    else:
        print(json.dumps(bundle))


if __name__ == "__main__":
    main()
