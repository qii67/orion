# orion

Orion 是一个面向“自我演化升级”的 AI Agent 骨架，重点包含：

- **分层记忆系统**：情节记忆（episodic）与语义记忆（semantic）。
- **Skill 扩展机制**：外部能力可以以 `Skill` 插件方式接入。
- **反馈驱动演化**：通过评分反馈触发策略升级。
- **架构吸收能力**：可把外部优秀架构沉淀到长期记忆中。
- **ReAct + Tool 执行**：支持在 TUI 中进行推理、调用工具完成任务。

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

## 核心代码

- `src/orion_agent/core.py`: Agent、Memory、SkillRegistry、FeedbackEngine、ToolRegistry、ReActAgent 核心实现。
- `src/orion_agent/tui.py`: 终端对话界面，展示 Thought/Action/Observation。
- `tests/test_core.py`: 关键行为测试。
- `docs/agent_evolution_design.md`: 详细设计说明（记忆、技能、反馈、自我演化路线）。
