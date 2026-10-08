"""Compatibility entrypoint for legacy console-script imports.

The Click command implementations live in :mod:`snomed_annotation_audit.cli.app`.
This module intentionally re-exports the audit-oriented commands so older
references such as ``snomed_annotation_audit.main:log_documents`` continue to
work.
"""

from __future__ import annotations

from .cli.app import (  # noqa: F401
    create_concept_id_dump,
    help_me,
    list_branches,
    log_documents,
    summarize_hdf5,
)

__all__ = [
    "log_documents",
    "create_concept_id_dump",
    "summarize_hdf5",
    "list_branches",
    "help_me",
]


if __name__ == "__main__":
    help_me(["--help"])
