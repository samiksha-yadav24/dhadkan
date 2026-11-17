"""Draw the two NFHS-6 state charts as small, text-based SVG files.

Uses matplotlib's object API (no pyplot), so nothing depends on a display or on
global state. SVG text stays as text: small files, readable by screen readers,
and testable. Every chart carries its limits as a fixed note block.
"""

import textwrap
from dataclasses import dataclass
from pathlib import Path

import pandas as pd
from matplotlib import rc_context
from matplotlib.figure import Figure

from dhadkan.analytics.summary import (
    TOPICS,
    ChartData,
    chart_data,
    check_dataset,
    write_table,
)

WOMEN_COLOUR = "#0072B2"
MEN_COLOUR = "#E69F00"
TEXT_COLOUR = "#222222"
MUTED_COLOUR = "#444444"
FIG_WIDTH = 8.0
FIG_HEIGHT = 12.6
NOTE_WRAP = 118
TITLE_WRAP = 105


@dataclass(frozen=True)
class TopicText:
    title: str
    definition: str
    indicators: str
    measure_note: str


TEXT: dict[str, TopicText] = {
    "blood_pressure": TopicText(
        title="Adults with elevated blood pressure, by state/UT (%)",
        definition=(
            "Systolic 140 or more and/or diastolic 90 or more, or taking medicine "
            "to control blood pressure. Adults aged 15 and over. NFHS-6 (2023-24)."
        ),
        indicators="indicators 86 (women) and 89 (men)",
        measure_note=(
            "These are survey measurements and medicine use, not individual diagnoses."
        ),
    ),
    "blood_sugar": TopicText(
        title="Adults with high blood sugar, by state/UT (%)",
        definition=(
            "Blood sugar above 140 mg/dl, or taking medicine to control blood "
            "sugar. Adults aged 15 and over. NFHS-6 (2023-24)."
        ),
        indicators="indicators 80 (women) and 83 (men)",
        measure_note=(
            "Blood sugar is a random (not fasting) measurement, so these figures "
            "are not diabetes rates."
        ),
    ),
}


def notes_for(data: ChartData) -> list[str]:
    text = TEXT[data.topic]
    notes = [
        "Source: NFHS-6 (2023-24) India and State/UT Fact Sheets, IIPS; "
        f"{text.indicators}.",
        text.measure_note,
        "Adults aged 15 and over; this does not describe the 23-56 age group alone.",
        "Manipur is not covered by NFHS-6. Men's samples are smaller than women's, "
        "so state estimates carry sampling error: do not over-read small "
        "differences.",
        "States are ordered by the simple average of the women's and men's values, "
        "for readability only.",
    ]
    if data.flagged:
        notes.append(
            "* Based on 25-49 unweighted cases (shown in parentheses in the fact "
            "sheet); less reliable."
        )
    notes.append("For awareness only: not medical advice or a diagnosis.")
    return notes


def wrapped_notes(data: ChartData) -> list[str]:
    lines: list[str] = []
    for note in notes_for(data):
        lines += textwrap.wrap(note, width=NOTE_WRAP) or [""]
    return lines


def build_figure(data: ChartData) -> Figure:
    text = TEXT[data.topic]
    states = data.states
    count = len(states)
    ys = list(range(count))
    height = 0.38

    note_lines = wrapped_notes(data)
    notes_fraction = 0.012 + len(note_lines) * 0.0117
    axes_bottom = notes_fraction + 0.045

    fig = Figure(figsize=(FIG_WIDTH, FIG_HEIGHT))
    fig.text(
        0.02,
        0.988,
        text.title,
        ha="left",
        va="top",
        fontsize=12,
        fontweight="bold",
        color=TEXT_COLOUR,
    )
    fig.text(
        0.02,
        0.968,
        "\n".join(textwrap.wrap(text.definition, width=TITLE_WRAP)),
        ha="left",
        va="top",
        fontsize=7.5,
        color=MUTED_COLOUR,
        linespacing=1.4,
    )
    fig.text(
        0.02,
        0.012,
        "\n".join(note_lines),
        ha="left",
        va="bottom",
        fontsize=7,
        color=MUTED_COLOUR,
        linespacing=1.4,
    )

    ax = fig.add_axes((0.30, axes_bottom, 0.66, 0.925 - axes_bottom))
    series = (
        ("women", "Women", WOMEN_COLOUR, -height / 2),
        ("men", "Men", MEN_COLOUR, height / 2),
    )
    top_value = 0.0
    for group, label, colour, offset in series:
        values = [float(v) for v in states[group]]
        top_value = max(top_value, max(values))
        bars = ax.barh(
            [y + offset for y in ys],
            values,
            height=height,
            color=colour,
            label=label,
        )
        labels = [
            f"{value:.1f}{'*' if (name, group) in data.flagged else ''}"
            for name, value in zip(states.index, values, strict=True)
        ]
        ax.bar_label(bars, labels=labels, padding=2, fontsize=6, color=TEXT_COLOUR)
    for group, _label, colour, _offset in series:
        value = data.india[group]
        top_value = max(top_value, value)
        ax.axvline(
            value,
            color=colour,
            linestyle="--",
            linewidth=1,
            label=f"India, {group} ({value:.1f})",
        )

    ax.set_yticks(ys)
    ax.set_yticklabels([str(s) for s in states.index], fontsize=7)
    ax.set_ylim(count - 0.5, -0.5)
    ax.set_xlim(0, top_value * 1.12)
    ax.set_xlabel("% of adults", fontsize=8, color=MUTED_COLOUR)
    ax.tick_params(axis="x", labelsize=7)
    ax.tick_params(axis="y", length=0)
    ax.xaxis.grid(True, color="#DDDDDD", linewidth=0.6)
    ax.set_axisbelow(True)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    ax.legend(loc="lower right", fontsize=7, frameon=False)
    return fig


def render_svg(data: ChartData, path: Path) -> None:
    text = TEXT[data.topic]
    fig = build_figure(data)
    path.parent.mkdir(parents=True, exist_ok=True)
    description = (
        f"Grouped horizontal bar chart: {text.title} Women and men for each state "
        "and union territory, with India's national values as dashed lines."
    )
    metadata = {
        "Creator": "Dhadkan",
        "Date": None,
        "Title": text.title,
        "Description": description,
    }
    with rc_context({"svg.fonttype": "none", "svg.hashsalt": "dhadkan"}):
        fig.savefig(path, format="svg", metadata=metadata)


def write_charts(df: pd.DataFrame, out_dir: Path) -> list[Path]:
    """Write one SVG and one CSV (the numbers behind it) per chart topic."""
    check_dataset(df)
    written: list[Path] = []
    for topic in sorted(TOPICS):
        data = chart_data(df, topic)
        svg = out_dir / f"nfhs6_{topic}.svg"
        table = out_dir / f"nfhs6_{topic}.csv"
        render_svg(data, svg)
        write_table(data, table)
        written += [svg, table]
    return written
