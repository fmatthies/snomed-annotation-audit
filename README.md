# SNOMED Annotation Audit

Audit SNOMED CT annotations in INCEpTION/UIMA exports (XMI/JSON) against materialized inclusion-list/exclusion-list policy HDF5 files:

- critical document logging for concepts that are not on the inclusion list or are on the exclusion list;
- HDF5 policy creation from Snowstorm;
- HDF5 policy creation from SNOMED CT RF2 release ZIPs;
- Streamlit GUI for selecting inputs, reviewing grouped findings, and downloading reports.

> [!IMPORTANT]
> Every audit requires a policy HDF5 file containing the materialized inclusion and exclusion lists. You can create this file from a [SNOMED CT RF2 release ZIP](#create-hdf5-policy-file-from-rf2-release-zip) or, optionally, from a [Snowstorm server](#optionally-create-hdf5-policy-file-from-snowstorm). If you already have a suitable policy HDF5 file, you can proceed directly to the GUI or command-line workflow.

## Recommended: Run audits with the GUI

The Streamlit GUI is the easiest way to run an annotation audit. It supports:

- uploading an INCEpTION project export;
- uploading an inclusion-list/exclusion-list policy HDF5 file;
- selecting the annotation layers to audit;
- filtering and reviewing findings grouped by document and annotator;
- downloading JSON and Markdown reports.

Start the published Docker image with the included helper script:

```bash
./start-gui.sh
```

Then open <http://localhost:8501>.

Alternatively, run the GUI locally:

```bash
uv run streamlit run src/snomed_annotation_audit/gui/app.py
```

### GUI workflow

1. Upload an INCEpTION project ZIP.
2. Upload an existing policy HDF5 file, or [create one using the instructions below](#create-hdf5-policy-file-from-rf2-release-zip).
3. Select the annotation layers and run the policy check.
4. Review the grouped findings and download the reports.

## Command-line usage

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
The INCEpTION project export must include documents in the additional JSON or XMI format.
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

## Create HDF5 policy file from RF2 release ZIP

```bash
uv run create-concepts-dump \
  --zip /path/to/SnomedCT_Release.zip \
  --rf2-view snapshot \
  --policy-date YYYYMMDD \
  --output data/policy.hdf5 \
  --dump-mode version \
  --filter-list config/exclusion_list_filter_tags.txt \
  138875005
```

In Snapshot mode, `--policy-date` must match the release date of the selected RF2 Snapshot. Snapshot files cannot reconstruct an earlier date.

For RF2 Full releases, use:

```bash
uv run create-concepts-dump \
  --zip /path/to/SnomedCT_Full.zip \
  --rf2-view full \
  --policy-date YYYYMMDD \
  --output data/policy.hdf5 \
  --dump-mode version \
  --filter-list config/exclusion_list_filter_tags.txt \
  138875005
```

In RF2 ZIP mode, `--dump-mode version` is the default. Combined with `--filter-list`, it creates both policy views in one run: the positional root concept and its active descendants form the inclusion list, while the filter-list rules form the exclusion list. The filter list may contain semantic tags or SNOMED CT concept IDs. Semantic tags exclude matching active concepts; concept IDs exclude those concepts and their active descendants. The resulting concept indices are materialized in the HDF5; the original rules are not stored.

Use `--dump-mode semantic` when creating only the RF2 exclusion-list view. Add `--force-overwrite` when replacing an exclusion-list view that already exists in the output file.

## Optionally create HDF5 policy file from Snowstorm

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

## Docker images and helper scripts

The default image is hosted at:

```text
ghcr.io/fmatthies/snomed-annotation-audit/audit-image:<version>
```

The repository includes helper scripts for common Docker runs.

#### Start the GUI

Use `start-gui.sh` to run the default published GUI image:

```bash
./start-gui.sh
```

Defaults:

- image: `ghcr.io/fmatthies/snomed-annotation-audit/audit-image`
- version: `1.0.0`
- host port: `8501`

You can override the port and/or image version:

```bash
./start-gui.sh 8502
./start-gui.sh 8502 1.0.0
```

#### Log an INCEpTION project ZIP

Use `log-inception-docs.sh` to run `log-critical-documents` in Docker against an INCEpTION project ZIP stored in `./data`:

```bash
./log-inception-docs.sh PROJECT_EXPORT.zip
```

The script mounts local `./data` to `/app/data` in the container. Put the INCEpTION ZIP and policy HDF5 file in `./data`; generated reports are written back there. If `./data` contains exactly one `.hdf5` or `.h5` file, the script selects it automatically.

The second argument optionally selects the image version. If multiple HDF5 files exist, use the third argument to select the policy file:

```bash
./log-inception-docs.sh PROJECT_EXPORT.zip 1.0.0
./log-inception-docs.sh PROJECT_EXPORT.zip 1.0.0 policy.hdf5
```

Example direct Docker invocation:

```bash
docker run --rm -p 8501:8501 \
  ghcr.io/fmatthies/snomed-annotation-audit/audit-image:1.0.0 \
  start-gui
```
