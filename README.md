# SNOMED Annotation Audit

Audit SNOMED CT annotations in INCEpTION/UIMA exports against materialized inclusion-list/exclusion-list policy HDF5 files:

- critical document logging for concepts that are not on the inclusion list or are on the exclusion list;
- HDF5 policy creation from Snowstorm;
- HDF5 policy creation from SNOMED CT RF2 release ZIPs;
- Streamlit UI for selecting inputs and running the audit.

## Commands

```text
log-critical-documents
create-concepts-dump
summarize-hdf5
list-branches
program-entry
```

## Audit INCEpTION annotations

```bash
uv run log-critical-documents \
  --lists-path /path/to/policy.hdf5 \
  /path/to/inception-json-or-xmi-export.zip
```

The audit reports annotations as critical when:

| Check | Critical when |
|---|---|
| Inclusion list | annotation SCTID is not in the inclusion-list policy view |
| Exclusion list | annotation SCTID is in the exclusion-list policy view |

The report is written next to the processed project ZIP as Markdown, masked Markdown, JSON, and CriticalFindings JSON.

Useful options:

```bash
--annotation-type gemtex.Concept
--annotation-type webanno.custom.Concept
--ignore-overlap-type webanno.custom.No_Human
--ignore-overlap-mode overlap
--id-feature id
--id-prefix http://snomed.info/id/
```

Use `--id-prefix ""` when annotations store plain SCTIDs.

## Create HDF5 from RF2 release ZIP

```bash
uv run create-concepts-dump \
  --zip /path/to/SnomedCT_Release.zip \
  --rf2-view snapshot \
  --policy-date YYYYMMDD \
  --output data/policy.hdf5 \
  138875005
```

For RF2 Full releases, use:

```bash
uv run create-concepts-dump \
  --zip /path/to/SnomedCT_Full.zip \
  --rf2-view full \
  --policy-date YYYYMMDD \
  --output data/policy.hdf5 \
  138875005
```

Exclusion list policy rules can be embedded with `--dump-mode semantic --filter-list <file-or-rule>`.

## Create HDF5 from Snowstorm

```bash
uv run create-concepts-dump \
  --ip SNOWSTORM_HOST \
  --port 8080 \
  --branch MAIN/YYYY-MM-DD \
  --dump-mode version
```

For an exclusion-list view:

```bash
uv run create-concepts-dump \
  --ip SNOWSTORM_HOST \
  --port 8080 \
  --branch MAIN/YYYY-MM-DD \
  --dump-mode semantic \
  --filter-list config/exclusion_list_filter_tags.txt
```

## Summarize HDF5 metadata

```bash
uv run summarize-hdf5 data/policy.hdf5 --markdown
```

## Streamlit GUI

```bash
uv run streamlit run src/snomed_annotation_audit/gui/app.py
```

The GUI supports selecting an INCEpTION project ZIP and a policy HDF5, choosing annotation layers, and running the inclusion-list/exclusion-list audit.
