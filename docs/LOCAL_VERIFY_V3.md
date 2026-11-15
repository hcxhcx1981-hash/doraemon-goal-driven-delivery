# V3 本地真实验收

保留 V2.0.2 Skill 协议；此处仅是本仓库的开发验收，不是宿主完成阻断器。
不安装 Skill、不配置 Stop Hook、不引入通用 Gate 或状态机。

## Windows 准备与执行

预先提供 Task 3.54.0、uv 0.11.18 和 Python 3.11 或更高版本，并加入 PATH。
首次仅在此隔离工作区同步开发依赖：`uv sync --locked`。
此步骤可能下载锁文件列出的依赖；正式验收离线运行，缺依赖直接失败。

唯一验收入口：`task -x --force verify`。
Task 不配置 sources、generates、status 或 run: once；每次都启动 pytest。
不使用 --lf/--ff、测试结果缓存或失败重试；禁用 pytest cacheprovider 和外部插件自动加载。
原 75 项测试不改；jsonschema 是开发依赖，原 Skill 运行仍为标准库零依赖。
pytest 原生拒绝测试失败和零测试；conftest 仅补充“退出 0 但无 passed”拒绝。
全部 skip/xfail 不算成功。部分 skip 不等于全部执行；本仓库回归须确认 75 passed、无 skip。

成功仅打印 pytest 汇总及日志位置；失败打印完整 pytest 日志。
每次日志独立保存在 `.verification/`，无论成败均保留；不要上传含敏感数据的日志。
`.venv/` 和 `.verification/` 不纳入 Git。

## 其他项目的适配

Task 是统一调用约定，不意味着统一测试语言。非 Python 项目使用自己的真实测试、
构建或制品核验命令（如已有 npm test），不复制本仓库的 pytest、uv 或 conftest。
项目负责人事先确定验收命令及“实际执行了有效验收”的证据；没有有效项目验收时写
UNVERIFIED，不用空任务、命令退出 0 或 Agent 口头声明替代。不得添加另一套通用门禁。

这是开发者主动执行的本地验收；不宣称能强制阻止 Agent 结束或证明真实宿主行为。
