"""Command-line tools for validating, viewing and building content."""

from pathlib import Path
from typing import Annotated

import click
import typer
import yaml
from pydantic import ValidationError

from dhadkan.engine.bundle import write_bundle
from dhadkan.engine.guidance import (
    banner_line,
    build_guidance,
    format_step,
    render_text,
)
from dhadkan.loader import Content, ContentError, load_content
from dhadkan.models import Protocol
from dhadkan.risk.idrs import FamilyHistory, IdrsInput, Sex, calculate, summary

app = typer.Typer(help="Dhadkan content tools.", no_args_is_help=True)

DEFAULT_CONTENT = Path("content")
DEFAULT_OUT = Path("build/bundle.json")

ContentDir = Annotated[Path, typer.Option("--content", help="Content folder.")]
OutFile = Annotated[Path, typer.Option("--out", help="Output file.")]


def _load(content_dir: Path) -> Content:
    try:
        return load_content(content_dir)
    except (ContentError, ValidationError, FileNotFoundError, yaml.YAMLError) as exc:
        typer.echo(f"Content check failed: {exc}", err=True)
        raise typer.Exit(code=1) from exc


def _get(content: Content, protocol_id: str) -> Protocol:
    protocol = content.protocols.get(protocol_id)
    if protocol is None:
        known = ", ".join(sorted(content.protocols))
        typer.echo(f"Unknown protocol '{protocol_id}'. Available: {known}", err=True)
        raise typer.Exit(code=1)
    return protocol


@app.command()
def validate(content_dir: ContentDir = DEFAULT_CONTENT) -> None:
    """Validate all content and cross-references."""
    content = _load(content_dir)
    typer.echo(
        f"OK: {len(content.protocols)} protocol(s), {len(content.sources)} source(s)"
    )
    for p in content.protocols.values():
        typer.echo(f"  {p.id}: {p.review.status.value} v{p.review.version}")


@app.command()
def show(protocol_id: str, content_dir: ContentDir = DEFAULT_CONTENT) -> None:
    """Print a protocol with the emergency banner first."""
    content = _load(content_dir)
    protocol = _get(content, protocol_id)
    guidance = build_guidance(protocol, content.emergency_numbers)
    typer.echo(render_text(guidance))


@app.command()
def walk(protocol_id: str, content_dir: ContentDir = DEFAULT_CONTENT) -> None:
    """Step through a protocol one step at a time."""
    content = _load(content_dir)
    protocol = _get(content, protocol_id)
    guidance = build_guidance(protocol, content.emergency_numbers)
    typer.echo(banner_line(guidance.banner))
    typer.echo(guidance.title)
    for i, step in enumerate(guidance.steps, 1):
        typer.echo("")
        typer.echo(format_step(i, step))
        if i < len(guidance.steps):
            click.pause("-- press any key for the next step --")


@app.command()
def build(
    content_dir: ContentDir = DEFAULT_CONTENT, out: OutFile = DEFAULT_OUT
) -> None:
    """Compile content into bundle.json for the offline app."""
    content = _load(content_dir)
    write_bundle(content, out)
    typer.echo(f"Wrote {out}")


@app.command()
def risk(
    age: Annotated[int, typer.Option(help="Age in years (18-110).")],
    sex: Annotated[Sex, typer.Option(help="female or male (sets waist cutoffs).")],
    waist: Annotated[float, typer.Option(help="Waist circumference in cm.")],
    exercise: Annotated[bool, typer.Option(help="Exercise regularly.")] = False,
    demanding_work: Annotated[
        bool, typer.Option(help="Physically demanding work.")
    ] = False,
    family: Annotated[
        FamilyHistory,
        typer.Option(help="Parents with diabetes: none, one_parent, both_parents."),
    ] = FamilyHistory.NONE,
) -> None:
    """Calculate the Indian Diabetes Risk Score (a screening aid, not a diagnosis)."""
    try:
        result = calculate(
            IdrsInput(
                age_years=age,
                sex=sex,
                waist_cm=waist,
                regular_exercise=exercise,
                demanding_work=demanding_work,
                family_history=family,
            )
        )
    except ValueError as exc:
        typer.echo(f"Input problem: {exc}", err=True)
        raise typer.Exit(code=1) from exc
    typer.echo(
        f"Age {result.age} + waist {result.waist} + activity {result.activity} "
        f"+ family {result.family} = {result.total}"
    )
    typer.echo(summary(result))


if __name__ == "__main__":
    app()
