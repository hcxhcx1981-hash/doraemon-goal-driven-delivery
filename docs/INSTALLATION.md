# 安装与实际验证

[返回 README](../README.md)

本包是**执行治理 Skill，不是自动调度器**：它不替宿主安装、不自动发现、不具备未经验证的宿主级程序强制能力。安装动作属于实施轮，预览/候选包不安装、不修改宿主配置。各宿主加载机制与四态（DISCOVERED/INSTALLED/LOADED/BEHAVIOR_VERIFIED）记录见 `adapters/`，未验证项一律 UNVERIFIED。

## 先定位宿主目录

不同版本、配置与机器可能采用不同目录。先查看宿主自身的 Skill 设置、已发现列表或官方帮助，确认实际用户目录。以下仅为本次本机安装位置对应的候选模式，不能视为所有版本的官方约定：

| Agent | Windows 用户目录下的候选位置 | 本次验证 |
| --- | --- | --- |
| Codex | `.codex\skills` | 文件一致；当前会话显式提供规则 |
| Agnes Code | `.agnes\skills` | 文件一致；发现/行为 UNVERIFIED |
| Hermes | `.hermes\skills` | 现存 V1.1，V2 前须先同步升级；行为 UNVERIFIED |
| WorkBuddy | `.workbuddy\skills` | doraemon 未安装；派工内嵌，行为 UNVERIFIED |
| CodeBuddy | 不依赖安装目录，任务内嵌 | 文案经一致性校验；行为 UNVERIFIED |

## Windows PowerShell（示例，非自动执行）

先通过可信渠道安装 Git；示例不自动安装依赖。克隆到当前选择的工作目录。

**安装的是完整运行所需文件集**，不是只复制 `SKILL.md`：`SKILL.md` + `references/` + `schemas/` + `adapters/` + `LICENSE`。`SKILL.md` 只列指针，真正规则全文在 `references/`，按需加载依赖这些文件都在宿主目录内——缺任一部分都会让"按需加载"失效。

```powershell
git clone https://github.com/hcxhcx1981-hash/doraemon-goal-driven-delivery.git
Set-Location .\doraemon-goal-driven-delivery
$srcRoot = Get-Location
# 根据目标宿主选择一项；须先确认实际配置，没有自动探测保证。
$skillRoot = Join-Path $HOME '.codex\skills'                 # Codex
# $skillRoot = Join-Path $HOME '.agnes\skills'               # Agnes Code
# $skillRoot = Join-Path $HOME '.hermes\skills'              # Hermes
# $skillRoot = Join-Path $HOME '.workbuddy\skills'           # WorkBuddy
if (-not (Test-Path -LiteralPath $skillRoot -PathType Container)) {
    throw '先从宿主配置确认并创建正确的 Skill 根目录，再继续。'
}
$destination = Join-Path $skillRoot 'doraemon-goal-driven-delivery'
if (Test-Path -LiteralPath $destination) {
    throw '目标已存在；先检查版本并保留备份，不自动覆盖。'
}
New-Item -ItemType Directory -Path $destination | Out-Null

# 只复制运行所需文件集（排除 docs/examples/tests 等开发材料）
$runtime = @('SKILL.md','LICENSE','references','schemas','adapters')
foreach ($item in $runtime) {
    $src = Join-Path $srcRoot $item
    if (-not (Test-Path -LiteralPath $src)) { throw "缺少必需安装项：$item" }
    if ((Get-Item -LiteralPath $src).PSIsContainer) {
        Copy-Item -LiteralPath $src -Destination (Join-Path $destination $item) -Recurse
    } else {
        Copy-Item -LiteralPath $src -Destination (Join-Path $destination $item)
    }
}

# 逐文件哈希核验：源与目标必须完全一致（不放过任何 references 漂移）
$mismatch = 0
Get-ChildItem -LiteralPath $srcRoot | Where-Object { $runtime -contains $_.Name } |
    Get-ChildItem -Recurse -File | ForEach-Object {
    $rel = $_.FullName.Substring($srcRoot.Length + 1)
    $srcH = (Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash
    $dstH = (Get-FileHash -LiteralPath (Join-Path $destination $rel) -Algorithm SHA256).Hash
    if ($srcH -ne $dstH) { $mismatch++; Write-Error "哈希不一致：$rel" }
}
if ($mismatch -gt 0) { throw "$mismatch 个文件安装哈希不一致，安装失败。" }
Write-Output "安装完成：$destination （$runtime 全部逐文件核验一致）"
```

此脚本使用 $HOME，而非某台机器的用户名。只复制本项目的运行所需文件集（SKILL.md + references + schemas + adapters + LICENSE），不复制开发材料、其他配置、开发守卫或测试证据。卸载只处理自己新建的目标目录，先核对路径并保留需要的备份。

## 发现、加载与行为是三件事（不得互推）

1. 文件：确认哈希、YAML front matter（name+description）和 V2 版本标题，且完整运行所需文件集（SKILL.md + references + schemas + adapters + LICENSE）全部逐文件核验一致。成功复制不等于宿主已发现。
2. 发现：按宿主刷新或重开会话，在其 Skill 列表查找名称；记录实际显示结果。没有列表或查不到就写 UNVERIFIED。
3. 加载：显式请求使用 `doraemon-goal-driven-delivery`；检查宿主真实加载提示或上下文证据。Agent 自述已加载不够。
4. 行为：在无业务数据、无付费调用的临时工作区派发合成失败任务，观察无新证据是否停止、同根因两轮是否停止、全任务四轮是否停止及是否保全成果。保存脱敏证据到本地；未运行写 UNVERIFIED。不要为了触发熔断绕过权限或故意调用真实失败接口。

## CodeBuddy 与其他 Agent

CodeBuddy 每次派工把 [inline-rules.md](../adapters/codebuddy/inline-rules.md) 的可复制规则块附加到任务正文，再提供明确目标、范围、验收和预算。本包不声明 CodeBuddy 原生 Skill 安装已验证。若未来版本支持原生 Skills，先按真实宿主能力验证，不能从目录存在推断。

其他 Agent 优先用其真实支持的 Skill 加载机制；否则把 SKILL.md 核心规则显式随任务传入。保持安全优先级与 2/4 预算完整，不冒充自动加载。开发守卫需要另外安装或由派工明确传入适用规则。

维护验证：安装示例经 PowerShell 语法解析及隔离目录复制/哈希校验；五个宿主的实时安装与加载 E2E 未全部执行，状态仍为 UNVERIFIED。
