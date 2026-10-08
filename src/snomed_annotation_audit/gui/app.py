"""Streamlit GUI entrypoint for annotation audit workflows."""

from __future__ import annotations

import streamlit as st
from snomed_annotation_audit.hdf5_handling.metadata import (
    format_hdf5_metadata_summary,
    inspect_hdf5_metadata,
)
from snomed_annotation_audit.gui.files import save_uploaded_file
from snomed_annotation_audit.gui.policy_tab import render_policy_tab
from snomed_annotation_audit.gui.sidebar import render_sidebar


st.set_page_config(page_title="GeMTeX SNOMED CT Annotation Audit", layout="wide")

st.title("SNOMED Annotation Audit")
st.write(
    "Check SNOMED CT annotations in INCEpTION exports against inclusion-list/exclusion-list "
    "policy HDF5 files, and create those HDF5 files from Snowstorm or RF2 release ZIPs."
)

inputs = render_sidebar()

st.info(
    "**Policy audit** — annotations are critical when their SNOMED CT code is not "
    "in the inclusion list or is present in the exclusion list for the selected HDF5 policy view.",
    icon="🎯",
)

if inputs.hdf5_file is not None:
    st.success(f"HDF5 selected: {getattr(inputs.hdf5_file, 'name', inputs.hdf5_file)}")
    try:
        inputs.hdf5_temp_path = save_uploaded_file(inputs.hdf5_file, ".hdf5")
        hdf5_summary = inspect_hdf5_metadata(inputs.hdf5_temp_path)
        st.caption(
            "HDF5 materialized view: "
            f"release date `{hdf5_summary.concepts_release_date or 'unknown'}`, "
            f"policy/view date `{hdf5_summary.concepts_policy_date or 'unknown'}`, "
            f"RF2 view `{hdf5_summary.concepts_rf2_view or 'unknown'}`."
        )
        with st.expander("HDF5 metadata summary", expanded=False):
            st.markdown(
                format_hdf5_metadata_summary(
                    hdf5_summary,
                    markdown=True,
                    include_path=False,
                    include_blacklist_rule_details=False,
                )
            )
    except Exception as exc:
        st.warning(f"Could not read HDF5 metadata: {exc}")

policy_tab, hdf5_tab = st.tabs(["Check annotations", "Create/update HDF5 policy"])

with policy_tab:
    render_policy_tab(inputs)

with hdf5_tab:
    st.markdown(
        "Use the CLI command `create-concepts-dump` to create HDF5 policy files from "
        "Snowstorm or from RF2 release ZIPs. The GUI currently exposes audit execution; "
        "RF2 ingestion remains available through the CLI."
    )
    st.code(
        "uv run create-concepts-dump --zip SnomedCT_Release.zip "
        "--policy-date YYYYMMDD --output data/policy.hdf5",
        language="bash",
    )
