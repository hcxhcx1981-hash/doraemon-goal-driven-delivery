# Adapter: CodeBuddy (CB) — Doraemon V2

宿主加载机制：CodeBuddy 无已验证的原生 Skill 自动加载目录；依赖 `adapters/codebuddy/inline-rules.md` 随派工指令内嵌（V1.2 已有此适配文件，V2 延续并加同步校验）。内嵌是否被 CB 实际读取 **UNVERIFIED，不得写成自动支持**。

## 适配方式
- 一致性机制：`inline-rules.md` 与 V2 CORE + references 逐词比对，由 `tests/consistency_check.py` 做**可复现的静态一致性校验**（12 条规则号/版本/机器字段/必停条件），不做"自动生成"声明（无生成器，只校验漂移）。
- 内嵌内容：CORE 摘要（≤2.5KB）+ 对应任务规则（code-dev/research/artifact 之一）+ 路径发现三句 + 熔断一句话。
- 机器可读字段（SKILL_LOADED/TASK_TYPE/MODE/BUDGET）由派工方在指令中预置默认值，CB 执行时回填。
- CB 宿主无法程序化强制熔断/轮次：只能软规则 + 台账留痕，**不得宣称为硬限制**（§5 软硬分离）。

## 宿主四态（截至 2026-11-09）
| 状态 | 当前记录 |
|---|---|
| DISCOVERED | skills 目录存在（无 doraemon） |
| INSTALLED | **否**（靠派工内嵌，非安装） |
| LOADED | **UNVERIFIED**（取决于派工方是否内嵌） |
| BEHAVIOR_VERIFIED | **UNVERIFIED** |

本适配器不自动安装、不修改 CB 配置。
