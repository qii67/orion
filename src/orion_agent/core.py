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


class ReActAgent:
    """A tiny ReAct-style agent that chooses tools, observes, and responds."""

    def __init__(self, tools: Optional[ToolRegistry] = None) -> None:
        self.tools = tools or ToolRegistry()

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
        if re.search(r"[\d\s\+\-\*/\(\)\.]+", lowered) and any(
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
        return f"任务: {user_message}\n结果: {final_observation}"


class Agent:
    """A self-evolving agent skeleton with memory, skills, and feedback loop."""

    def __init__(self) -> None:
        self.episodic_memory = EpisodicMemory()
        self.semantic_memory = SemanticMemory()
        self.skills = SkillRegistry()
        self.feedback = FeedbackEngine()
        self.architecture_log: List[str] = []
        self.tools = ToolRegistry()
        self.react_agent = ReActAgent(self.tools)
        self._register_default_tools()

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
