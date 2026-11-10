# Adapter: WorkBuddy (WB) — Doraemon V2

宿主加载机制：WorkBuddy 有 skill 市场/缓存（`.workbuddy\skills`、skill-cloud-sync），但其 doraemon 类 Skill 无原生安装（截至 2026-11-09 扫描确认 `.workbuddy\skills` 仅有 pptx/xlsx 等）。

## 适配方式（按任务书：经验证的 Skill 或派工适配器，二选一，不得假设已验证）
- 方式 A（若 WB 原生 skill 目录被验证可用）：CORE + references 平铺安装，哈希核验。
- 方式 B（当前采用）：派工时在任务指令内注入 **CORE 摘要（≤2.5KB）+ 对应任务规则**；超出上限只保留可执行规则。
- 摘要必须从唯一真源（V2 repo）生成，禁止手工双维护（防漂移 R1）。
- 历史/台账位置（B 级搜索提示）：`.workbuddy\projects`、`.workbuddy\workspace\sessions`，动态检测。

## 宿主四态（截至 2026-11-09）
| 状态 | 当前记录 |
|---|---|
| DISCOVERED | skill 目录存在 |
| INSTALLED | **否**（doraemon 未安装） |
| LOADED | **UNVERIFIED**（取决于派工方是否注入；WB 对本 Skill 无已验证的原生自动加载机制，不得写成自动支持） |
| BEHAVIOR_VERIFIED | **UNVERIFIED** |

本适配器不自动安装、不修改 WB 配置。
