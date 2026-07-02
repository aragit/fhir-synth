import json
import sys

import pytest


class TestCLIDirect:
    def test_list_scenarios_direct(self):
        from fhir_synth.cli import main
        try:
            main(["--list-scenarios"])
        except SystemExit as e:
            pytest.fail(f"main() raised SystemExit: {e}")

    def test_unknown_scenario_direct(self):
        from fhir_synth.cli import main
        with pytest.raises(SystemExit) as exc:
            main(["--scenario", "nonexistent", "--duration", "60"])
        assert exc.value.code != 0

    def test_normal_scenario_direct(self, capsys):
        from fhir_synth.cli import main
        main(["--scenario", "normal", "--duration", "10", "--seed", "42", "--output", "json"])
        captured = capsys.readouterr()
        bundle = json.loads(captured.out)
        assert bundle["resourceType"] == "Bundle"
        assert len(bundle["entry"]) > 0

    def test_pretty_output_direct(self, capsys):
        from fhir_synth.cli import main
        main(["--scenario", "normal", "--duration", "10", "--seed", "42", "--output", "pretty"])
        captured = capsys.readouterr()
        bundle = json.loads(captured.out)
        assert bundle["resourceType"] == "Bundle"

    def test_single_backend_direct(self, capsys):
        from fhir_synth.cli import main
        main(["--scenario", "normal", "--duration", "10", "--seed", "42", "--backends", "patient"])
        captured = capsys.readouterr()
        bundle = json.loads(captured.out)
        types = {e["resource"]["resourceType"] for e in bundle["entry"]}
        assert types == {"Patient"}

    def test_deterministic_output_direct(self, capsys):
        from fhir_synth.cli import main
        main(["--scenario", "normal", "--duration", "10", "--seed", "42"])
        r1 = capsys.readouterr().out
        main(["--scenario", "normal", "--duration", "10", "--seed", "42"])
        r2 = capsys.readouterr().out
        assert r1 == r2


class TestCLISubprocess:
    def test_list_scenarios(self):
        import subprocess
        result = subprocess.run(
            [sys.executable, "-m", "fhir_synth.cli", "--list-scenarios"],
            capture_output=True, text=True,
        )
        assert result.returncode == 0
        lines = result.stdout.strip().split("\n")
        assert "normal" in lines
        assert "icu_sepsis" in lines
        assert "post_op_recovery" in lines
        assert "ards" in lines
        assert "cardiac_arrest" in lines

    def test_scenario_normal(self):
        import subprocess
        result = subprocess.run(
            [sys.executable, "-m", "fhir_synth.cli",
             "--scenario", "normal", "--duration", "60", "--seed", "42", "--output", "json"],
            capture_output=True, text=True,
        )
        assert result.returncode == 0
        bundle = json.loads(result.stdout)
        assert bundle["resourceType"] == "Bundle"

    def test_scenario_nonexistent(self):
        import subprocess
        result = subprocess.run(
            [sys.executable, "-m", "fhir_synth.cli",
             "--scenario", "nonexistent", "--duration", "60"],
            capture_output=True, text=True,
        )
        assert result.returncode != 0
        assert "Unknown scenario" in result.stderr
