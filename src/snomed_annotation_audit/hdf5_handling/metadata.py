"""Concise metadata summaries for audit-only SNOMED HDF5 policy files."""

from __future__ import annotations

import dataclasses
import pathlib
from typing import Any, Optional, Union

import h5py
import numpy as np


@dataclasses.dataclass(frozen=True)
class Hdf5MetadataSummary:
    path: pathlib.Path
    has_concepts: bool
    concept_count: Optional[int] = None
    active_concept_count: Optional[int] = None
    concepts_policy_date: Optional[str] = None
    concepts_release_date: Optional[str] = None
    concepts_rf2_view: Optional[str] = None
    policy_view_counts: tuple[tuple[str, str, int], ...] = ()

    @property
    def audit_ready(self) -> bool:
        return (
            self.has_concepts
            and self.concept_count is not None
            and self.active_concept_count is not None
            and any(policy == "whitelist" for policy, _, _ in self.policy_view_counts)
            and any(policy == "blacklist" for policy, _, _ in self.policy_view_counts)
        )


def inspect_hdf5_metadata(path: Union[str, pathlib.Path]) -> Hdf5MetadataSummary:
    path = pathlib.Path(path)
    with h5py.File(path, "r") as h5_file:
        has_concepts = "concepts" in h5_file
        concept_count = None
        active_concept_count = None
        concepts_policy_date = None
        concepts_release_date = None
        concepts_rf2_view = None

        if has_concepts:
            concepts = h5_file["concepts"]
            if "codes" in concepts:
                concept_count = int(concepts["codes"].shape[0])
            if "active" in concepts:
                active_concept_count = int(np.count_nonzero(concepts["active"][:]))
            concepts_policy_date = _attr(concepts, "policy_date")
            concepts_release_date = _attr(concepts, "release_date")
            concepts_rf2_view = _attr(concepts, "rf2_view")

        policy_view_counts = []
        if "policy_views" in h5_file:
            policy_views = h5_file["policy_views"]
            for policy in sorted(policy_views.keys()):
                for view_name in sorted(policy_views[policy].keys()):
                    view = policy_views[policy][view_name]
                    if "concept_index" in view:
                        policy_view_counts.append(
                            (policy, view_name, int(view["concept_index"].shape[0]))
                        )

    return Hdf5MetadataSummary(
        path=path,
        has_concepts=has_concepts,
        concept_count=concept_count,
        active_concept_count=active_concept_count,
        concepts_policy_date=concepts_policy_date,
        concepts_release_date=concepts_release_date,
        concepts_rf2_view=concepts_rf2_view,
        policy_view_counts=tuple(policy_view_counts),
    )


def format_hdf5_metadata_summary(
    summary: Hdf5MetadataSummary,
    *,
    markdown: bool = False,
    include_path: bool = True,
    include_blacklist_rule_details: bool = True,
) -> str:
    del include_blacklist_rule_details  # retained for compatibility with callers
    lines = []
    if markdown:
        lines.append("### HDF5 metadata summary")
    else:
        lines.append("HDF5 metadata summary")
    if include_path:
        lines.append(f"- File: `{summary.path}`" if markdown else f"- File: {summary.path}")
    lines.extend(
        [
            f"- Audit-ready: {_yes_no(summary.audit_ready)}",
            f"- Concepts: {_count(summary.concept_count)}"
            + (
                f" ({summary.active_concept_count:,} active at policy date)"
                if summary.active_concept_count is not None
                else ""
            ),
            f"- Release date: {summary.concepts_release_date or 'unknown'}",
            f"- Policy date: {summary.concepts_policy_date or 'unknown'}",
            f"- RF2 view: {summary.concepts_rf2_view or 'unknown'}",
        ]
    )
    if summary.policy_view_counts:
        lines.append("- Compact policy views:")
        for policy, view_name, count in summary.policy_view_counts:
            lines.append(f"  - {_format_policy_label(policy)}/{view_name}: {count:,} concepts")
    else:
        lines.append("- Compact policy views: missing")
    return "\n".join(lines) + "\n"


def _format_policy_label(policy: str) -> str:
    if policy == "whitelist":
        return "inclusion list"
    if policy == "blacklist":
        return "exclusion list"
    return policy


def _attr(group: h5py.Group, name: str) -> Optional[str]:
    if name not in group.attrs:
        return None
    value: Any = group.attrs[name]
    if isinstance(value, (bytes, bytearray)):
        return value.decode("utf-8")
    return str(value)


def _count(value: Optional[int]) -> str:
    return "unknown" if value is None else f"{value:,}"


def _yes_no(value: bool) -> str:
    return "yes" if value else "no"
