"""Reusable Click option decorators."""

from __future__ import annotations

import pathlib

import click

from ..snomed import DumpMode, FilterMode
from .types import ClickEnumChoice, ClickUnion


def click_server_options(fnc):
    fnc = click.option(
        "--use-secure_protocol", is_flag=True, help="Whether to use 'https'."
    )(fnc)
    fnc = click.option(
        "--port",
        default=8080,
        help="Port on which the Snowstorm/INCEpTION instance runs.",
    )(fnc)
    fnc = click.option(
        "--ip",
        default="localhost",
        help="The IP address of the Snowstorm/INCEpTION instance.",
    )(fnc)
    return fnc


def click_inception_client_options(fnc):
    fnc = click.option(
        "--inception-project",
        default=None,
        help="The name of the INCEpTION project (URL slug).",
    )(fnc)
    fnc = click.option(
        "--inception-password",
        default=None,
        help="The password for the INCEpTION client (needs to have REMOTE role).",
    )(fnc)
    fnc = click.option(
        "--inception-username",
        default=None,
        help="The username for the INCEpTION client (needs to have REMOTE role).",
    )(fnc)
    return fnc


def click_log_level(fnc):
    fnc = click.option(
        "--log-level",
        default="INFO",
        type=click.Choice(
            ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"], case_sensitive=False
        ),
        help="The log level.",
    )(fnc)
    return fnc


def common_click_args(fnc):
    fnc = click.argument("root_code", default="138875005")(fnc)
    return fnc


def log_documents_options(fnc):
    """Apply options for the log-critical-documents command."""
    fnc = click.option(
        "--id-feature",
        default="id",
        show_default=True,
        help="Name of the annotation string feature that stores the SNOMED CT ID/SCTID.",
    )(fnc)
    fnc = click.option(
        "--id-prefix",
        default="http://snomed.info/id/",
        show_default=True,
        help=(
            "Prefix used before the SCTID in the annotation ID feature. "
            "Use an empty string for plain SCTIDs."
        ),
    )(fnc)
    fnc = click.option(
        "--ignore-overlap-mode",
        default="overlap",
        show_default=True,
        type=click.Choice(["overlap", "covered-by", "contains", "exact"], case_sensitive=False),
        help="How target annotations must match ignore-overlap annotations to be ignored.",
    )(fnc)
    fnc = click.option(
        "--ignore-overlap-type",
        multiple=True,
        default=("webanno.custom.No_Human",),
        show_default=True,
        help="Annotation layer/type whose overlapping spans suppress faulty-code findings on target annotations. Can be provided multiple times.",
    )(fnc)
    fnc = click.option(
        "--annotation-type",
        multiple=True,
        default=("gemtex.Concept", "webanno.custom.Concept"),
        show_default=True,
        help="Target annotation layer/type to check for SNOMED CT codes. Can be provided multiple times.",
    )(fnc)
    fnc = click.option(
        "--forbid-prompt",
        is_flag=True,
        help="Forbid prompting to select annotators manually; process all annotators instead.",
    )(fnc)
    fnc = click.option(
        "--omit-dump",
        is_flag=True,
        help="Omit creation of a dump of all concepts in the project and their offsets.",
    )(fnc)
    fnc = click.option(
        "--keep-export",
        is_flag=True,
        help="Keep the temporary exported INCEpTION project after processing.",
    )(fnc)
    fnc = click_log_level(fnc)
    fnc = click_inception_client_options(fnc)
    fnc = click_server_options(fnc)
    fnc = click.option(
        "--lists-path",
        default=None,
        help="The path to the policy HDF5 file. Defaults to bundled project data when available.",
    )(fnc)
    fnc = click.argument("process_path", type=click.STRING)(fnc)
    return fnc


def create_concept_id_dump_options(fnc):
    """Apply options for the create-concepts-dump command."""
    fnc = click_log_level(fnc)
    fnc = click.option(
        "--force-overwrite-concepts",
        is_flag=True,
        help="Rebuild an existing /concepts HDF5 extension. Independent from --force-overwrite.",
    )(fnc)
    fnc = click.option(
        "--force-overwrite",
        is_flag=True,
        help="Overwrite the selected inclusion-list/exclusion-list HDF5 policy group.",
    )(fnc)
    fnc = click.option(
        "--not-recursive",
        is_flag=True,
        help="Snowstorm mode only: do not resolve descendants recursively.",
    )(fnc)
    fnc = click.option(
        "--filter-mode",
        default=FilterMode.POSITIVE,
        type=ClickEnumChoice(FilterMode),
        help="Snowstorm semantic mode: include ('positive') or exclude ('negative') filtered codes/tags.",
    )(fnc)
    fnc = click.option(
        "--filter-list",
        "-fl",
        default=None,
        type=ClickUnion((click.STRING, "str"), (click.File, "file")),
        multiple=True,
        help="Codes/semantic tags, or a file with one code/tag per line, used for exclusion-list policy creation.",
    )(fnc)
    fnc = click.option(
        "--dump-mode",
        default=DumpMode.VERSION,
        type=ClickEnumChoice(DumpMode),
        help="Whether to create/update an inclusion-list ('version') or exclusion-list ('semantic') policy view.",
    )(fnc)
    fnc = click.option(
        "--branch",
        default=0,
        type=ClickUnion((click.INT, "int"), (click.STRING, "str")),
        help="Snowstorm mode: branch/release version. Defaults to the first branch found.",
    )(fnc)
    fnc = click.option(
        "--ip",
        default=None,
        help="Snowstorm mode: host/IP. Required together with --port when --zip is not used.",
    )(fnc)
    fnc = click.option(
        "--port",
        default=None,
        type=click.INT,
        help="Snowstorm mode: port. Required together with --ip when --zip is not used.",
    )(fnc)
    fnc = click.option(
        "--use-secure_protocol", is_flag=True, help="Snowstorm mode: use HTTPS."
    )(fnc)
    fnc = click.option(
        "--rf2-view",
        default="snapshot",
        show_default=True,
        type=click.Choice(["snapshot", "full"], case_sensitive=False),
        help="RF2 release view to ingest from the ZIP.",
    )(fnc)
    fnc = click.option(
        "--policy-date",
        default=None,
        help="RF2 ZIP mode: policy date as YYYYMMDD. Full mode reconstructs state at or before this date.",
    )(fnc)
    fnc = click.option(
        "--language",
        default="en",
        show_default=True,
        help="RF2 description language used in ZIP mode, e.g. 'en'.",
    )(fnc)
    fnc = click.option(
        "--output",
        default=None,
        type=click.Path(dir_okay=False, path_type=pathlib.Path),
        help="RF2 ZIP mode: output HDF5 path. Defaults to data/gemtex_snomedct_codes_<release-date>.hdf5.",
    )(fnc)
    fnc = click.option(
        "--zip",
        "rf2_zip",
        default=None,
        type=click.Path(exists=True, dir_okay=False, path_type=pathlib.Path),
        help="Path to a SNOMED CT RF2 release ZIP. If provided, HDF5 is generated from the ZIP instead of Snowstorm.",
    )(fnc)
    fnc = common_click_args(fnc)
    return fnc
