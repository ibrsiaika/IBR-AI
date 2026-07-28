"""
Agent Sandbox Configuration — PRD Section 22.1.

Defines the sandbox configuration for agent execution. Agents run in
containerized sandboxes with restricted network access, read-only
filesystems, and resource limits. The gVisor runtime class (ADR-0015)
provides kernel-level isolation by intercepting syscalls.

References:
    - PRD Section 22.1 (Security — Sandboxed Execution)
    - ADR-0015 (Container Runtime — containerd + gVisor)
    - PRD Section 100 (Low-Resource Inference)
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class SandboxConfig:
    """Configuration for agent sandboxing (PRD Section 22.1).

    Agents run in isolated containers with the following restrictions:
    - No network egress by default (allowlist for approved domains)
    - Read-only filesystem (writable only to designated directories)
    - Memory and CPU limits
    - Timeout to prevent infinite loops
    - gVisor runtime class for kernel-level isolation (ADR-0015)

    Attributes:
        network_egress: Whether network access is allowed (default: False).
        network_allowlist: List of allowed domains (if egress is True).
        filesystem_readonly: Whether the filesystem is read-only (default: True).
        writable_dirs: List of writable directories (if readonly is True).
        max_memory_mb: Maximum memory in MB (default: 512).
        max_cpu_percent: Maximum CPU usage percentage (default: 50).
        timeout_seconds: Execution timeout in seconds (default: 300).
        runtime_class: Container runtime class (default: "gvisor").
    """

    network_egress: bool = False
    network_allowlist: list[str] = field(default_factory=list)
    filesystem_readonly: bool = True
    writable_dirs: list[str] = field(default_factory=lambda: ["/tmp", "/work"])  # nosec B108 — config default, not actual file access
    max_memory_mb: int = 512
    max_cpu_percent: int = 50
    timeout_seconds: int = 300
    runtime_class: str = "gvisor"

    def to_kubernetes_annotations(self) -> dict[str, str]:
        """Convert to Kubernetes pod annotations.

        Returns:
            Dictionary of Kubernetes annotations for sandbox configuration.
        """
        return {
            "container.apparmor.security.beta.kubernetes.io/agent": "runtime/default",
            "container.seccomp.security.alpha.kubernetes.io/agent": "runtime/default",
            "scheduler.alpha.kubernetes.io/runtime-class": self.runtime_class,
        }

    def to_security_context(self) -> dict[str, object]:
        """Convert to Kubernetes security context.

        Returns:
            Dictionary suitable for a Kubernetes SecurityContext.
        """
        return {
            "runAsNonRoot": True,
            "runAsUser": 1000,
            "readOnlyRootFilesystem": self.filesystem_readonly,
            "allowPrivilegeEscalation": False,
            "capabilities": {
                "drop": ["ALL"],
                "add": [] if self.filesystem_readonly else ["CHOWN", "FOWNER"],
            },
            "resources": {
                "limits": {
                    "memory": f"{self.max_memory_mb}Mi",
                    "cpu": f"{self.max_cpu_percent}%",
                },
            },
        }

    def __repr__(self) -> str:
        return (
            f"<SandboxConfig(runtime={self.runtime_class}, "
            f"egress={self.network_egress}, readonly={self.filesystem_readonly})>"
        )
