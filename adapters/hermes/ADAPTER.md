# Adapter: Hermes (H) — Doraemon V2

宿主加载机制：`.hermes\skills\<name>\SKILL.md`（Hermes Skill 目录；实际加载机制须按 H 宿主实测，不得假设与其他宿主相同）。

## 适配方式
- CORE 与 references 平铺到 `skills/doraemon-goal-driven-delivery/`。
- 当前基线差异：本机 H 现存副本为 **V1.1**（SHA256 `4BA20606…`，2026-10-20），V2 前必须先同步升级并核验哈希。
- 历史/台账位置（B 级搜索提示）：`.hermes\projects`、`.hermes\workspace` 等，动态检测，不存在则 UNVERIFIED 跳过。

## 宿主四态（截至 2026-11-09）
| 状态 | 当前记录 |
|---|---|
| DISCOVERED | skills 目录存在，可写 |
| INSTALLED | **否**——现为 V1.1，非 V2 |
| LOADED | **UNVERIFIED** |
| BEHAVIOR_VERIFIED | **UNVERIFIED** |

本适配器不自动安装、不修改 H 配置；升级 H 副本属于实施轮。
