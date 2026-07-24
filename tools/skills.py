"""Agent Skills toolset loading and registration."""

from pathlib import Path

from pydantic_ai_skills import SkillsToolset

from config.settings import Settings


def get_skills_dir(settings: Settings) -> Path:
    """Return the configured Agent Skills directory."""
    return settings.skills_dir


def get_skills_toolset(settings: Settings) -> SkillsToolset:
    """Build the project's progressive-disclosure Skills toolset."""
    return SkillsToolset(directories=[get_skills_dir(settings)])


def build_skills_toolsets(settings: Settings) -> list[SkillsToolset]:
    """Build the project's Agent Skills toolset collection."""
    return [get_skills_toolset(settings)]
