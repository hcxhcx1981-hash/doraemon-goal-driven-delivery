# 机器字段与任务判型规范（单一真源）

CORE 与全部适配器、行为测试、台账 schema 必须引用本文档的枚举值，禁止字段名或枚举漂移。

## 任务判型规则（顶层仅三类，AUDIT/PPT 均为模式或子类型，不新增顶层类型）
- 交付物是代码、功能、修复、配置变更 → `TASK_TYPE=CODE_DEV`。
- 交付物是研究、核验、结论、证据链 → `TASK_TYPE=RESEARCH`；复核历史结论/交付物 → `MODE=AUDIT`。
- 交付物是文档、PPT、表格、网页 → `TASK_TYPE=ARTIFACT`（PPT 为 ARTIFACT 子类型，执行流程见 artifact.md「PPT 专项」，不新增顶层任务类型）。
- 混合交付物：取主交付物判型；次类需求只写入 GAPS，只加载主类一份 reference。
- 判型不确定时保守取最小范围类型，并在 GAPS 记录判型依据。

## 四状态（对应 V2 硬规则 11）
- DISCOVERED：宿主目录/机制可发现本 Skill
- INSTALLED：文件就位于宿主 Skill 目录且哈希核验
- LOADED：会话中实际载入并观察到输出
- BEHAVIOR_VERIFIED：观察到规则行为（熔断/路径/收口）

## 字段定义
| 字段 | 取值 |
|---|---|
| SKILL_LOADED | `宿主:版本:加载方式`，加载方式∈{native, dispatch-injected, preview-injected, unverified}。preview-injected=宿主未安装、仅预览/构建轮内嵌，LOADED 与 BEHAVIOR_VERIFIED 均 UNVERIFIED |
| TASK_TYPE | {CODE_DEV, RESEARCH, ARTIFACT}；AUDIT 是 RESEARCH 的 MODE，不是顶层类型 |
| MODE | {NORMAL, AUDIT} |
| BUDGET | {level, time_seconds, tool_calls, model}；level∈{S, M, L, UNKNOWN}；读不到的键一律写 `UNKNOWN`（完整字串，禁止缩写漂移） |

## 安装/加载/行为验证状态（与四状态分离标注，不得互推）
- 安装状态 INSTALLED∈{INSTALLED, NOT_INSTALLED}：以宿主目录哈希核验为准；未安装写 NOT_INSTALLED。
- 实际加载状态 LOADED∈{LOADED, UNVERIFIED}：需会话内观察加载证据；自述不算。
- 行为验证状态 BEHAVIOR_VERIFIED∈{BEHAVIOR_VERIFIED, UNVERIFIED}：需观察到熔断/路径/收口真实行为。

## 一致性要求
- 任一字段在 CORE、references、adapters、tests、schemas 中出现时，键名与枚举必须与本文一致。
- 派工方预置默认值，宿主执行时回填；未知一律 UNKNOWN。
