from pathlib import Path

from typer.testing import CliRunner

from dhadkan.cli import app

runner = CliRunner()


def test_validate_ok(content_dir: Path) -> None:
    result = runner.invoke(app, ["validate", "--content", str(content_dir)])
    assert result.exit_code == 0
    assert "OK" in result.output


def test_validate_missing_folder_fails(tmp_path: Path) -> None:
    result = runner.invoke(app, ["validate", "--content", str(tmp_path)])
    assert result.exit_code == 1


def test_show_leads_with_emergency_banner(content_dir: Path) -> None:
    result = runner.invoke(
        app, ["show", "cardiac-arrest-cols", "--content", str(content_dir)]
    )
    assert result.exit_code == 0
    assert result.output.splitlines()[0] == "*** Call 112 now ***"


def test_show_unknown_protocol_fails(content_dir: Path) -> None:
    result = runner.invoke(app, ["show", "nope", "--content", str(content_dir)])
    assert result.exit_code == 1


def test_walk_runs(content_dir: Path) -> None:
    result = runner.invoke(
        app, ["walk", "cardiac-arrest-cols", "--content", str(content_dir)]
    )
    assert result.exit_code == 0
    assert "Call 112 now" in result.output


def test_build_writes_bundle(content_dir: Path, tmp_path: Path) -> None:
    out = tmp_path / "bundle.json"
    result = runner.invoke(
        app, ["build", "--content", str(content_dir), "--out", str(out)]
    )
    assert result.exit_code == 0
    assert out.exists()


def test_risk_command_scores_table_3_example() -> None:
    args = ["risk", "--age", "60", "--sex", "male", "--waist", "101"]
    args += ["--exercise", "--family", "both_parents"]
    result = runner.invoke(app, args)
    assert result.exit_code == 0
    assert "= 90" in result.output
    assert "not a diagnosis" in result.output


def test_risk_command_rejects_bad_age() -> None:
    result = runner.invoke(
        app, ["risk", "--age", "5", "--sex", "female", "--waist", "75"]
    )
    assert result.exit_code == 1
