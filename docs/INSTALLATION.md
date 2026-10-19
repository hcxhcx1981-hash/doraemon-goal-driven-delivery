# 安装与实际验证

[返回 README](../README.md)

## 先定位宿主目录

不同版本、配置与机器可能采用不同目录。先查看宿主自身的 Skill 设置、已发现列表或官方帮助，确认实际用户目录。以下仅为本次本机安装位置对应的候选模式，不能视为所有版本的官方约定：

| Agent | Windows 用户目录下的候选位置 | 本次验证 |
| --- | --- | --- |
| Codex / CX | `.codex\skills` | 文件一致；当前会话显式提供规则 |
| Agnes Code / AC | `.agnes\skills` | 文件一致；发现/行为 UNVERIFIED |
| Hermes / H | `.hermes\skills\execution` | 文件一致；发现/行为 UNVERIFIED |
| WorkBuddy / WB | `.workbuddy\skills` | 文件一致；发现/行为 UNVERIFIED |
| CodeBuddy / CB | 不依赖安装目录，任务内嵌 | 文案已核对；行为 UNVERIFIED |

## Windows PowerShell

先通过可信渠道安装 Git；示例不自动安装依赖。克隆到当前选择的工作目录：

```powershell
git clone https://github.com/hcxhcx1981-hash/doraemon-goal-driven-delivery.git
Set-Location .\doraemon-goal-driven-delivery
$source = (Resolve-Path .\SKILL.md).Path
# 根据目标宿主选择一项；须先确认实际配置，没有自动探测保证。
$skillRoot = Join-Path $HOME '.codex\skills'                 # CX
# $skillRoot = Join-Path $HOME '.agnes\skills'               # AC
# $skillRoot = Join-Path $HOME '.hermes\skills\execution'    # H
# $skillRoot = Join-Path $HOME '.workbuddy\skills'           # WB
if (-not (Test-Path -LiteralPath $skillRoot -PathType Container)) {
    throw '先从宿主配置确认并创建正确的 Skill 根目录，再继续。'
}
$destination = Join-Path $skillRoot 'doraemon-goal-driven-delivery'
if (Test-Path -LiteralPath $destination) {
    throw '目标已存在；先检查版本并保留备份，不自动覆盖。'
}
New-Item -ItemType Directory -Path $destination | Out-Null
Copy-Item -LiteralPath $source -Destination (Join-Path $destination 'SKILL.md')
if ((Get-FileHash -LiteralPath $source).Hash -ne
    (Get-FileHash -LiteralPath (Join-Path $destination 'SKILL.md')).Hash) {
    throw '安装文件哈希不一致。'
}
Select-String -LiteralPath (Join-Path $destination 'SKILL.md') -Pattern 'V1.1'
```

此脚本使用 $HOME，而非某台机器的用户名。只复制本项目 SKILL.md，不复制其他配置、开发守卫或测试证据。卸载只处理自己新建的目标目录，先核对路径并保留需要的备份。

## 发现、加载与行为是三件事

1. 文件：确认哈希、YAML front matter 和 V1.1 标题。成功复制不等于宿主已发现。
2. 发现：按宿主刷新或重开会话，在其 Skill 列表查找名称；记录实际显示结果。没有列表或查不到就写 UNVERIFIED。
3. 加载：显式请求使用 `doraemon-goal-driven-delivery`；检查宿主真实加载提示或上下文证据。Agent 自述已加载不够。
4. 行为：在无业务数据、无付费调用的临时工作区派发合成失败任务，观察无新证据是否停止、同根因两轮是否停止、全任务四轮是否停止及是否保全成果。保存脱敏证据到本地；未运行写 UNVERIFIED。不要为了触发熔断绕过权限或故意调用真实失败接口。

## CodeBuddy 与其他 Agent

CB 每次派工把 [inline-rules.md](../adapters/codebuddy/inline-rules.md) 的可复制规则块附加到任务正文，再提供明确目标、范围、验收和预算。本项目不声明 CB 原生 Skill 安装已验证。若未来版本支持原生 Skills，先按真实宿主能力验证，不能从目录存在推断。

其他 Agent 优先用其真实支持的 Skill 加载机制；否则把 SKILL.md 核心规则显式随任务传入。保持安全优先级与 2/4 预算完整，不冒充自动加载。开发守卫需要另外安装或由派工明确传入适用规则。

维护验证：安装示例经 PowerShell 语法解析及隔离目录复制/哈希校验；五个宿主的实时安装与加载 E2E 未全部执行，状态仍为 UNVERIFIED。
