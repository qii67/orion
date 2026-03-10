# 自我演化 AI Agent 设计草案

## 1. 目标

构建一个可持续升级的 Agent 系统，具备：

1. 高质量记忆系统（短期 + 长期 + 可蒸馏）；
2. 兼容外部 Skill 扩展；
3. 吸收外界优秀架构并内化；
4. 基于反馈自动进化策略。

## 2. 分层记忆架构

- **Episodic Memory（情节记忆）**
  - 存储交互过程事件：任务、上下文、执行结果、反馈分数。
  - 支持 recent replay，用于短期决策。

- **Semantic Memory（语义记忆）**
  - 存储蒸馏后的稳定知识：
    - 领域知识
    - 架构模式
    - 策略快照
  - 通过 key-value 统一管理，支持版本化迁移。

- **Memory Distillation（后续可扩展）**
  - 定期从 episodic 提取高价值轨迹写入 semantic。
  - 低价值事件执行衰减/压缩。

## 3. Skill 插件化机制

- Skill 是三元结构：
  - `name`
  - `description`
  - `handler(prompt) -> response`

- SkillRegistry 职责：
  - 注册 / 查询 / 列出技能
  - 支持用户在对话中动态创建模板化 Skill（`create_skill`）并调用（`run_skill`）
  - 可扩展能力隔离（后续可加入沙箱和权限）

- 指标追踪：
  - `usage_count`
  - `avg_score`

## 4. 反馈闭环与演化策略

- FeedbackEngine 接收 [0,1] 评分；
- 当最近窗口评分均值超过阈值（默认 0.85）时触发 `evolve_policy`；
- 触发后写入语义记忆：
  - 提升高收益策略权重
  - 归档低收益 prompt
  - 提升成功记忆轨迹检索权重

## 5. 外界架构吸收机制

提供 `absorb_architecture(source, design_note)`：

- `source`：论文/仓库/方案来源
- `design_note`：抽象后的可复用设计

吸收流程：
1. 写入 semantic memory（长期沉淀）；
2. 写入 episodic event（用于追溯和评估来源可靠性）。

## 6. 安全治理层（当前实现）

- 新增敏感行为管控组件，对高风险 shell 命令进行拒绝（如 `rm -rf`、`mkfs`、fork bomb、`curl|bash`）。
- 新增技能模板内容审核，阻止包含 `token/password/secret` 等敏感关键词的模板。
- 被拦截行为会写入 episodic memory，支持后续审计与策略优化。

## 7. 下一步演进建议

1. 增加向量检索（RAG）和记忆打分器；
2. Skill 引入 manifest 与 ABI，支持跨语言插件；
3. 引入自我反思（reflection）任务，离线微调策略；
4. 增加执行配额与多级审批策略。
