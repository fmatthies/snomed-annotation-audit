"""Central HDF5 policy-file access helpers.

This module keeps knowledge of the SNOMED postprocessing HDF5 layout in one
place. Higher-level code should prefer these helpers over opening HDF5 files and
addressing datasets directly.
"""

from __future__ import annotations

import dataclasses
import pathlib
from typing import Iterable, Optional, Sequence, Union

import h5py
import numpy as np


POLICY_VIEW_VERSION = "0"
POLICIES = ("whitelist", "blacklist")


@dataclasses.dataclass(frozen=True)
class PolicyData:
    """Policy concept codes and FSNs for one policy list."""

    codes: np.ndarray
    fsn: np.ndarray
    source: str


@dataclasses.dataclass(frozen=True)
class ConceptsData:
    """Compact /concepts data used by audit and policy views."""

    codes: tuple[str, ...]
    fsn: tuple[str, ...]
    active: np.ndarray
    code_to_index: dict[str, int]


@dataclasses.dataclass(frozen=True)
class HistoricalAssociationsData:
    """Compact /historical_associations data."""

    source_index: np.ndarray
    target_index: np.ndarray
    association_type_id: np.ndarray
    association_types: tuple[str, ...]
    active: np.ndarray
    effective_time: tuple[str, ...]
    refset_id: tuple[str, ...]


@dataclasses.dataclass(frozen=True)
class AncestorsData:
    """Compact active ancestor arrays under /concepts."""

    ancestor_index: np.ndarray
    ancestor_concept_index: np.ndarray
    ancestor_distance: np.ndarray


@dataclasses.dataclass(frozen=True)
class DepthToRootData:
    """Per-concept active hierarchy depth to root; -1 means unknown/unreachable."""

    min_depth_to_root: np.ndarray
    max_depth_to_root: np.ndarray


@dataclasses.dataclass(frozen=True)
class HistoricalIsARelationshipsData:
    """Inactive is-a relationship states used for historical ancestor fallback."""

    source_index: np.ndarray
    parent_index: np.ndarray
    effective_time: tuple[str, ...]


def has_concepts_extension(path: Union[str, pathlib.Path]) -> bool:
    path = pathlib.Path(path)
    if not path.exists() or not path.is_file():
        return False
    with h5py.File(path, "r") as h5_file:
        return "concepts" in h5_file


def read_policy_data(
    h5_file: h5py.File,
    policy: str,
    *,
    version: str = POLICY_VIEW_VERSION,
) -> Optional[PolicyData]:
    """Read policy codes/FSNs from legacy groups or compact policy views.

    Legacy layout is preferred for backwards compatibility when both layouts are
    present. Returns ``None`` if the requested policy is absent.
    """
    if policy in h5_file:
        group = h5_file[policy]
        if version in group and "codes" in group[version]:
            return PolicyData(
                codes=group[version]["codes"][:],
                fsn=group[version]["fsn"][:] if "fsn" in group[version] else np.asarray([], dtype="S"),
                source=f"/{policy}/{version}",
            )

    compact_path = f"policy_views/{policy}/{version}/concept_index"
    if compact_path in h5_file and "concepts/codes" in h5_file:
        concept_indices = h5_file[compact_path][:]
        concepts = h5_file["concepts"]
        return PolicyData(
            codes=concepts["codes"][:][concept_indices],
            fsn=concepts["fsn"][:][concept_indices] if "fsn" in concepts else np.asarray([], dtype="S"),
            source=f"/policy_views/{policy}/{version}",
        )

    return None


def require_paths(h5_file: h5py.File, paths: list[str], *, purpose: str) -> None:
    missing = [path for path in paths if path not in h5_file]
    if missing:
        raise ValueError(
            f"HDF5 file is not {purpose}; missing compact dataset(s): "
            + ", ".join(missing)
        )


def require_audit_ready(h5_file: h5py.File) -> None:
    require_paths(
        h5_file,
        [
            "concepts/codes",
            "concepts/fsn",
            "concepts/active",
            "policy_views/whitelist/0/concept_index",
            "policy_views/blacklist/0/concept_index",
        ],
        purpose="audit-ready",
    )


def has_active_ancestor_arrays(h5_file: h5py.File) -> bool:
    return all(
        path in h5_file
        for path in (
            "concepts/ancestors_index",
            "concepts/ancestor_concept_index",
            "concepts/ancestor_distance",
        )
    )


def has_depth_to_root_arrays(h5_file: h5py.File) -> bool:
    return all(
        path in h5_file
        for path in (
            "concepts/min_depth_to_root",
            "concepts/max_depth_to_root",
        )
    )


def has_historical_is_a_relationships(h5_file: h5py.File) -> bool:
    return all(
        path in h5_file
        for path in (
            "historical_is_a/source_index",
            "historical_is_a/parent_index",
            "historical_is_a/effective_time",
        )
    )


def read_concepts(h5_file: h5py.File) -> ConceptsData:
    require_paths(
        h5_file,
        ["concepts/codes", "concepts/fsn", "concepts/active"],
        purpose="concepts-ready",
    )
    codes = tuple(decode_array(h5_file["concepts/codes"][:]))
    fsn = tuple(decode_array(h5_file["concepts/fsn"][:]))
    active = np.asarray(h5_file["concepts/active"][:], dtype=bool)
    return ConceptsData(
        codes=codes,
        fsn=fsn,
        active=active,
        code_to_index={code: idx for idx, code in enumerate(codes)},
    )


def read_policy_indices(
    h5_file: h5py.File,
    policy: str,
    *,
    version: str = POLICY_VIEW_VERSION,
) -> frozenset[int]:
    return frozenset(
        int(idx) for idx in h5_file[f"policy_views/{policy}/{version}/concept_index"][:]
    )


def read_blacklist_rule_file(path: Union[str, pathlib.Path]) -> list[str]:
    """Read exclusion-list rules in the original filter-list format.

    Numeric lines are SNOMED CT roots whose descendants-or-self are excluded.
    Non-numeric lines are FSN semantic tags, e.g. ``procedure`` or
    ``qualifier value``.
    """
    return [
        line.strip()
        for line in pathlib.Path(path).read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def split_blacklist_rules(rules: Iterable[str]) -> tuple[list[str], list[str]]:
    cleaned = [str(rule).strip() for rule in rules if str(rule).strip()]
    return (
        [rule for rule in cleaned if rule.isdigit()],
        [rule for rule in cleaned if not rule.isdigit()],
    )


def resolve_blacklist_rule_indices(
    h5_file: h5py.File,
    rules: Iterable[str],
) -> frozenset[int]:
    """Resolve runtime exclusion-list rules to concept indices for a compact HDF5.

    This mirrors the RF2 exclusion-list input format: SCTID roots exclude the root
    concept and all descendants; non-numeric entries exclude concepts whose
    FSN semantic tag equals the entry.

    Keep these semantics aligned with embedded exclusion-list creation in
    ``snomed_annotation_audit.release_ingestion.hdf5_writer.write_compact_hdf5_from_rf2``.
    The implementations use different traversal backends: runtime resolution uses
    compact HDF5 ancestor arrays, while RF2 ingestion uses the active RF2 parent map.
    """
    root_codes, semantic_tags = split_blacklist_rules(rules)
    if not root_codes and not semantic_tags:
        return frozenset()
    concepts = read_concepts(h5_file)
    indices: set[int] = set()
    if semantic_tags:
        tag_set = set(semantic_tags)
        indices.update(
            idx for idx, tag in enumerate(_concept_semantic_tags(h5_file, concepts.fsn))
            if tag in tag_set
        )
    if root_codes:
        indices.update(_descendant_or_self_indices(h5_file, concepts.code_to_index, root_codes))
    return frozenset(indices)


def _concept_semantic_tags(h5_file: h5py.File, fsn_values: Sequence[str]) -> tuple[str, ...]:
    if "concepts/semantic_tag_id" in h5_file and "concepts/semantic_tags" in h5_file:
        tags = tuple(decode_array(h5_file["concepts/semantic_tags"][:]))
        return tuple(tags[int(tag_id)] for tag_id in h5_file["concepts/semantic_tag_id"][:])
    return tuple(_semantic_tag_from_fsn(fsn) for fsn in fsn_values)


def _semantic_tag_from_fsn(fsn: str) -> str:
    text = str(fsn or "")
    if "(" not in text or not text.endswith(")"):
        return ""
    return text.rsplit("(", 1)[1][:-1].strip()


def _descendant_or_self_indices(
    h5_file: h5py.File,
    code_to_index: dict[str, int],
    root_codes: Iterable[str],
) -> set[int]:
    root_indices = {code_to_index[code] for code in root_codes if code in code_to_index}
    if not root_indices:
        return set()
    if not has_active_ancestor_arrays(h5_file):
        raise ValueError(
            "Runtime exclusion-list SCTID rules require compact ancestor arrays in the HDF5. "
            "Rebuild the HDF5 with ancestor support or use semantic-tag rules only."
        )
    ancestors = read_active_ancestors(h5_file)
    descendants = set(root_indices)
    for concept_idx in range(len(ancestors.ancestor_index)):
        start, count = ancestors.ancestor_index[concept_idx]
        concept_ancestors = ancestors.ancestor_concept_index[int(start): int(start) + int(count)]
        if any(int(ancestor_idx) in root_indices for ancestor_idx in concept_ancestors):
            descendants.add(concept_idx)
    return descendants


def read_active_ancestors(h5_file: h5py.File) -> AncestorsData:
    require_paths(
        h5_file,
        [
            "concepts/ancestors_index",
            "concepts/ancestor_concept_index",
            "concepts/ancestor_distance",
        ],
        purpose="active-ancestor-ready",
    )
    concepts = h5_file["concepts"]
    return AncestorsData(
        ancestor_index=np.asarray(concepts["ancestors_index"][:], dtype=np.int64),
        ancestor_concept_index=np.asarray(concepts["ancestor_concept_index"][:], dtype=np.int64),
        ancestor_distance=np.asarray(concepts["ancestor_distance"][:], dtype=np.int64),
    )


def read_depth_to_root(h5_file: h5py.File) -> DepthToRootData:
    require_paths(
        h5_file,
        ["concepts/min_depth_to_root", "concepts/max_depth_to_root"],
        purpose="depth-to-root-ready",
    )
    concepts = h5_file["concepts"]
    return DepthToRootData(
        min_depth_to_root=np.asarray(concepts["min_depth_to_root"][:], dtype=np.int64),
        max_depth_to_root=np.asarray(concepts["max_depth_to_root"][:], dtype=np.int64),
    )


def read_historical_associations(h5_file: h5py.File) -> HistoricalAssociationsData:
    require_paths(
        h5_file,
        [
            "historical_associations/source_index",
            "historical_associations/target_index",
            "historical_associations/association_type_id",
            "historical_associations/association_types",
            "historical_associations/effective_time",
            "historical_associations/active",
            "historical_associations/refset_id",
        ],
        purpose="historical-association-ready",
    )
    hist = h5_file["historical_associations"]
    return HistoricalAssociationsData(
        source_index=np.asarray(hist["source_index"][:], dtype=np.int64),
        target_index=np.asarray(hist["target_index"][:], dtype=np.int64),
        association_type_id=np.asarray(hist["association_type_id"][:], dtype=np.int64),
        association_types=tuple(decode_array(hist["association_types"][:])),
        active=np.asarray(hist["active"][:], dtype=bool),
        effective_time=tuple(decode_array(hist["effective_time"][:])),
        refset_id=tuple(decode_array(hist["refset_id"][:])),
    )


def read_historical_is_a_relationships(h5_file: h5py.File) -> HistoricalIsARelationshipsData:
    require_paths(
        h5_file,
        [
            "historical_is_a/source_index",
            "historical_is_a/parent_index",
            "historical_is_a/effective_time",
        ],
        purpose="historical-is-a-ready",
    )
    group = h5_file["historical_is_a"]
    return HistoricalIsARelationshipsData(
        source_index=np.asarray(group["source_index"][:], dtype=np.int64),
        parent_index=np.asarray(group["parent_index"][:], dtype=np.int64),
        effective_time=tuple(decode_array(group["effective_time"][:])),
    )


def decode_array(values) -> list[str]:
    decoded = []
    for value in values:
        if isinstance(value, (bytes, bytearray)):
            decoded.append(value.decode("utf-8"))
        else:
            decoded.append(str(value))
    return decoded
