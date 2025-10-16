from __future__ import annotations

from textwrap import dedent


TEXT_PROMPTS: dict[str, str] = {
    "overall_spec": dedent(
        """
        You are outlining the overarching creative brief for the project "{project_name}".
        Summarise the long-term scenario, key characters, and world-building in a structured Markdown document.
        Include sections for Setting, Characters, and Story Arcs. Incorporate any additional instructions: {instructions}
        """
    ).strip(),
    "character_design": dedent(
        """
        Generate a character design sheet for the project "{project_name}" episode {episode_label}.
        Provide Markdown bullets describing appearance, personality, costume, and signature poses.
        Reference existing lore: {existing_summary}. Apply instructions: {instructions}
        """
    ).strip(),
    "background_sample": dedent(
        """
        Produce descriptive references for background environments in "{project_name}".
        List at least three settings with mood, lighting, and colour palette guidance. Instructions: {instructions}
        """
    ).strip(),
    "episode_summary": dedent(
        """
        Write an episode synopsis for episode {episode_number} of "{project_name}".
        Provide logline, act breakdown, and cliffhanger in Markdown. Consider existing canon: {existing_summary}.
        Extra guidance: {instructions}
        """
    ).strip(),
    "episode_script": dedent(
        """
        Draft a short script excerpt for episode {episode_number} of "{project_name}".
        Use markdown with dialogue lines and beats. Leverage synopsis: {existing_summary}. Instructions: {instructions}
        """
    ).strip(),
    "storyboard_table": dedent(
        """
        Create a storyboard table for episode {episode_number} of "{project_name}".
        Return a markdown table with columns: Timecode, Visual, Direction, Notes.
        Base direction on synopsis: {existing_summary}. Extra requirements: {instructions}
        """
    ).strip(),
}


IMAGE_PROMPT_TEMPLATE = dedent(
    """
    Generate a keyframe concept art for episode {episode_number} of "{project_name}".
    Scene description: {instructions}
    Maintain consistency with existing lore: {existing_summary}
    """
).strip()
