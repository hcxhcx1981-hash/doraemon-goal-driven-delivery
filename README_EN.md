# Doraemon Goal-Driven Delivery

**V1.1 · Authorize once. Deliver continuously. Verify with evidence. Stop within limits.**

[中文](README.md) · [Canonical rules in Chinese](SKILL.md) · [Installation](docs/INSTALLATION.md) · [Architecture](docs/ARCHITECTURE.md) · [Workflow](docs/WORKFLOW.md) · [Safety](docs/SAFETY.md)

Agents often interrupt users for routine choices because scope, authority, acceptance and stop conditions are unclear. This portable prompt protocol makes a complete, verifiable outcome the unit of work. Within an explicit authorization, the executor implements, tests, diagnoses, repairs and verifies continuously.

The user owns business goals and final product acceptance. ChatGPT owns planning, dispatch and technical arbitration. Execution agents own implementation, testing and evidence-based repairs. This repository provides collaboration instructions, not an automatic multi-agent scheduler or a permission sandbox. It does not promise unlimited autonomy or unattended operation.

## Repair limits

At most two evidence-backed repair rounds per root cause and four effective repair rounds for the entire task by default. Stricter limits win. Each repair records hypothesis, evidence, minimal change and acceptance method. Stop immediately without new evidence, on regressions, missing critical evidence, exhausted budgets or authorization conflicts. Renaming or splitting tasks and restarting sessions must not reset budgets.

Never retry indefinitely, purchase quota automatically or bypass production gates. Report `QUOTA=UNKNOWN` when quota cannot be read. On a fuse event, stop related work, preserve accepted artifacts and failure evidence, record attempted repairs, report PARTIAL/BLOCKED and return technical arbitration to ChatGPT.

## Use and acceptance

Follow the [PowerShell installation guide](docs/INSTALLATION.md), explicitly request the Skill and supply a bounded [task dispatch](examples/task-dispatch.md). CodeBuddy uses [inline rules](adapters/codebuddy/inline-rules.md). Development tasks also follow the separately installed local development guard. Verify actual outputs and report using the [acceptance template](examples/acceptance-report.md). Stop at acceptance or fuse preservation.

## Verification status

The four locally installed CX/AC/H/WB V1.1 files matched byte-for-byte. The canonical SKILL.md is preserved unchanged. The CB adapter retains its V1.1 rules; a categorical native-installation claim was replaced with UNVERIFIED. Static contract tests and a test-only fuse reference model are reproducible with `python -X utf8 -m unittest discover -s tests -v`. Scenario tests do not prove real-agent compliance or enforce permissions.

This CX session explicitly supplied the Skill. Automatic discovery and behavioral E2E for AC/H/WB/CB remain **UNVERIFIED**. Historical T1–T7 summaries lack reproducible fuse test sources and are not accepted as behavior evidence. See the Chinese README for GitHub-native architecture/state diagrams and the workflow document for rendering checks.

No runtime dependencies. Tests use Python's standard library. MIT applies to repository content only; third-party hosts, trademarks and external guards are not included.
