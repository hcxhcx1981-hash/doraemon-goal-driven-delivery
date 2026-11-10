# 执行、验收与维护

[返回 README](../README.md)

任务类型为 CODE_DEV / RESEARCH（含 AUDIT 模式）/ ARTIFACT（含 PPT 子类型）；判型与子类型规则见 `references/machine-fields.md`。启动前冻结 GOAL_BASELINE：目标、产物、已有基线、验收、授权、禁止动作、资源预算。只做一次最小环境检查，再连续执行实现/采集、验证、定位、有限修复和复测。每个有效修复都有证据账目；计数跟随任务与根因，不跟随文件名或聊天名称。L 级任务写 `task-ledger.json`，跨会话继承计数与预算。

验证失败先分析证据，再检查修复前的预算与安全边界。计数达到 2/4 后不能再做下一轮；成功则立即交付，失败则熔断保全。即使尚有预算，没有新证据也不继续。验收通过后不擅自启动新阶段。停轮询（连续 2 次无变化）不等于取消后台任务。

## 可复现验证

```powershell
python -X utf8 -m unittest discover -s tests -v
python -X utf8 tests\schema_check.py   # JSON Schema Draft 2020-12 真实正反例校验（需 jsonschema，开发依赖）
python -X utf8 tests\behavior_ac.py    # 宿主模拟行为测试（模拟，不是宿主真实行为验证）
```

测试分层（见 README「验证状态」）：静态规则测试（文档契约/链接/安全模式）、真实代码测试（path_engine/ledger 随包实现 + 自建 Git 夹具）、模拟测试（行为测试在临时树模拟宿主管线）、宿主行为测试（须在真实宿主隔离 E2E，本包不代验）。测试不执行 Agent、不联网、不读取真实密钥。Git 夹具由 `make_git_fixture` 自建，不依赖 ZIP 中隐藏的 `.git`。
