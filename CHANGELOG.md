# Changelog

## 2.0.2 (2026-11-09) — 正式发布候选（RC）结构修正 + README 专业化
基线：V1.2（SHA256 `D0DB9299B60172A72B69FD819A1472EFDC8B0D58C3D88DEFC7684655A6503722`，零改动核验通过）
本轮仅做 RC 结构修正与发布候选验收，不新增平台/调度器/无关功能；只在独立 staging 工作。

### 修正 1：Agent Skills 标准兼容
- `SKILL.md` frontmatter 补齐必需 `description`（做什么+何时用）；`license: MIT` 用标准可选字段；非标准字段 version/base/tasks 移入 `metadata` 映射（string→string，值加引号）。
- 分布 ZIP 顶层目录名必须等于 `name`（`doraemon-goal-driven-delivery`）；staging 目录名后缀 `-v2` 只属工作区，不进包。
- ZIP 全 arcname 用标准 `/` 分隔符；由 `tests/package_skill.py` 单一真源生成，`test_distribution_zip_top_dir_and_slash_paths` 校验。
- 删除包内隐藏的 `.git` fixture；Git 夹具改由测试自建。

### 修正 2：会话级上下文复用
- `references/recovery.md` 新增 §8：同会话 CORE 只加载一次；同任务不重读已读 reference；新任务只加载增量；新会话恢复 L 级任务优先读台账恢复点（next_action/计数/预算），不重放全部历史；dispatch/preview-injected 宿主由派工方负责去重。
- CORE「加载」节加 §8 指针与三句复用摘要。

### 修正 3：机器字段四分 + UNKNOWN 统一
- 新增 `references/machine-fields.md` 作为字段与判型单一真源：区分 加载方式（SKILL_LOADED 第三段 4 值）、安装状态（INSTALLED/NOT_INSTALLED）、实际加载状态（LOADED/UNVERIFIED）、行为验证状态（BEHAVIOR_VERIFIED/UNVERIFIED），不得互推。
- 未知一律完整字串 `UNKNOWN`；全库扫描清除 `UNK` 等缩写漂移；CORE/inline-rules/behavior_ac/schema 字段名与枚举对齐。

### 修正 4：任务判型规则 + ARTIFACT PPT 专项
- machine-fields.md「任务判型规则」：顶层仅 CODE_DEV/RESEARCH/ARTIFACT；AUDIT=RESEARCH 的 MODE；PPT=ARTIFACT 子类型；混合交付取主类、次类写 GAPS；判型不确定保守取最小范围并记 GAPS。
- `references/artifact.md` 新增「PPT 专项流程」（大纲先行/固定画幅无裁剪/图 contain/断言回指来源/逐页复检/导出只修该页），不新增顶层任务类型。

### 修正 5：Schema 与 Ledger 加固
- schema：`repair_rounds.total` 升为必填（`required:["total"]`）；L 级 if/then 与 BLOCKED if/then 迁入 `allOf`（BLOCKED⇒blocked_reason+final_status=BLOCKED）；`repair_events`：`new_evidence=true` 的轮次必须 ≥1 条 evidence_refs（if/then minItems）；`async_tasks` 增加 `cancelled`/`cancel_reason`，与 `stopped` 分离——停轮询不等于取消后台任务。
- `tests/ledger.py`（真实实现）：缺 total 时 `counts_reliable=False`，`repair_allowed`/计轮全部拒绝且**禁止默认归零**；`mark_blocked` 持久化 BLOCKED 三字段；计轮需证据引用否则拒；`poll` 停止轮询保持 `cancelled=false`；新增 `cancel_task` 显式取消。
- 反例测试：计数丢失拒绝、BLOCKED 持久化往返、计轮无证据被拒、停轮询≠取消。

### 修正 6：路径发现加固（path_engine.py）
- 严格封顶：`bounded_scan_enf` 逐文件/目录判 `len(found)<max_candidates` + 函数尾 assert，单目录 6 命中也只返回 3。
- 任务词只作排序（match_score），不作为身份证据 kind：`project_identity` 只含 structure/config_ref/git/git_identity/content（文件内容命中）；纯任务词命名的伪项目 0 证据，过不了 ≥2 门禁。
- Git 核验实际仓库身份：`git_state` 要求 rev-parse work-tree **且** HEAD 可解析（空仓 unborn-HEAD 不算）；`git_identity` 暴露 branch/remote 作独立证据。
- 新增反例：空目录、伪项目（仅任务词名）、空 .git 目录、unborn-HEAD。

### 修正 7：报告识别加固
- `list_deliverables` 支持标准 Markdown 标题（`## 交付物索引` 等，剥离 `#>*-` 前缀）。
- 占位 Run ID（TEMPLATE/PLACEHOLDER/TODO/XXX 等）不算正向运行数据。
- 拆两级门禁：`report_candidates`（纯文本筛选，只证明"是候选"）与 `is_real_report(text, base_dir)`/`verify_report`（base_dir 给出时验证交付物实际存在）；文本特征单独不能证明报告真实。
- 新增反例 fixtures：`placeholder_runid.md`、`md_heading_report.md`。

### 修正 8：测试分层 + Git 夹具自建
- `tests/test_v2.py` 重写为 63 项分层：L1 静态规则（frontmatter/12条/CORE预算/链接/密钥模式/UNK漂移/README 章节/适配器一致性）、L2 真实代码（path_engine+ledger+自建 Git 夹具+真实 Draft 2020-12 校验）、L3 模拟（字段回填/按需加载，显式标注"模拟"）、L4 宿主行为测试不在本包执行（UNVERIFIED，须真实宿主隔离 E2E）。
- 原 46 项逐项保留复核（名称与断言随 RC 修正同步更新，不以数量代替质量）。
- `make_git_fixture` 自建 git 仓库（git init+commit，env 注入作者），包内不再有任何 `.git`；测试 `test_no_git_fixture_shipped_in_package` 防回归。
- `tests/schema_check.py`：jsonschema（开发依赖）Draft 2020-12 真实正反例 4 正 + 10 反；运行时零依赖，开发依赖在 `requirements-dev.txt` 分离。

### 修正 9：CodeBuddy 适配器版本与字段漂移
- `inline-rules.md` 版本 2.0.0-draft→2.0.2；字段 time/calls→time_seconds/tool_calls（与 machine-fields 对齐）；规则 10 从"禁转包"对齐为"范围"（与 CORE 12 条一致）；补 §5 停轮询≠取消、§8 台账优先恢复。
- 新增单一真源一致性校验测试（`L1_ReadmeAndAdapters.test_adapter_version_consistency_single_source` + 字段统一测试）：全部 adapters 不得出现 2.0.0-draft/2.0.1 漂移。

### README 专业化（中/英同步）
- 新增 `README.md`（中文正式版）与 `README_EN.md`（英文同步版）：项目定位（执行治理 Skill，非自动调度器、无未经验证的宿主级强制）、架构、任务分类、渐进加载、会话复用、预算熔断、跨会话恢复、宿主适配（四态表）、安装与测试（含依赖分离）、验证状态、安全限制。
- 保留 MIT `LICENSE`、`docs/`（4 篇，清理 V1.1 残留：四类→三分法、Hermes 目录、ChatGPT 单控→当前宿主总控）、`examples/`（3 篇，BUILD→CODE_DEV）。
- 全部 README 相对链接经测试逐一校验存在。

### 发布候选验收
- 全量测试 63/63 OK；行为测试 PASS；schema_check PASS（jsonschema 4.26.0）。
- ZIP 解压后直接运行全部测试（不人工补建文件）；Git 夹具自建；SHA256 清单全量重建。
- 密钥/Token/Cookie/隐私/本机绝对路径/日志泄漏全库扫描（测试内置 + 发布前人工复核）；全文件 UTF-8。
- 硬边界：V1.2 权威源/备份/AC/Codex/Hermes 安装副本零改动；不安装、不 commit/push、只动 staging。

## 2.0.1 (2026-11-09) — 审计缺陷第二轮修正
基线：V1.2（SHA256 `D0DB9299B60172A72B69FD819A1472EFDC8B0D58C3D88DEFC7684655A6503722`）
本轮仅修复审计缺陷，不重构架构。全部测试跑真实代码（`tests/path_engine.py` + `tests/ledger.py`），无平行模拟。

### 审计项 1：完整恢复 V1.2 项目治理规则
- `references/recovery.md` 新增 §7，逐条恢复 V1.2 原文：
  - 7.1 项目规则优先级（平台/宿主安全、用户授权、AGENTS.md、开发守卫、AUTHORIZED 门禁、生产门禁 > 本 Skill；与 dev-guard 叠加不替代）
  - 7.2 授权边界（明确授权范围内操作；提交/推送依派工授权；禁上传密钥/隐私/Token/Cookie/.env）
  - 7.3 必须停止条件（不中断清单 + 必须停止八条件 + "只问一个问题并附推荐"）
  - 7.4 任务范围约束（BUILD/RESEARCH/AUDIT/ARTIFACT→三分法映射；仅执行派工指定类型范围，不擅自扩大/不开后续阶段/不安排其他 Agent）
  - 7.5 用户视角汇报（完成什么功能/在哪运行/真实验收是否通过/还有什么差距；Git 日志作附录）
- CORE 第 10 条（范围约束）与"治理边界→recovery.md"指针同步指向 §7。

### 审计项 2：task-ledger.schema.json + 真实 JSON 测试
- schema：`repair_rounds` 用 `patternProperties ^total$ maximum 4` + 各根因 `maximum 2`；`async_tasks.items` 加 `if no_change_polls>=2 then stopped=true`；`budget` 统一 `time_seconds`/`tool_calls`/`quota`；`if budget.level=L then required [next_action, repair_rounds, remaining, completed]`。
- 新增 `tests/ledger.py` 真实实现（`Ledger.save/load/roundtrip` + `repair_allowed` + `record_repair` + `poll`）；N3/N4/N7 与 R2LedgerRoundTrip 全部调用该实现（不再用平行模拟）。
- R2LedgerRoundTrip 用 `TemporaryDirectory`（Windows 下 NamedTemporaryFile 手动 unlink 易锁冲突）。

### 审计项 3：path_engine
- `bounded_scan_enf` 真实 `time.monotonic` 截止；超时保留已找到候选并 `timed_out=true`；深度边界精确定义（相对深度 ≤ max_depth）。
- 候选排序先按任务词命中数（match_score），再按证据种类数。
- `git_state` 调 `git rev-parse --is-inside-work-tree`，**空 .git 目录不算 git 证据**。
- `list_deliverables` 只在"交付物索引"章节内取项（否定句"无交付物索引"不触发）；`is_real_report` 需四条件：收口标记 + 正向(非否定)运行数据 + 至少一项交付物 + 非模板。
- 反例 fixtures：`forged_report.md`（无运行数据/无交付物）、`template.md`、真实 `git` 仓库 fixture（collector 为真 work-tree，publish 无 git）。

### 审计项 4：机器字段统一
- 字段名统一为 `time_seconds` / `tool_calls`（CORE、schema、behavior_ac、inline-rules 全一致）。
- `preview-injected` 在 CORE 明确合法定义："宿主未安装、仅预览/构建轮内嵌，加载行为均 UNVERIFIED"。

### 审计项 5：适配器去"自动支持"
- codex/agnes/workbuddy/codebuddy 首行与四态表改为"未经实测验证，不得写成已支持/自动支持"，四态全部如实 UNVERIFIED。

### 审计项 6：按需加载触发条件 + 严格一层引用
- CORE"加载"节明确：普通任务不加载任何 reference；`path-discovery` 仅在"引用本机文件/项目/配置/Skill/报告且无精确路径"触发；`recovery` 仅在"触发熔断/异步/预算/恢复或需治理边界"触发。
- 消除 `code-dev.md` 对 `recovery.md` 的二层引用（内联熔断要点），references 仅引用 CORE。

### 审计项 7：回归测试
- 保留第一轮全部测试 + 新增 16 项第二轮反例（R2LedgerRoundTrip 2 / R2SchemaLLayer 3 / R2GitRealState 2 / R2ReportCounterCases 4 / R2BoundedScan 3 / R2FieldConsistency 2）。
- 全量 46 项 PASS，行为测试 PASS。

## 2.0.0-draft (2026-11-09)
首轮建设（CORE + 5 references + schema + 5 adapters + tests + CHANGELOG）。
详见下方保留条目。

### 已知限制
- `jsonschema` 库本机不可用且任务边界禁止装依赖 → N5 用标准库结构等价校验并标注 UNAVAILABLE。
- CX/AC 真实宿主内 LOADED / BEHAVIOR_VERIFIED 无法由 AC 代验，一律 UNVERIFIED。
