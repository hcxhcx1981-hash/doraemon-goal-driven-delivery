# Doraemon Goal-Driven Delivery（V2.0.2 正式发布候选）

**版本 2.0.2 · 基线 V1.2（SHA256 `D0DB9299…`）· 一次授权、连续交付、证据验收、有界熔断。**

[English](README_EN.md) · [完整规则 CORE](SKILL.md) · [安装](docs/INSTALLATION.md) · [架构](docs/ARCHITECTURE.md) · [流程](docs/WORKFLOW.md) · [安全](docs/SAFETY.md) · [派工示例](examples/task-dispatch.md) · [验收报告模板](examples/acceptance-report.md)

## 项目定位

本项目是一个**模型无关（model-agnostic）、Agent 无关（agent-independent）的目标驱动执行协议**（prompt 层执行协议），不是自动调度器，不是运行时沙箱，也不具备未经验证的宿主级程序强制能力：

- 任务发起方/用户定义目标与授权，执行 Agent（可以是任何宿主、任何模型）在授权范围内自主工作；按证据验收，必要时停止并升级风险。
- 协议**不要求**存在中心调度器、不要求任何具体模型/Agent/平台、不要求固定的主/子 Agent 架构；执行 Agent 的失败交接对象由任务约定（任务发起方/授权责任方/指定接收方），不预设 ChatGPT 或任何单一控制器。
- 它把 Agent 的工作单位从"逐步问答"变成"完整可验收成果"：在一次明确授权内连续完成实现→测试→修复→复测，常规技术问题自主处理，只有实质风险/不可逆/越界才升级。
- 它提供失败熔断（同根因≤2轮、单任务≤4轮、无新证据即停）与跨会话台账恢复（仅 L 级任务写 `task-ledger.json`）。
- 它**不**自动安装 Skill、**不**替宿主做程序级强制熔断、**不**自动购买额度。宿主能否强制某条规则，以宿主实测为准；未验证的能力一律标注 UNVERIFIED，不写成"已支持"。
- 平台安全规则、用户授权、项目 `AGENTS.md` 与开发守卫**优先于本 Skill**；本 Skill 不授予任何额外权限，也禁止未经授权转包。

## 架构：CORE + 一层 references + adapters

```
doraemon-goal-driven-delivery/
├── SKILL.md               # V2 CORE 入口（精简为目标，高风险必停条件始终可见；12 条硬规则指针 + 机器字段）
├── references/            # 一层引用（按需加载，不嵌套第二层）
│   ├── code-dev.md        #   CODE_DEV 任务规则
│   ├── research.md        #   RESEARCH 任务规则（AUDIT 为其 MODE）
│   ├── artifact.md        #   ARTIFACT 任务规则（含 PPT 专项子流程）
│   ├── path-discovery.md  #   路径自主发现（V1.2 A–H 重组：阶段/加速器/核验门禁）
│   ├── recovery.md        #   熔断/异步/预算/跨会话恢复/V1.2 治理全文/会话复用 §8
│   └── machine-fields.md #   机器字段与任务判型规范（单一真源，禁字段漂移）
├── schemas/               # task-ledger.schema.json（JSON Schema Draft 2020-12）
├── adapters/              # 五宿主适配：agnes / codex / hermes / workbuddy / codebuddy
├── tests/                 # 分层测试 + 参考实现（path_engine.py / ledger.py / schema_check.py）
├── docs/ examples/ LICENSE CHANGELOG.md
```

**Agent Skills 标准兼容**：`SKILL.md` frontmatter 按 agentskills.io 标准——必需 `name`（与目录名一致）+ `description`；非标准字段（version/base/tasks）移入 `metadata` 映射；`license` 用标准可选字段。

## 任务分类（顶层三类，不新增类型）

| TASK_TYPE | 判型（按主交付物） | 加载 | 说明 |
|---|---|---|---|
| CODE_DEV | 交付物=代码/功能/修复/配置变更 | code-dev.md | V1.2 BUILD 映射 |
| RESEARCH | 交付物=研究/核验/结论/证据链 | research.md | **AUDIT 是 MODE=AUDIT，不是顶层类型** |
| ARTIFACT | 交付物=文档/PPT/表格/网页 | artifact.md | **PPT 是子类型**，走 artifact.md「PPT 专项流程」 |

混合交付物取主类判型，次类写 GAPS，只加载主类一份 reference。判型与字段的唯一规范：[machine-fields.md](references/machine-fields.md)。

### 三类任务使用示例（通用、可复现）

| 任务（示例，可任意替换为同类任务） | 派工字段 | 判型 | 加载 |
|---|---|---|---|
| 为现有 REST API 端点增加输入校验与错误返回 | `TASK_TYPE=CODE_DEV` `GOAL=…` `BUDGET={level:M,time_seconds:1800,tool_calls:25}` | CODE_DEV | code-dev.md |
| 核验某第三方库安全修复在本项目依赖中是否仍然有效 | `TASK_TYPE=RESEARCH` `MODE=AUDIT` | RESEARCH（AUDIT=MODE） | research.md |
| 产出 10 页产品发布公告 PPT（含数据页与 QA 页） | `TASK_TYPE=ARTIFACT`（PPT 子类型） | ARTIFACT | artifact.md「PPT 专项」 |

每个示例都在派工中写明 GOAL / 范围 / 验收 / 授权 / BUDGET，Agent 一次性连续执行；普通技术选择自主处理，只有实质风险才请示。

## 软规则与运行时硬限制（必须区分）

- **软规则（本 Skill 提供）**：全部 12 条硬规则、熔断 2/4 轮、停轮询、台账继承都是 **prompt 层约定**，靠模型遵守；宿主没有程序级强制时，"熔断"体现为 Agent 主动停止并记录，而非被运行时拦截。
- **运行时硬限制（宿主/平台提供，非本 Skill）**：工具权限、生产门禁、授权边界、额度与配额由平台/用户授权控制；本 Skill **不授予也不绕过**它们。
- 因此宿主能力一律按实测标注（见下表），未验证项写 UNVERIFIED；不得把"宿主支持/已验证"当成默认事实。

## 渐进加载与会话复用

- **一层引用**：CORE 只列指针；reference 不嵌套引用其他 reference（code-dev.md 已内联熔断要点，不再二层引用 recovery.md）。
- **按需触发**：普通任务不加载任何 reference；无精确路径才加载 path-discovery.md；触发熔断/异步/预算/恢复/治理边界才加载 recovery.md。
- **会话复用（recovery.md §8）**：同一会话 CORE 只加载一次；同一任务不重复读取已读 reference；新任务只加载新增所需 reference；新会话恢复 L 级任务时**优先读台账恢复点（next_action/计数/预算），不重放全部历史**。

## 预算与熔断

- 任务规模 S/M/L 由派工设定；读不到的预算键写 `UNKNOWN`（完整字串，禁止缩写漂移），额度读不到写 `QUOTA=UNKNOWN`。
- 熔断继承 V1.2 规则 A–E：同根因≤2 轮有证据修复；单任务≤4 轮有效修复；无新证据即停；禁改名/拆分/重启规避。
- 每轮修复必须记录：根因假设/支持证据/最小修改/验收方式；有效修复轮必须在台账 `repair_events` 中关联≥1 条证据（`new_evidence=true` 无证据引用即被拒）。
- **异步防护**：优先等完成通知；连续 2 次轮询无变化**停止轮询**——停轮询≠取消后台任务，取消是台账中独立的 `cancelled` 标志。
- **计数不可丢失**：L 级台账 `repair_rounds.total` 为必填；缺失计数时**拒绝继续修复，禁止默认归零**；无新证据时持久化 `BLOCKED` 状态（status+blocked_reason+final_status 同写）。

## 跨会话恢复（仅 L 级）

`task-ledger.json` 结构见 [schemas/task-ledger.schema.json](schemas/task-ledger.schema.json)（Draft 2020-12）。恢复流程：读台账→核验成果存在→继承修复计数与预算→从 `next_action` 恢复点继续→不重做已验证工作。台账不落公开仓库、不记密钥/隐私。

## 宿主适配（四态如实标注）

| 宿主 | DISCOVERED | INSTALLED | LOADED | BEHAVIOR_VERIFIED |
|---|---|---|---|---|
| Agnes Code | skills 目录可写 | 待实施轮（本包不安装） | UNVERIFIED | UNVERIFIED |
| Codex | skills 目录可写 | 待实施轮 | UNVERIFIED | UNVERIFIED |
| Hermes | 现存 V1.1，V2 前须先同步 | 否（现为 V1.1） | UNVERIFIED | UNVERIFIED |
| WorkBuddy | 目录存在 | 否（派工内嵌） | UNVERIFIED | UNVERIFIED |
| CodeBuddy | 不依赖安装目录 | 否（派工内嵌） | UNVERIFIED | UNVERIFIED |

详见各 [adapters/](adapters/) 文件；CodeBuddy 内嵌规则与 CORE 做**可复现的静态一致性校验**（`tests/consistency_check.py`，12 条规则号/版本/机器字段/必停条件逐词比对；无生成器，不声称自动生成），未验证能力一律不写成"自动支持"。

## 安装与测试

```powershell
# 安装（实施轮；本预览/候选包不安装、不修改宿主配置）见 docs/INSTALLATION.md
python -X utf8 -m unittest discover -s tests -v      # 全量分层测试（随包参考实现 + 自建 Git 夹具）
python -X utf8 tests\schema_check.py                # JSON Schema Draft 2020-12 真实正反例校验（需 jsonschema，开发依赖）
python -X utf8 tests\behavior_ac.py                 # 宿主模拟行为测试（模拟 ≠ 宿主真实行为验证）
python -X utf8 tests\consistency_check.py           # CodeBuddy inline-rules 与 CORE 一致性校验（可复现，退出码 0=一致）
```

**依赖分离**：运行时零依赖（Python 标准库）；开发依赖 `requirements-dev.txt`（jsonschema，仅 schema_check 与完整测试使用）。ZIP 解压后可直接运行全部测试，Git 夹具由测试自建（`make_git_fixture`），不依赖 ZIP 中隐藏的 `.git`。

**测试分层**（不以数量代替质量）：
1. 静态规则测试：文档契约/frontmatter/链接/安全模式/CORE 预算；
2. 真实代码测试：path_engine.py、ledger.py 随包实现 + 真实 Git 仓库夹具；
3. 模拟测试：行为管线在临时目录模拟宿主管线（明确标注"模拟"，不冒充宿主真实行为验证）；
4. 宿主行为测试：须在真实宿主做隔离 E2E（CX/AC 运行时 LOADED/BEHAVIOR_VERIFIED 无法由本包代验，一律 UNVERIFIED）。

## 验证状态（截至 2026-11-09）

| 项 | 状态 |
|---|---|
| V1.2 权威源/备份/AC/Codex 安装副本哈希 | 零改动核验通过（D0DB9299 / 4BA20606） |
| 全量测试（静态+真实代码+模拟） | 见 tests/*.log |
| schema Draft 2020-12 正反例 | schema_check.py（jsonschema 4.26.0） |
| 宿主 LOADED / BEHAVIOR_VERIFIED | 全部 UNVERIFIED（须真实宿主 E2E） |
| Hermes 同步 | 仍为 V1.1，V2 部署前须升级 |

## 安全限制

- 不泄露/上传密钥、Token、Cookie、密码、隐私、`.env`；不自动购买额度；QUOTA 读不到=UNKNOWN。
- 不修改/绕过项目安全门禁；不可逆操作、越权、隐私外传、新增费用必须停止并请示。
- 发布物扫描：密钥模式、真实隐私、用户本机绝对路径、日志泄漏；全部文件 UTF-8。
- MIT 授权只覆盖本仓库内容（见 [LICENSE](LICENSE)），不包含第三方 Agent 的实现与商标。

## 变更历史

见 [CHANGELOG.md](CHANGELOG.md)（2.0.2 RC：结构修正 + README 专业化；2.0.1：审计缺陷二轮修正；2.0.0-draft：首轮建设）。

## 版本沿革（准确描述，避免误读）

- **远端 `main` 当前基线为 V1.1**（Git 提交 `2bc1117`，"Use public agent names and add GitHub Actions contract CI"）。
- **V1.2 是本地维护的版本线**（权威源 SHA256 `D0DB9299…`，含 11-05 历史审计包与 8/8 测试日志证据），**远端尚不存在独立的 V1.2 Git 提交**；本仓库的 `references/`、`schemas/`、`adapters/` 等由 V1.2 规则演进而来。
- V2（本包）以 V1.2 为规则基线：V1.2 的四类任务→V2 三分法映射、V1.1 引入的熔断规则 A–E、V1.2 新增的路径自主发现 A–H，均在 `references/` 中完整承接。
