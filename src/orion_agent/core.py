from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from statistics import mean
from typing import Callable, Dict, List, Optional


@dataclass
class MemoryEvent:
    timestamp: datetime
    category: str
    content: str
    score: float = 0.0


class EpisodicMemory:
    """Stores interaction-level events for short/medium-term replay."""

    def __init__(self) -> None:
        self._events: List[MemoryEvent] = []

    def add(self, category: str, content: str, score: float = 0.0) -> None:
        self._events.append(
            MemoryEvent(
                timestamp=datetime.now(timezone.utc),
                category=category,
                content=content,
                score=score,
            )
        )

    def recent(self, limit: int = 10) -> List[MemoryEvent]:
        return self._events[-limit:]


class SemanticMemory:
    """Stores distilled long-term knowledge and architectural patterns."""

    def __init__(self) -> None:
        self._facts: Dict[str, str] = {}

    def upsert(self, key: str, value: str) -> None:
        self._facts[key] = value

    def get(self, key: str) -> Optional[str]:
        return self._facts.get(key)

    def export(self) -> Dict[str, str]:
        return dict(self._facts)


@dataclass
class Skill:
    name: str
    description: str
    handler: Callable[[str], str]
    version: str = "1.0.0"
    usage_count: int = 0
    scores: List[float] = field(default_factory=list)

    def execute(self, prompt: str) -> str:
        self.usage_count += 1
        return self.handler(prompt)

    def record_score(self, value: float) -> None:
        self.scores.append(value)

    @property
    def avg_score(self) -> float:
        return mean(self.scores) if self.scores else 0.0


class SkillRegistry:
    """Skill-compatible extension point for external capability modules."""

    def __init__(self) -> None:
        self._skills: Dict[str, Skill] = {}

    def register(self, skill: Skill) -> None:
        self._skills[skill.name] = skill

    def get(self, name: str) -> Optional[Skill]:
        return self._skills.get(name)

    def list(self) -> List[str]:
        return sorted(self._skills.keys())


class FeedbackEngine:
    """Collects feedback and drives policy evolution decisions."""

    def __init__(self, evolve_threshold: float = 0.85) -> None:
        self.evolve_threshold = evolve_threshold
        self._global_scores: List[float] = []

    def add_feedback(self, score: float) -> None:
        self._global_scores.append(max(0.0, min(1.0, score)))

    def should_evolve(self) -> bool:
        if len(self._global_scores) < 5:
            return False
        return mean(self._global_scores[-5:]) >= self.evolve_threshold

    def average(self) -> float:
        return mean(self._global_scores) if self._global_scores else 0.0


class Agent:
    """A self-evolving agent skeleton with memory, skills, and feedback loop."""

    def __init__(self) -> None:
        self.episodic_memory = EpisodicMemory()
        self.semantic_memory = SemanticMemory()
        self.skills = SkillRegistry()
        self.feedback = FeedbackEngine()
        self.architecture_log: List[str] = []

    def absorb_architecture(self, source: str, design_note: str) -> None:
        key = f"architecture:{source}"
        self.semantic_memory.upsert(key, design_note)
        self.architecture_log.append(key)
        self.episodic_memory.add(
            category="architecture_absorption",
            content=f"Absorbed architecture from {source}",
            score=0.7,
        )

    def run(self, skill_name: str, prompt: str) -> str:
        skill = self.skills.get(skill_name)
        if not skill:
            raise ValueError(f"skill not found: {skill_name}")

        response = skill.execute(prompt)
        self.episodic_memory.add(
            category="skill_execution",
            content=f"skill={skill_name}, prompt={prompt}",
            score=skill.avg_score,
        )
        return response

    def learn_from_feedback(self, skill_name: str, score: float) -> Dict[str, str]:
        skill = self.skills.get(skill_name)
        if not skill:
            raise ValueError(f"skill not found: {skill_name}")

        normalized = max(0.0, min(1.0, score))
        skill.record_score(normalized)
        self.feedback.add_feedback(normalized)

        action = "hold"
        if self.feedback.should_evolve():
            action = "evolve_policy"
            self.semantic_memory.upsert(
                "policy:last_evolution",
                (
                    "Promote high-performing strategies; archive low-performing prompts; "
                    "raise retrieval weight for successful memory traces."
                ),
            )

        self.episodic_memory.add(
            category="feedback",
            content=f"skill={skill_name}, score={normalized}, action={action}",
            score=normalized,
        )
        return {"action": action, "skill": skill_name}
