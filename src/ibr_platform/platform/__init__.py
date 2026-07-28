"""
Platform package — Core platform code (PRD Section 32.2).

Contains:
    - runtime: IBR runtime (process management, lifecycle, health checks)
    - kernel: Resource management, sandboxing, IPC
    - scheduler: Task scheduler (plan execution, dependency resolution)
"""

__all__ = ["runtime", "kernel", "scheduler"]
