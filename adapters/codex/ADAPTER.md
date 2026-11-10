# Adapter: Codex (CX) — Doraemon V2

宿主加载机制：`.codex\skills\<name>\SKILL.md`（原生 Skill 目录；**自动加载与子文件按需读取能力未经实测验证，不得写成已支持**；实际行为以宿主实测为准）。

## 适配方式
- CORE（V2 `SKILL.md`）放入 `skills/doraemon-goal-driven-delivery/SKILL.md`。
- references 同目录平铺；宿主对子文件的读取能力 **UNVERIFIED**，未验证前不得假设"按需自动读取"。
- 加载差异：若宿主会话自动发现 Skill 的经验被实测确认，才省去派工全文注入；未确认前按派工内嵌 CORE 摘要处理。

## 宿主四态（截至 2026-11-09，逐项如实标注，不得冒充）
| 状态 | 判定 | 当前记录 |
|---|---|---|
| DISCOVERED | 宿主 skills 目录可写 | INSTALLED 的前提 |
| INSTALLED | V2 文件就位且哈希核验 | 待实施轮核验（本预览包未安装） |
| LOADED | 会话中实际载入 CORE（观察 SKILL_LOADED 输出） | **UNVERIFIED**（须一次真实任务实测） |
| BEHAVIOR_VERIFIED | 任务中观察到熔断/路径/收口行为 | **UNVERIFIED** |

本适配器不自动安装、不修改 Agent 配置；安装动作属于实施轮。
