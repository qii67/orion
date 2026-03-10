from __future__ import annotations

import ast
import operator
import re
import subprocess
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


@dataclass
class Tool:
    name: str
    description: str
    handler: Callable[[str], str]

    def execute(self, tool_input: str) -> str:
        return self.handler(tool_input)


class ToolRegistry:
    """Registry for tool functions used by the ReAct loop."""

    def __init__(self) -> None:
        self._tools: Dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        self._tools[tool.name] = tool

    def get(self, name: str) -> Optional[Tool]:
        return self._tools.get(name)

    def list(self) -> List[str]:
        return sorted(self._tools.keys())


class SensitiveActionGuard:
    """Performs simple policy checks for potentially dangerous actions."""

    def __init__(self) -> None:
        self._blocked_shell_patterns = [
            (r"\brm\s+-rf\b", "blocked destructive deletion command"),
            (r"\bmkfs\b", "blocked disk formatting command"),
            (r"\bshutdown\b|\breboot\b", "blocked host control command"),
            (r":\(\)\s*\{", "blocked fork bomb pattern"),
            (r"\bcurl\b.+\|\s*(bash|sh)", "blocked piped remote script execution"),
        ]
        self._blocked_text_patterns = [
            (r"\btoken\b", "contains sensitive token keyword"),
            (r"\bpassword\b", "contains sensitive password keyword"),
            (r"\bsecret\b", "contains sensitive secret keyword"),
        ]

    def validate_shell_command(self, command: str) -> Optional[str]:
        stripped = command.strip()
        if not stripped:
            return "empty shell command is not allowed"
        for pattern, reason in self._blocked_shell_patterns:
            if re.search(pattern, stripped, flags=re.IGNORECASE):
                return reason
        return None

    def validate_skill_template(self, template: str) -> Optional[str]:
        lowered = template.lower()
        for pattern, reason in self._blocked_text_patterns:
            if re.search(pattern, lowered):
                return reason
        return None


class SafeCalculator:
    """Evaluates basic arithmetic expressions using a safe AST interpreter."""

    _operators = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.Pow: operator.pow,
        ast.Mod: operator.mod,
        ast.USub: operator.neg,
        ast.UAdd: operator.pos,
    }

    def eval_expr(self, expression: str) -> str:
        parsed = ast.parse(expression, mode="eval")
        value = self._eval_node(parsed.body)
        return str(value)

    def _eval_node(self, node: ast.AST) -> float:
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return float(node.value)
        if isinstance(node, ast.BinOp):
            op_func = self._operators.get(type(node.op))
            if not op_func:
                raise ValueError("unsupported operator")
            return op_func(self._eval_node(node.left), self._eval_node(node.right))
        if isinstance(node, ast.UnaryOp):
            op_func = self._operators.get(type(node.op))
            if not op_func:
                raise ValueError("unsupported unary operator")
            return op_func(self._eval_node(node.operand))
        raise ValueError("invalid expression")


@dataclass
class ReActStep:
    thought: str
    action: str
    action_input: str
    observation: str


@dataclass
class ReActResult:
    answer: str
    steps: List[ReActStep]


@dataclass
class PersonaProfile:
    style: str = "专业、清晰"
    principles: List[str] = field(default_factory=list)

    def to_text(self) -> str:
        principle_text = "；".join(self.principles) if self.principles else "无"
        return f"风格={self.style} | 原则={principle_text}"


class ReActAgent:
    """A tiny ReAct-style agent that chooses tools, observes, and responds."""

    def __init__(self, tools: Optional[ToolRegistry] = None, persona: Optional[PersonaProfile] = None) -> None:
        self.tools = tools or ToolRegistry()
        self.persona = persona or PersonaProfile()

    def solve(self, user_message: str) -> ReActResult:
        plan = self._plan(user_message)
        steps: List[ReActStep] = []

        for action, action_input, thought in plan:
            tool = self.tools.get(action)
            if not tool:
                observation = f"tool not found: {action}"
            else:
                try:
                    observation = tool.execute(action_input)
                except Exception as exc:  # pragma: no cover - defensive
                    observation = f"tool error: {exc}"

            steps.append(
                ReActStep(
                    thought=thought,
                    action=action,
                    action_input=action_input,
                    observation=observation,
                )
            )

        answer = self._summarize(user_message, steps)
        return ReActResult(answer=answer, steps=steps)

    def _plan(self, user_message: str) -> List[tuple[str, str, str]]:
        lowered = user_message.lower().strip()
        if lowered.startswith("create skill:") or lowered.startswith("创建技能:"):
            payload = user_message.split(":", maxsplit=1)[-1].strip()
            return [(
                "create_skill",
                payload,
                "The user wants to define a new reusable skill template.",
            )]
        if lowered.startswith("run skill:") or lowered.startswith("运行技能:"):
            payload = user_message.split(":", maxsplit=1)[-1].strip()
            return [(
                "run_skill",
                payload,
                "The user wants to invoke an existing skill by name.",
            )]
        if lowered.startswith("set persona:") or lowered.startswith("设定人格:"):
            payload = user_message.split(":", maxsplit=1)[-1].strip()
            return [(
                "set_persona",
                payload,
                "The user wants to customize the assistant persona.",
            )]
        if lowered in {"show persona", "查看人格"}:
            return [(
                "show_persona",
                "",
                "The user wants to inspect current persona settings.",
            )]
        if any(ch.isdigit() for ch in lowered) and re.search(r"[\d\s\+\-\*/\(\)\.]+", lowered) and any(
            op in lowered for op in ["+", "-", "*", "/"]
        ):
            expression = re.sub(r"[^0-9\+\-\*/\(\)\.\s]", "", user_message).strip()
            return [(
                "calculator",
                expression,
                "I should compute the arithmetic expression using calculator.",
            )]
        if any(token in lowered for token in ["shell", "命令", "运行", "执行"]):
            command = user_message.split(":", maxsplit=1)[-1].strip() if ":" in user_message else "pwd"
            return [(
                "shell",
                command,
                "The user likely needs an environment action, so I will use shell.",
            )]
        return [(
            "echo",
            user_message,
            "No special tool needed; echo can preserve the message context.",
        )]

    def _summarize(self, user_message: str, steps: List[ReActStep]) -> str:
        if not steps:
            return "I could not produce any reasoning steps."
        final_observation = steps[-1].observation
        return (
            f"[人格] {self.persona.to_text()}\n"
            f"任务: {user_message}\n"
            f"结果: {final_observation}"
        )


class Agent:
    """A self-evolving agent skeleton with memory, skills, and feedback loop."""

    def __init__(self) -> None:
        self.episodic_memory = EpisodicMemory()
        self.semantic_memory = SemanticMemory()
        self.skills = SkillRegistry()
        self.feedback = FeedbackEngine()
        self.architecture_log: List[str] = []
        self.tools = ToolRegistry()
        self.guard = SensitiveActionGuard()
        self.persona = PersonaProfile()
        self.react_agent = ReActAgent(self.tools, self.persona)
        self._register_default_tools()

    def update_persona(self, style: str, principles: List[str]) -> PersonaProfile:
        style_text = style.strip() or "专业、清晰"
        normalized_principles = [p.strip() for p in principles if p.strip()]
        self.persona.style = style_text
        self.persona.principles = normalized_principles
        self.episodic_memory.add(
            category="persona_update",
            content=f"style={style_text}, principles={normalized_principles}",
            score=0.6,
        )
        return self.persona

    def create_template_skill(self, name: str, description: str, template: str) -> str:
        normalized_name = name.strip().lower()
        if not re.match(r"^[a-z][a-z0-9_-]{1,31}$", normalized_name):
            raise ValueError("invalid skill name")
        if normalized_name in {"echo", "calculator", "shell", "create_skill", "run_skill"}:
            raise ValueError("reserved skill name")
        if self.skills.get(normalized_name):
            raise ValueError("skill already exists")
        violation = self.guard.validate_skill_template(template)
        if violation:
            raise ValueError(f"skill rejected: {violation}")

        template_text = template.strip()

        def _handler(prompt: str) -> str:
            return template_text.replace("{prompt}", prompt)

        self.skills.register(
            Skill(
                name=normalized_name,
                description=description.strip() or "User-created template skill",
                handler=_handler,
            )
        )
        self.episodic_memory.add(
            category="skill_creation",
            content=f"created skill={normalized_name}, desc={description}",
            score=0.6,
        )
        return f"skill created: {normalized_name}"

    def _register_default_tools(self) -> None:
        calc = SafeCalculator()

        self.tools.register(
            Tool(
                name="echo",
                description="Echo input text back",
                handler=lambda text: text,
            )
        )
        self.tools.register(
            Tool(
                name="calculator",
                description="Safely compute arithmetic expressions",
                handler=calc.eval_expr,
            )
        )

        def _run_shell(command: str) -> str:
            violation = self.guard.validate_shell_command(command)
            if violation:
                self.episodic_memory.add(
                    category="security_block",
                    content=f"shell blocked: command={command}, reason={violation}",
                    score=1.0,
                )
                return f"blocked by security policy: {violation}"
            completed = subprocess.run(
                command,
                shell=True,
                check=False,
                capture_output=True,
                text=True,
                timeout=8,
            )
            output = (completed.stdout or completed.stderr).strip()
            return output or "(no output)"

        self.tools.register(
            Tool(
                name="shell",
                description="Run a shell command",
                handler=_run_shell,
            )
        )

        def _create_skill(payload: str) -> str:
            pieces = [part.strip() for part in payload.split("|")]
            if len(pieces) != 3:
                return "usage: <name>|<description>|<template with optional {prompt}>"
            name, description, template = pieces
            try:
                return self.create_template_skill(name, description, template)
            except ValueError as exc:
                return f"skill creation failed: {exc}"

        self.tools.register(
            Tool(
                name="create_skill",
                description="Create a template-based skill using name|description|template",
                handler=_create_skill,
            )
        )

        def _run_skill(payload: str) -> str:
            skill_name, prompt = payload, ""
            if ":" in payload:
                skill_name, prompt = payload.split(":", maxsplit=1)
            skill = self.skills.get(skill_name.strip().lower())
            if not skill:
                return f"skill not found: {skill_name.strip()}"
            try:
                return skill.execute(prompt.strip())
            except Exception as exc:  # pragma: no cover - defensive
                return f"skill execution failed: {exc}"

        self.tools.register(
            Tool(
                name="run_skill",
                description="Run an existing skill using <skill_name>:<prompt>",
                handler=_run_skill,
            )
        )

        def _set_persona(payload: str) -> str:
            pieces = [part.strip() for part in payload.split("|")]
            if len(pieces) != 2:
                return "usage: <style>|<principle1,principle2,...>"
            style, principle_csv = pieces
            principles = [item.strip() for item in principle_csv.split(",")]
            profile = self.update_persona(style, principles)
            return f"persona updated: {profile.to_text()}"

        self.tools.register(
            Tool(
                name="set_persona",
                description="Set persona using <style>|<principle1,principle2,...>",
                handler=_set_persona,
            )
        )

        self.tools.register(
            Tool(
                name="show_persona",
                description="Show current persona settings",
                handler=lambda _payload: self.persona.to_text(),
            )
        )

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

    def run_dialogue_turn(self, user_message: str) -> ReActResult:
        result = self.react_agent.solve(user_message)
        self.episodic_memory.add(
            category="dialogue",
            content=f"user={user_message} | assistant={result.answer}",
            score=0.5,
        )
        for step in result.steps:
            self.episodic_memory.add(
                category="react_step",
                content=(
                    f"thought={step.thought} | action={step.action} "
                    f"| input={step.action_input} | observation={step.observation}"
                ),
                score=0.4,
            )
        return result

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
