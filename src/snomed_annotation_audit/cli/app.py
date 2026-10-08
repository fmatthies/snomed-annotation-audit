import logging
import pathlib
from typing import Optional, Union

import click

from ..hdf5_handling.metadata import format_hdf5_metadata_summary, inspect_hdf5_metadata
from ..pipelines import run_create_concept_id_dump, run_log_documents
from ..snomed import DumpMode, FilterMode
from ..snowstorm import build_endpoint, get_branches
from .logging import set_log_level
from .options import (
    click_log_level,
    click_server_options,
    create_concept_id_dump_options,
    log_documents_options,
)


@click.command()
@log_documents_options
def log_documents(
    process_path: str,
    lists_path: Optional[str],
    ip: str,
    port: Union[int, str],
    use_secure_protocol: bool,
    inception_username: Optional[str],
    inception_password: Optional[str],
    inception_project: Optional[str],
    log_level: str,
    keep_export: bool,
    omit_dump: bool,
    forbid_prompt: bool,
    annotation_type: tuple[str, ...],
    ignore_overlap_type: tuple[str, ...],
    ignore_overlap_mode: str,
    id_prefix: str,
    id_feature: str,
):
    """
    Analyze an INCEpTION project ZIP or remote export and report SNOMED CT
    annotations that violate the configured inclusion-list/exclusion-list HDF5 policy.
    """
    run_log_documents(
        process_path=process_path,
        lists_path=lists_path,
        ip=ip,
        port=port,
        use_secure_protocol=use_secure_protocol,
        inception_username=inception_username,
        inception_password=inception_password,
        inception_project=inception_project,
        log_level=log_level,
        keep_export=keep_export,
        omit_dump=omit_dump,
        forbid_prompt=forbid_prompt,
        annotation_type=annotation_type,
        ignore_overlap_type=ignore_overlap_type,
        ignore_overlap_mode=ignore_overlap_mode,
        id_prefix=id_prefix,
        id_feature=id_feature,
    )


@click.command()
@create_concept_id_dump_options
def create_concept_id_dump(
    root_code: str,
    rf2_zip: Optional[pathlib.Path],
    output: Optional[pathlib.Path],
    language: str,
    policy_date: Optional[str],
    rf2_view: str,
    use_secure_protocol: bool,
    port: Optional[int],
    ip: Optional[str],
    branch: Union[int, str],
    dump_mode: DumpMode,
    filter_list: Union[str, click.File],
    filter_mode: FilterMode,
    not_recursive: bool,
    force_overwrite: bool,
    force_overwrite_concepts: bool,
    log_level: str,
):
    """Create a SNOMED CT inclusion-list/exclusion-list HDF5 policy dump."""
    run_create_concept_id_dump(
        root_code=root_code,
        rf2_zip=rf2_zip,
        output=output,
        language=language,
        policy_date=policy_date,
        rf2_view=rf2_view,
        use_secure_protocol=use_secure_protocol,
        port=port,
        ip=ip,
        branch=branch,
        dump_mode=dump_mode,
        filter_list=filter_list,
        filter_mode=filter_mode,
        not_recursive=not_recursive,
        force_overwrite=force_overwrite,
        force_overwrite_concepts=force_overwrite_concepts,
        log_level=log_level,
    )


@click.command()
@click.argument(
    "hdf5_path",
    type=click.Path(exists=True, dir_okay=False, path_type=pathlib.Path),
)
@click.option(
    "--markdown",
    is_flag=True,
    help="Render the metadata summary as Markdown.",
)
def summarize_hdf5(hdf5_path: pathlib.Path, markdown: bool):
    """Print a concise metadata summary for a SNOMED postprocessing HDF5 file."""
    summary = inspect_hdf5_metadata(hdf5_path)
    click.echo(format_hdf5_metadata_summary(summary, markdown=markdown))


@click.command()
@click_server_options
@click_log_level
def list_branches(
    ip: str, port: Union[int, str], use_secure_protocol: bool, log_level: str
):
    """List all available Snowstorm branches."""
    set_log_level(log_level)
    endpoint_builder, host = build_endpoint(ip, port, use_secure_protocol)
    path_ids, _ = get_branches(endpoint_builder, host)
    pad = len(max([str(x) for x in path_ids.get("path").keys()], key=len))
    for _id, path in path_ids.get("path").items():
        print(f"{str(_id).ljust(pad, ' ')} : {path}")


@click.command()
def help_me():
    """Show available audit-oriented commands."""
    logging.info("Please use one of the command-specific --help screens.")
    print(
        "Please use one of the following commands:\n"
        "\n * log-critical-documents"
        "\n * create-concepts-dump"
        "\n * summarize-hdf5"
        "\n * list-branches"
        "\n\nEach command has a '--help' option, e.g. 'log-critical-documents --help'."
    )
