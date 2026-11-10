# 合成任务派工示例（V2.0.2）

使用 doraemon-goal-driven-delivery V2.0.2；开发任务叠加现有开发守卫。

- TASK_TYPE：CODE_DEV（判型依据：交付物为纯函数代码）
- GOAL：在临时目录实现一个纯函数，将合成整数列表求和。
- BASELINE：无既有代码；开始前确认实际路径与 Git 状态（一次基线检查）。
- SCOPE：仅合成示例文件与必要测试，不访问其他项目。
- ACCEPTANCE：空列表、正负整数测试通过；提供实际执行结果（真实可运行证据，非模拟）。
- AUTHORIZATION：允许本地可逆编辑与测试；不联网、不付费、不发布、不读取隐私或凭据。
- BUDGET：{level: S, time_seconds: 900, tool_calls: 40, model: <派工值>}；同根因最多 2 轮，全任务最多 4 轮有证据修复；无新证据立即停止；QUOTA=UNKNOWN。
- STOP：验收通过或熔断保全后停止，不启动下一阶段。

普通技术问题自行处理。交付 GOAL / DELIVERED / ACCEPTANCE / GAPS / REPOSITORY / FINAL_STATUS，并回填机器字段 SKILL_LOADED / TASK_TYPE / MODE / BUDGET（未知一律 UNKNOWN）。
