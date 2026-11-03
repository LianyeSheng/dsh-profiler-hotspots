# dsh-profiler

English | [中文](/README.zh.md)

dsh-profiler is a hotspot analysis tool for agent execution: it analyzes where a run spends time and tokens across steps, calls and context, and reports verifiable cost facts and potential anomaly leads.

The specific goal is quoted from [the project charter](/docs/agent-profiler.md): provide factual evidence for agent efficiency optimization through execution cost analysis. The profiler's responsibilities are limited to cost measurement and attribution and to identifying potential anomalies from objective facts; it does not judge whether a process is necessary and does not evaluate efficiency directly.

The project is in an early exploration stage: the goal and responsibility boundary are set, while the measurement basis, capability scope and delivery shape are still forming.
