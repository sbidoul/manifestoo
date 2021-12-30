from pathlib import Path
from typing import List, Optional

import typer

from . import echo
from .commands.check_dev_status import check_dev_status_command
from .commands.check_licenses import check_licenses_command
from .commands.list import list_command
from .commands.list_depends import list_depends_command
from .commands.list_external_dependencies import list_external_dependencies_command
from .commands.tree import tree_command
from .core_addons import get_core_addons
from .git import get_branch_modified_addons
from .odoo_series import OdooSeries, detect_from_addons_set
from .options import MainOptions
from .utils import ensure_odoo_series, not_implemented, print_list
from .version import __version__

app = typer.Typer()


def version_callback(value: bool) -> None:
    if value:
        typer.echo(f"manifestoo version {__version__}")
        raise typer.Exit()


@app.callback()
def callback(
    ctx: typer.Context,
    select_addons_dirs: Optional[List[Path]] = typer.Option(
        None,
        "--select-addons-dir",
        "-d",
        exists=True,
        file_okay=False,
        dir_okay=True,
        help=(
            "Select all installable addons found in this directory. "
            "This option may be repeated. "
            "The directories selected with this options are "
            "automatically added to the addons search path."
        ),
        show_default=False,
    ),
    select_git_modified: str = typer.Option(
        None,
        "--select-git-modified",
        "-g",
        help=(
            "Select all addons modified on current branch,"
            " relative to the given branch."
        ),
    ),
    select_include: Optional[str] = typer.Option(
        None,
        "--select-include",
        "--select",
        metavar="addon1,addon2,...",
        help=(
            "Comma separated list of addons to select. "
            "These addons will be searched in the addons path."
        ),
    ),
    select_exclude: Optional[str] = typer.Option(
        None,
        metavar="addon1,addon2,...",
        help=(
            "Comma separated list of addons to exclude from selection. "
            "This option is useful in combination with `--select-addons-dir`."
        ),
    ),
    select_core_addons: bool = typer.Option(
        False,
        "--select-core-addons",
        help="Select the Odoo core addons (CE and EE) for the given series.",
        show_default=False,
    ),
    addons_path: Optional[str] = typer.Option(
        None,
        help="Expand addons path with this comma separated list of directories.",
    ),
    addons_path_from_import_odoo: bool = typer.Option(
        True,
        help=(
            "Expand addons path by trying to `import odoo` and "
            "looking at `odoo.addons.__path__`. This option is useful when "
            "addons have been installed with pip."
        ),
    ),
    addons_path_python: str = typer.Option(
        "python",
        "--addons-path-python",
        show_default=False,
        metavar="PYTHON",
        help=(
            "The python executable to use when importing `odoo.addons.__path__`. "
            "Defaults to the `python` executable found in PATH."
        ),
    ),
    addons_path_from_odoo_cfg: Optional[Path] = typer.Option(
        None,
        exists=True,
        file_okay=True,
        dir_okay=False,
        readable=True,
        envvar="ODOO_RC",
        help=(
            "Expand addons path by looking into the provided Odoo configuration file. "
        ),
    ),
    separator: str = typer.Option(
        default=None,
        hidden=True,  # deprecated
    ),
    odoo_series: Optional[OdooSeries] = typer.Option(
        None,
        envvar=["ODOO_VERSION", "ODOO_SERIES"],
        help="Odoo series to use, in case it is not autodetected from addons version.",
    ),
    verbose: int = typer.Option(
        0,
        "--verbose",
        "-v",
        count=True,
        show_default=False,
    ),
    quiet: int = typer.Option(
        0,
        "--quiet",
        "-q",
        count=True,
        show_default=False,
    ),
    version: Optional[bool] = typer.Option(
        None,
        "--version",
        callback=version_callback,
        is_eager=True,
    ),
) -> None:
    """Reason about Odoo addons manifests.

    The `--select-*` options of this command select addons on which the
    subcommands will act. The `--addons-path` options provide locations to
    search for addons.

    Run `manifestoo <subcommand> --help` for more options.
    """
    echo.verbosity += verbose
    echo.verbosity -= quiet
    main_options = MainOptions()
    if separator:
        echo.warning(
            "--separator is deprecated as a global option. "
            "Please use the same option of list, list-depends."
        )
        main_options.separator = separator
    # resolve addons_path
    if select_addons_dirs:
        main_options.addons_path.extend_from_addons_dirs(select_addons_dirs)
    if addons_path:
        main_options.addons_path.extend_from_addons_path(addons_path)
    if addons_path_from_import_odoo:
        main_options.addons_path.extend_from_import_odoo(addons_path_python)
    if addons_path_from_odoo_cfg:
        main_options.addons_path.extend_from_odoo_cfg(addons_path_from_odoo_cfg)
    echo.info(str(main_options.addons_path), bold_intro="Addons path: ")
    # populate addons_set
    main_options.addons_set.add_from_addons_dirs(main_options.addons_path)
    echo.info(str(main_options.addons_set), bold_intro="Addons set: ")
    # Odoo series
    if odoo_series:
        main_options.odoo_series = odoo_series
    else:
        main_options.odoo_series = detect_from_addons_set(main_options.addons_set)
    # addons selection
    if select_addons_dirs:
        main_options.addons_selection.add_addons_dirs(select_addons_dirs)
    if select_git_modified:
        modified_addons = get_branch_modified_addons(
            select_git_modified, main_options.addons_path
        )
        main_options.addons_selection.add_addon_names(",".join(modified_addons))
    if select_include:
        main_options.addons_selection.add_addon_names(select_include)
    if select_exclude:
        main_options.addons_selection.remove_addon_names(select_exclude)
    if select_core_addons:
        ensure_odoo_series(main_options.odoo_series)
        assert main_options.odoo_series
        main_options.addons_selection.update(get_core_addons(main_options.odoo_series))
    if main_options.addons_selection:
        echo.info(str(main_options.addons_selection), bold_intro="Addons selection: ")
    else:
        echo.notice("No addon selected, please use one of the --select options.")
    echo.info(f"{main_options.odoo_series}", bold_intro="Odoo series: ")
    # pass main options to commands
    ctx.obj = main_options


@app.command()
def list(
    ctx: typer.Context,
    separator: Optional[str] = typer.Option(
        None,
        help="Separator charater to use (by default, print one item per line).",
    ),
) -> None:
    """Print the selected addons."""
    main_options: MainOptions = ctx.obj
    result = list_command(main_options.addons_selection)
    print_list(result, separator or main_options.separator or "\n")


@app.command()
def list_depends(
    ctx: typer.Context,
    separator: Optional[str] = typer.Option(
        None,
        help="Separator charater to use (by default, print one item per line).",
    ),
    transitive: bool = typer.Option(
        False,
        "--transitive",
        help="Print all transitive dependencies.",
        show_default=False,
    ),
    include_selected: bool = typer.Option(
        False,
        "--include-selected",
        help="Print the selected addons along with their dependencies.",
        show_default=False,
    ),
    ignore_missing: bool = typer.Option(
        False,
        "--ignore-missing",
        help=(
            "Do not fail if dependencies are not found in addons path. "
            "This only applies to top level (selected) addons "
            "and transitive dependencies."
        ),
        show_default=False,
    ),
    as_pip_requirements: bool = typer.Option(
        False,
        "--as-pip-requirements",
        show_default=False,
    ),
) -> None:
    """Print the dependencies of selected addons."""
    main_options: MainOptions = ctx.obj
    if as_pip_requirements:
        not_implemented("--as-pip-requirement")
    result, missing = list_depends_command(
        main_options.addons_selection,
        main_options.addons_set,
        transitive,
        include_selected,
    )
    if missing and not ignore_missing:
        echo.error("not found in addons path: " + ",".join(sorted(missing)))
        raise typer.Abort()
    print_list(
        result,
        separator or main_options.separator or "\n",
    )


@app.command()
def list_external_dependencies(
    ctx: typer.Context,
    kind: str = typer.Argument(
        ...,
        help="Kind of external dependency, such as `python` or `deb`.",
    ),
    separator: Optional[str] = typer.Option(
        None,
        help="Separator charater to use (by default, print one item per line).",
    ),
    transitive: bool = typer.Option(
        False,
        "--transitive",
        help="Print external dependencies of all transitive dependent addons.",
        show_default=False,
    ),
    ignore_missing: bool = typer.Option(
        False,
        "--ignore-missing",
        help=(
            "Do not fail if dependencies are not found in addons path. "
            "This only applies to top level (selected) addons "
            "and transitive dependencies."
        ),
        show_default=False,
    ),
) -> None:
    """Print the external dependencies of selected addons."""
    main_options: MainOptions = ctx.obj
    result, missing = list_external_dependencies_command(
        main_options.addons_selection,
        main_options.addons_set,
        kind,
        transitive,
    )
    if missing and not ignore_missing:
        echo.error("not found in addons path: " + ",".join(sorted(missing)))
        raise typer.Abort()
    print_list(
        result,
        separator or main_options.separator or "\n",
    )


@app.command()
def check_licenses(
    ctx: typer.Context,
    transitive: bool = typer.Option(
        False,
        "--transitive",
        help="Also check transitive dependencies.",
        show_default=False,
    ),
) -> None:
    """Check license compatibility.

    Check that selected addons only depend on addons with compatible
    licenses.
    """
    main_options: MainOptions = ctx.obj
    ensure_odoo_series(main_options.odoo_series)
    assert main_options.odoo_series
    errors = check_licenses_command(
        main_options.addons_selection,
        main_options.addons_set,
        transitive,
        main_options.odoo_series,
    )
    if errors:
        echo.error("\n".join(errors), err=False)
        raise typer.Exit(1)


@app.command()
def check_dev_status(
    ctx: typer.Context,
    transitive: bool = typer.Option(
        False,
        "--transitive",
        help="Also check transitive dependencies.",
        show_default=False,
    ),
    default_dev_status: Optional[str] = None,
) -> None:
    """Check development status compatibility.

    Check that selected addons only depend on addons that have an equal
    or higher development status.
    """
    main_options: MainOptions = ctx.obj
    ensure_odoo_series(main_options.odoo_series)
    assert main_options.odoo_series
    errors = check_dev_status_command(
        main_options.addons_selection,
        main_options.addons_set,
        default_dev_status,
        transitive,
        main_options.odoo_series,
    )
    if errors:
        echo.error("\n".join(errors), err=False)
        raise typer.Exit(1)


@app.command()
def tree(
    ctx: typer.Context,
    fold_core_addons: bool = typer.Option(
        False,
        "--fold-core-addons",
        help="Do not expand dependencies of core Odoo addons.",
        show_default=False,
    ),
) -> None:
    """Print the dependency tree of selected addons."""
    main_options: MainOptions = ctx.obj
    ensure_odoo_series(main_options.odoo_series)
    assert main_options.odoo_series
    tree_command(
        main_options.addons_selection,
        main_options.addons_set,
        main_options.odoo_series,
        fold_core_addons,
    )
