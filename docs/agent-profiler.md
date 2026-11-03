# Agent Profiler: goal and responsibilities

English | [中文](/docs/agent-profiler.zh.md)

This document states the goal and responsibilities of the Agent Profiler; it is the repository's most important development guidance.

## Goal

The Agent Profiler provides factual evidence for Agent efficiency optimization through execution cost analysis.

## Cost and efficiency

Given the same completed task and the same quality standard, cost consists of time cost and economic cost:

`C = aT + bM`

where `a` and `b` are weights and unit conversion factors specified by the user; economic cost currently means token billing.

Efficiency is defined as the reciprocal of the combined cost:

`E = 1 / C`

Lowering the combined cost therefore raises efficiency. The main optimization paths are shortening the execution critical path and reducing unnecessary input and output.

## The boundary of judgment

How to shorten the execution path safely, and which input and output can be reduced, usually require reasoning about the task goal, the execution context, and complex behavior analysis. Cost facts alone are not enough to make those judgments reliably.

## Responsibilities

The Agent Profiler's responsibilities are limited to:

1. **Cost measurement and attribution**: provide verifiable, traceable cost facts with an explicit measurement basis.
2. **Potential anomaly identification**: identify potential anomalies from objective facts and provide relevant evidence and optimization leads for investigation; the Profiler does not judge whether a process is necessary and does not evaluate efficiency directly.

Task-quality evaluation, efficiency analysis, and optimization decisions are made by humans or agents on the basis of the facts the Profiler provides.
