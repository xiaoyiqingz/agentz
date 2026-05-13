from __future__ import annotations

from pathlib import Path

from pydantic_ai_skills import SkillsToolset

from config import Settings


def get_skills_dir(settings: Settings) -> Path:
    """
    Return the configured skills directory.
    """
    return settings.skills_dir


def get_skills_toolset(settings: Settings) -> SkillsToolset:
    """
    Build the third-party agent skills toolset.
    """
    return SkillsToolset(directories=[get_skills_dir(settings)])
