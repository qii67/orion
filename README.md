# orion

Orion 是一个面向“自我演化升级”的 AI Agent 骨架，重点包含：

- **分层记忆系统**：情节记忆（episodic）与语义记忆（semantic）。
- **Skill 扩展机制**：外部能力可以以 `Skill` 插件方式接入。
- **反馈驱动演化**：通过评分反馈触发策略升级。
- **架构吸收能力**：可把外部优秀架构沉淀到长期记忆中。

## 快速开始

```bash
PYTHONPATH=src python -m unittest discover -s tests
```

## 核心代码

- `src/orion_agent/core.py`: Agent、Memory、SkillRegistry、FeedbackEngine 的核心实现。
- `tests/test_core.py`: 关键行为测试。
- `docs/agent_evolution_design.md`: 详细设计说明（记忆、技能、反馈、自我演化路线）。
