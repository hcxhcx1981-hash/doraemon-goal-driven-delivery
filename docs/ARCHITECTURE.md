# 架构与责任

[返回 README](../README.md)

用户定义业务目标与授权，ChatGPT 把目标变成边界清晰的派工，执行 Agent 在宿主权限内交付。技术验收先检查证据与覆盖；用户再做产品体验验收。任何模拟或静态测试都不能替代这两层验收。

README 的两张 Mermaid 图是本项目架构和状态流程的唯一图源。CX=Codex，AC=Agnes Code，H=Hermes，WB=WorkBuddy，CB=CodeBuddy。Other Agents 通过显式加载规则或任务内嵌适配。

SKILL.md 是规范性 V1.1 原文；docs 与 examples 为说明；CB 文档是精简适配，不能提升权限。tests 只检查文档契约与测试用参考状态模型，不在宿主执行路径中。没有后台服务、自动路由、工具拦截、额度读取或强制熔断实现。
