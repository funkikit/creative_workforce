from __future__ import annotations

from typing import Iterable

GLOBAL_TEMPLATES = [
    "overall_spec",
    "character_design",
    "background_sample",
]

EPISODE_TEMPLATES = [
    "episode_summary",
    "episode_script",
    "storyboard_table",
    "keyframe_image",
]


def validate_template_code(template_code: str) -> None:
    """Ensure a template code exists within the known catalogue."""

    if template_code not in GLOBAL_TEMPLATES + EPISODE_TEMPLATES:
        raise ValueError(f"未対応のテンプレートコードです: {template_code}")


def all_template_codes() -> list[str]:
    return GLOBAL_TEMPLATES + EPISODE_TEMPLATES


def expected_episode_templates(episodes: Iterable[int]) -> list[tuple[int, str]]:
    return [(episode, template) for episode in episodes for template in EPISODE_TEMPLATES]
