# 架构与责任

[返回 README](../README.md)

用户定义业务目标与授权，总控（ChatGPT 或当前宿主派工方）把目标变成边界清晰的派工，执行 Agent 在宿主权限内交付。技术验收先检查证据与覆盖；用户再做产品体验验收。任何模拟或静态测试都不能替代这两层验收。

README 是本项目架构和状态流程的权威说明。支持 Codex、Agnes Code、Hermes、WorkBuddy 和 CodeBuddy 五个宿主适配；其他 Agent 通过显式加载规则或任务内嵌适配。本包是执行治理 Skill，不是自动调度器，也不具备宿主级程序强制熔断能力。

SKILL.md 是规范性 V2 CORE（2.0.2，基线 V1.2 D0DB9299）；references 一层引用按需加载；docs 与 examples 为说明；adapters 为宿主差异与四态记录（未验证项一律 UNVERIFIED）；CodeBuddy 内嵌摘要由单一真源生成并经一致性校验，不能提升权限。tests 驱动随包参考实现（path_engine/ledger），不在宿主执行路径中。没有后台服务、自动路由、工具拦截、额度读取或强制熔断实现。
