# Adapter: Agnes Code (AC) — Doraemon V2

宿主加载机制：`.agnes\skills\<name>\SKILL.md`（原生 Skill 目录；`load_skill` 载入 SKILL.md 已在会话中实测可用；**对 `references/` 子文件的按需读取能力 UNVERIFIED，未验证前不得写成已支持**）。

## 适配方式
- CORE 放入 `.agnes\skills\doraemon-goal-driven-delivery\SKILL.md`。
- references 同目录平铺；宿主经 `load_skill(name, "references/xxx.md")` 单层读取——**该嵌套读取行为 UNVERIFIED**，实施轮需实测；未确认前由宿主直接读文件。
- 机器可读字段（SKILL_LOADED/TASK_TYPE/MODE/BUDGET）由 AC 在会话输出中回填，BUDGET 读不到写 UNKNOWN。
- 宿主硬限制：AC 的 turn budget、工具审批**为宿主潜在硬限制，是否对本任务强制 UNVERIFIED**；未实测前按软规则+台账留痕，不宣称为程序级强制熔断。

## 宿主四态（截至 2026-11-09）
| 状态 | 当前记录 |
|---|---|
| DISCOVERED | skills 目录可写 |
| INSTALLED | 待实施轮（本预览包未安装） |
| LOADED | **UNVERIFIED**（本轮为预览建设，未装入 AC skills 目录） |
| BEHAVIOR_VERIFIED | **UNVERIFIED** |

> 说明：AC 本轮以"读取+行为测试"方式验证 V2 规则可执行性（`tests/behavior_ac.py` 以 preview-injected 注入），但未把 V2 装入 `.agnes\skills`（交付边界：不安装）。故 LOADED/BEHAVIOR_VERIFIED 均标 UNVERIFIED。
