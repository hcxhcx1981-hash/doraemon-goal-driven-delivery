---
name: doraemon-goal-driven-delivery
description: 目标驱动交付治理:连续交付可验收成果、有限熔断、证据验收、台账跨会话恢复。用于开发、研究审计、文档PPT表格网页;无精确路径时自主发现目标。
license: MIT
metadata:
  version: "2.0.2"
  base: "V1.2 D0DB9299"
  tasks: "CODE_DEV|RESEARCH|ARTIFACT"
---
# V2 CORE
使命:用户定目标,授权交付。

## 加载(标准machine-fields.md)
CODE_DEV→code-dev.md / RESEARCH(AUDIT=MODE)→research.md / ARTIFACT→artifact.md
无精确路径→path-discovery.md;熔断/异步/预算/恢复/治理/复用→recovery.md
复用§8:同会话CORE一次/不重读/只增量。

## 字段(未知=UNKNOWN)
SKILL_LOADED=宿主:版本:方式(native|dispatch-injected|preview-injected|unverified)
TASK_TYPE=CODE_DEV|RESEARCH|ARTIFACT MODE=NORMAL|AUDIT
BUDGET={level,time_seconds,tool_calls,model}

## 硬规则(全文references)
1目标优先+一次基线检查。
2连续:研发=实现→测试→修复→复测;研究=采集→核验→反证→结论;不逐步请示。
3证据:存在≠可用,安装≠加载≠行为验证,单测≠全链,模拟≠生产,未验证=UNVERIFIED。
4熔断:同根因≤2轮,单任务≤4轮,无新证据即停,禁改名/拆分/重启。
5异步:等完成通知;连续2次轮询无变化即停(停轮询≠取消后台任务);不重复建任务。
6台账:仅L级写task-ledger.json;跨会话继承计数与预算;恢复优先读台账。
7资源:不自购;不重复无收益验证;QUOTA读不到=UNKNOWN。
8安全:不泄露/上传密钥Token Cookie密码隐私.env。
9免打扰:只问一个需用户定问题并附推荐;路径仅四条件可问。
10范围:不擅自扩大/不开后续阶段/不安排其他Agent。
11四态:DISCOVERED≠INSTALLED≠LOADED≠BEHAVIOR_VERIFIED;未验证不写成已支持。
12交接:熔断交当前宿主总控/派工方(取消ChatGPT单控绑定)。

## 必停(始终可见)
高风险必停:越权/生产真实数据/不可逆删除覆盖迁移/高风险权限变更/凭据隐私外传/新增费用超预算/实质业务冲突→停止并交派工方;安全门禁拒绝不是可绕过的技术问题。
全文见recovery.md §7.3。

## 收口
GOAL/DELIVERED/ACCEPTANCE/GAPS/REPOSITORY/FINAL_STATUS∈{PASS,PARTIAL,BLOCKED};不为PASS降验收或伪造。
