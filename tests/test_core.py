import unittest

from orion_agent.core import Agent, Skill


class TestAgentCore(unittest.TestCase):
    def setUp(self) -> None:
        self.agent = Agent()
        self.agent.skills.register(
            Skill(
                name="planner",
                description="Generates plans from prompts",
                handler=lambda prompt: f"plan::{prompt}",
            )
        )

    def test_skill_execution_and_memory(self) -> None:
        result = self.agent.run("planner", "build adaptive memory")
        self.assertEqual(result, "plan::build adaptive memory")
        self.assertEqual(len(self.agent.episodic_memory.recent()), 1)

    def test_absorb_architecture(self) -> None:
        self.agent.absorb_architecture("paper:x", "Use layered memory hierarchy")
        value = self.agent.semantic_memory.get("architecture:paper:x")
        self.assertEqual(value, "Use layered memory hierarchy")

    def test_feedback_evolution_trigger(self) -> None:
        for _ in range(5):
            outcome = self.agent.learn_from_feedback("planner", 0.95)
        self.assertEqual(outcome["action"], "evolve_policy")
        self.assertIsNotNone(self.agent.semantic_memory.get("policy:last_evolution"))

    def test_react_dialogue_uses_calculator_tool(self) -> None:
        result = self.agent.run_dialogue_turn("请计算 2 + 3 * 4")
        self.assertEqual(result.steps[0].action, "calculator")
        self.assertEqual(result.steps[0].observation, "14.0")
        self.assertIn("14.0", result.answer)

    def test_react_dialogue_uses_shell_tool(self) -> None:
        result = self.agent.run_dialogue_turn("执行命令: echo hello")
        self.assertEqual(result.steps[0].action, "shell")
        self.assertEqual(result.steps[0].observation, "hello")

    def test_shell_sensitive_command_blocked(self) -> None:
        result = self.agent.run_dialogue_turn("执行命令: rm -rf /tmp/demo")
        self.assertEqual(result.steps[0].action, "shell")
        self.assertIn("blocked by security policy", result.steps[0].observation)

    def test_create_and_run_template_skill_via_dialogue(self) -> None:
        created = self.agent.run_dialogue_turn("create skill: greeter|Simple greet|Hello {prompt}")
        self.assertEqual(created.steps[0].action, "create_skill")
        self.assertIn("skill created: greeter", created.steps[0].observation)

        executed = self.agent.run_dialogue_turn("run skill: greeter:Orion")
        self.assertEqual(executed.steps[0].action, "run_skill")
        self.assertEqual(executed.steps[0].observation, "Hello Orion")

    def test_create_skill_rejects_sensitive_template(self) -> None:
        result = self.agent.run_dialogue_turn("create skill: leak|bad|dump password {prompt}")
        self.assertEqual(result.steps[0].action, "create_skill")
        self.assertIn("skill creation failed", result.steps[0].observation)

    def test_persona_can_be_set_and_shown(self) -> None:
        updated = self.agent.run_dialogue_turn(
            "set persona: 温暖导师|简洁回答,先结论后细节"
        )
        self.assertEqual(updated.steps[0].action, "set_persona")
        self.assertIn("persona updated", updated.steps[0].observation)

        shown = self.agent.run_dialogue_turn("show persona")
        self.assertEqual(shown.steps[0].action, "show_persona")
        self.assertIn("温暖导师", shown.steps[0].observation)
        self.assertIn("简洁回答", shown.answer)

    def test_persona_set_usage_validation(self) -> None:
        result = self.agent.run_dialogue_turn("set persona: only-style")
        self.assertEqual(result.steps[0].action, "set_persona")
        self.assertIn("usage:", result.steps[0].observation)


if __name__ == "__main__":
    unittest.main()
