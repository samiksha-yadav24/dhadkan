"""Turn a validated protocol into the text a user sees.

The emergency banner is built from verified config and is always rendered
first. Protocol content cannot remove or reorder it.
"""

from dataclasses import dataclass

from dhadkan.models import EmergencyNumbers, Protocol, ReviewStatus, Step

DISCLAIMER = "Not a substitute for professional care. Call emergency services first."
DRAFT_NOTICE = "[DRAFT: not yet reviewed by a clinician. Do not rely on this alone.]"


@dataclass(frozen=True)
class Banner:
    text: str
    primary: str
    others: tuple[str, ...]


@dataclass(frozen=True)
class Guidance:
    banner: Banner
    protocol_id: str
    title: str
    steps: tuple[Step, ...]
    review_status: ReviewStatus
    version: str


def build_banner(numbers: EmergencyNumbers) -> Banner:
    primary, *others = [n.number for n in numbers.numbers]
    return Banner(text=f"Call {primary} now", primary=primary, others=tuple(others))


def build_guidance(protocol: Protocol, numbers: EmergencyNumbers) -> Guidance:
    return Guidance(
        banner=build_banner(numbers),
        protocol_id=protocol.id,
        title=protocol.title,
        steps=tuple(protocol.steps),
        review_status=protocol.review.status,
        version=protocol.review.version,
    )


def banner_line(banner: Banner) -> str:
    return f"*** {banner.text} ***"


def format_step(index: int, step: Step) -> str:
    if step.condition:
        return f"{index}. [{step.condition}] {step.text}"
    return f"{index}. {step.text}"


def render_text(guidance: Guidance) -> str:
    lines = [banner_line(guidance.banner)]
    if guidance.banner.others:
        lines.append(f"Other numbers: {', '.join(guidance.banner.others)}")
    lines += ["", guidance.title, ""]
    if guidance.review_status is ReviewStatus.DRAFT:
        lines += [DRAFT_NOTICE, ""]
    lines += [format_step(i, s) for i, s in enumerate(guidance.steps, 1)]
    lines += ["", DISCLAIMER]
    return "\n".join(lines)
