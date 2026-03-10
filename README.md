# orion

Orion 是一个面向“自我演化升级”的 AI Agent 骨架，重点包含：

- **分层记忆系统**：情节记忆（episodic）与语义记忆（semantic）。
- **Skill 扩展机制**：外部能力可以以 `Skill` 插件方式接入。
- **反馈驱动演化**：通过评分反馈触发策略升级。
- **架构吸收能力**：可把外部优秀架构沉淀到长期记忆中。
- **ReAct + Tool 执行**：支持在 TUI 中进行推理、调用工具完成任务。
- **用户自定义 Skill**：对话中可创建模板化技能并立刻运行。
- **人格系统**：用户可设定 agent 的风格与行为原则，并在回答中持续生效。
- **敏感行为管控**：对危险 shell 指令与高风险 skill 模板进行拦截。

## 快速开始

```bash
PYTHONPATH=src python -m unittest discover -s tests
```

## TUI 对话

```bash
PYTHONPATH=src python -m orion_agent.tui
```

示例：

- `请计算 2 + 3 * 4`（调用 `calculator` 工具）
- `执行命令: echo hello`（调用 `shell` 工具）
- `create skill: greeter|问候模板|你好 {prompt}`（调用 `create_skill` 工具）
- `run skill: greeter:Orion`（调用 `run_skill` 工具）
- `set persona: 温暖导师|简洁回答,先结论后细节`（调用 `set_persona` 工具）
- `show persona`（调用 `show_persona` 工具）

> 安全策略会拒绝明显危险的命令（如 `rm -rf`）以及包含敏感词（如 `password`）的技能模板。

## 核心代码

- `src/orion_agent/core.py`: Agent、Memory、SkillRegistry、FeedbackEngine、ToolRegistry、ReActAgent、敏感行为管控与动态 Skill 创建。
- `src/orion_agent/tui.py`: 终端对话界面，展示 Thought/Action/Observation。
- `tests/test_core.py`: 关键行为测试。
- `docs/agent_evolution_design.md`: 详细设计说明（记忆、技能、反馈、自我演化路线）。
