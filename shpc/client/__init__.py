#!/usr/bin/env python

__author__ = "Vanessa Sochat"
__copyright__ = "Copyright 2021-2024, Vanessa Sochat"
__license__ = "MPL 2.0"

import argparse
import os
import sys

import shpc
from shpc.logger import setup_logger

from . import help


def get_parser():
    parser = argparse.ArgumentParser(
        description="Singularity Registry (HPC)",
        formatter_class=argparse.RawTextHelpFormatter,
    )

    # Global Variables
    parser.add_argument(
        "--debug",
        dest="debug",
        help="use verbose logging to debug.",
        default=False,
        action="store_true",
    )

    parser.add_argument(
        "--quiet",
        dest="quiet",
        help="suppress additional output.",
        default=False,
        action="store_true",
    )

    parser.add_argument(
        "--settings-file",
        dest="settings_file",
        help="custom path to settings file.",
    )

    # On the fly updates to config params
    parser.add_argument(
        "-c",
        dest="config_params",
        help=help.config_params,
        action="append",
    )

    parser.add_argument(
        "--version",
        dest="version",
        help="show software version.",
        default=False,
        action="store_true",
    )

    description = "actions for Singularity Registry HPC"
    subparsers = parser.add_subparsers(
        help="shpc actions",
        title="actions",
        description=description,
        dest="command",
    )

    # print version and exit
    subparsers.add_parser("version", description="show software version")

    # Local shell with client loaded
    shell = subparsers.add_parser(
        "shell",
        description=help.shell_description,
        formatter_class=argparse.RawTextHelpFormatter,
    )
    shell.add_argument(
        "module_name",
        help="optionally provide the container module name to shell into, with loaded.",
        nargs="?",
    )
    shell.add_argument(
        "--interpreter",
        "-i",
        dest="interpreter",
        help="python interpreter",
        choices=["ipython", "python", "bpython"],
        default="ipython",
    )

    # Install a known recipe from the registry
    install = subparsers.add_parser(
        "install",
        description=help.install_description,
        formatter_class=argparse.RawTextHelpFormatter,
    )
    install.add_argument("install_recipe", help="recipe to install")

    install.add_argument(
        "container_image",
        help="path to an existing container image for this software",
        nargs="?",
    )

    install.add_argument(
        "--keep-path",
        help="if installing a local container, do not copy the container - use the provided path.",
        default=False,
        action="store_true",
    )

    install.add_argument(
        "--no-view",
        dest="no_view",
        help="skip installing to the default view, if defined in settings.",
        action="store_true",
    )
    install.add_argument(
        "--force",
        "-f",
        dest="force",
        help="replace existing symlinks",
        default=False,
        action="store_true",
    )

    # Reinstall an installed software
    reinstall = subparsers.add_parser(
        "reinstall",
        description=help.reinstall_description,
        formatter_class=argparse.RawTextHelpFormatter,
    )
    reinstall.add_argument(
        "reinstall_recipe",
        help="recipe to reinstall",
        nargs="?",
    )

    reinstall.add_argument(
        "--update-containers",
        "-u",
        dest="update_containers",
        help="Also reinstall the containers (by default, containers are preserved)",
        default=False,
        action="store_true",
    )

    reinstall.add_argument(
        "--all",
        "-a",
        help="reinstall all installed software",
        action="store_true",
    )

    # List installed modules
    listing = subparsers.add_parser(
        "list",
        formatter_class=argparse.RawTextHelpFormatter,
        description=help.listing_description,
    )
    listing.add_argument("pattern", help="filter to a pattern", nargs="?")
    listing.add_argument(
        "--names-only", help="omit versions", default=False, action="store_true"
    )

    listing.add_argument(
        "--short",
        help="multiple tags per line for shorter length output.",
        default=False,
        action="store_true",
    )

    # List local containers and collections
    inspect = subparsers.add_parser(
        "inspect",
        description=help.inspect_description,
        formatter_class=argparse.RawTextHelpFormatter,
    )
    inspect.add_argument("module_name", help="module to inspect")
    inspect.add_argument(
        "--json", help="dump metadata as json", default=False, action="store_true"
    )
    inspect.add_argument(
        "--runscript", help="show the runscript", default=False, action="store_true"
    )

    # Get path to an image
    get = subparsers.add_parser(
        "get",
        formatter_class=argparse.RawTextHelpFormatter,
        description=help.get_description,
    )
    get.add_argument("module_name", help="the name of the module")
    get.add_argument(
        "-e",
        "--env-file",
        help="get the environment file path",
        default=False,
        action="store_true",
    )

    # Add a container direcly
    add = subparsers.add_parser(
        "add",
        formatter_class=argparse.RawTextHelpFormatter,
        description=help.add_description,
    )
    add.add_argument("container_uri", help="full path to container image file")
    add.add_argument(
        "module_id",
        help='desired identifier for module (e.g. "name/version"). Not required for docker)',
        nargs="?",
    )

    # Remove a container recipe
    remove = subparsers.add_parser(
        "remove", description="remove a container.yaml entry"
    )
    remove.add_argument(
        "module_id",
        help='desired identifier path to remove (e.g. "quay.io/biocontainers"). Leave out to remove all.',
        nargs="?",
    )

    check = subparsers.add_parser(
        "check",
        formatter_class=argparse.RawTextHelpFormatter,
        description=help.check_description,
    )
    check.add_argument("module_name", help="module to check (module:version)")

    view = subparsers.add_parser(
        "view",
        description=help.view_description,
        formatter_class=argparse.RawTextHelpFormatter,
    )
    view.add_argument("params", nargs="*", type=str, help="parameters for view command")
    view.add_argument(
        "--force",
        "-f",
        dest="force",
        help="force install or uninstall",
        default=False,
        action="store_true",
    )

    config = subparsers.add_parser(
        "config",
        description=help.config_description,
        formatter_class=argparse.RawTextHelpFormatter,
    )

    config.add_argument(
        "--central",
        dest="central",
        help="make edits to the central config file.",
        default=False,
        action="store_true",
    )

    config.add_argument(
        "params",
        nargs="*",
        help="parameters for config command",
        type=str,
    )
    # Generate markdown docs for a container registry entry
    docgen = subparsers.add_parser(
        "docgen",
        formatter_class=argparse.RawTextHelpFormatter,
        description=help.docgen_description,
    )
    docgen.add_argument("module_name", help="the module to generate docs for.")
    docgen.add_argument(
        "--registry-url", help="GitHub repository where registry can be found."
    )
    docgen.add_argument(
        "--branch",
        help="Branch that registry source files live (defaults to main)",
        default="main",
    )

    # Pull a nontraditional container type (e.g., github release asset)
    pull = subparsers.add_parser(
        "pull",
        formatter_class=argparse.RawTextHelpFormatter,
        description=help.pull_description,
    )
    pull.add_argument("uri", help="the unique resource identifier to pull")
    pull.add_argument("--path", help="A custom path to pull to (defaults to $PWD)")

    # Test a registry entry
    test = subparsers.add_parser(
        "test",
        formatter_class=argparse.RawTextHelpFormatter,
        description=help.test_description,
    )
    test.add_argument("module_name", help="the module to test")
    test.add_argument(
        "--template", help="a custom test.sh template to use.", default=None
    )
    test.add_argument(
        "--stage",
        help="keep the temporary install directory",
        default=False,
        action="store_true",
    )
    test.add_argument(
        "--test-exec",
        help="test executing commands",
        default=False,
        action="store_true",
    )
    test.add_argument(
        "--skip-module",
        help="Do not try testing the install module (e.g., lmod)",
        default=False,
        action="store_true",
    )
    test.add_argument(
        "--commands",
        help="Run tests section in container.yml",
        default=False,
        action="store_true",
    )

    # Uninstall a module, or a specific version
    uninstall = subparsers.add_parser(
        "uninstall",
        formatter_class=argparse.RawTextHelpFormatter,
        description=help.uninstall_description,
    )
    uninstall.add_argument(
        "--force",
        "-f",
        dest="force",
        help="don't prompt before deletion",
        default=False,
        action="store_true",
    )
    uninstall.add_argument(
        "uninstall_recipe", help="module to uninstall (module/version)", nargs="?"
    )
    uninstall.add_argument(
        "--all",
        "-a",
        dest="uninstall_all",
        help="uninstall all recipes",
        default=False,
        action="store_true",
    )

    # Upgrade a software to its latest version
    upgrade = subparsers.add_parser(
        "upgrade",
        description=help.upgrade_description,
        formatter_class=argparse.RawTextHelpFormatter,
    )
    upgrade.add_argument(
        "upgrade_recipe",
        help="software to upgrade",
        nargs="?",
    )

    upgrade.add_argument(
        "--all",
        "-a",
        help="upgrade all installed software.",
        dest="upgrade_all",
        action="store_true",
    )

    upgrade.add_argument(
        "--force",
        "-f",
        dest="force",
        help="force upgrade without prompting for confirmation to uninstall current version(s) or install latest version to view(s).",
        default=False,
        action="store_true",
    )

    # Update gets latest tags from OCI registries
    update = subparsers.add_parser(
        "update",
        formatter_class=argparse.RawTextHelpFormatter,
        description=help.update_description,
    )
    update.add_argument(
        "module_name", help="module to update (no version required)", nargs="?"
    )
    update.add_argument(
        "--filter",
        "-f",
        action="append",
        help="ignore container.yaml filters, run an update with this specific set",
        dest="filters",
    )

    # sync-registry gets latest files and non-existing containers from upstream shpc
    sync = subparsers.add_parser(
        "sync-registry",
        formatter_class=argparse.RawTextHelpFormatter,
        description=help.sync_description,
    )
    sync.add_argument(
        "module_name", help="module to add or sync from upstream", nargs="?"
    )
    sync.add_argument(
        "--tag",
        "-t",
        default="main",
        help="Upstream shpc repository reference (tag or branch) to upgrade from.",
    )
    sync.add_argument(
        "--config-file",
        "-c",
        dest="config_file",
        help="Provide a registries.yaml config file to coordinate the sync.",
    )
    sync.add_argument(
        "--all",
        "-a",
        dest="upgrade_all",
        help="Replace all existing files in sync set.",
        default=False,
        action="store_true",
    )
    sync.add_argument(
        "--existing-only",
        help="Do not add recipes that are not found in the local repository (only sync existing).",
        default=False,
        action="store_true",
    )

    for command in update, upgrade, sync:
        command.add_argument(
            "--dry-run",
            "-d",
            dest="dryrun",
            help="Do a dry run to view changes without performing them.",
            default=False,
            action="store_true",
        )

    # Add customization for each of container tech and module system
    for command in [
        add,
        check,
        docgen,
        get,
        inspect,
        install,
        listing,
        remove,
        reinstall,
        shell,
        test,
        uninstall,
        upgrade,
        view,
    ]:
        command.add_argument(
            "--module-sys",
            dest="module_sys",
            help="module system to use (defaults to lmod)",
            choices=["lmod", "tcl"],
            default=None,
        )
        command.add_argument(
            "--container-tech",
            dest="container_tech",
            help="container technology to use to override settings.yaml",
            choices=["singularity", "podman", "docker"],
            default=None,
        )

    namespace = subparsers.add_parser(
        "namespace",
        description=help.namespace_description,
        formatter_class=argparse.RawTextHelpFormatter,
    )
    namespace.add_argument(
        "namespace",
        help="command (use/unset) and if use, the namespace to set",
        nargs="*",
    )

    show = subparsers.add_parser(
        "show",
        formatter_class=argparse.RawTextHelpFormatter,
        description=help.show_description,
    )
    show.add_argument(
        "--versions", help="include versions", default=False, action="store_true"
    )
    show.add_argument(
        "name", help="the name of the container config to show", nargs="?"
    )
    show.add_argument(
        "-f",
        "--filter",
        help="filter results by regular expression",
        default=None,
        dest="filter_string",
    )
    show.add_argument(
        "-l",
        "--limit",
        help="set a limit for the number to show",
        default=None,
        type=int,
    )

    for command in docgen, show, add, remove, sync:
        command.add_argument(
            "--registry", help="GitHub repository or local path where registry lives."
        )
    return parser


def run_shpc():
    """
    run_shpc is the entrypoint to the singularity-hpc client.
    """

    parser = get_parser()

    def help(return_code=0):
        """print help, including the software version and active client
        and exit with return code.
        """

        version = shpc.__version__

        print("\nSingularity Registry (HPC) Client v%s" % version)
        parser.print_help()
        sys.exit(return_code)

    # If the user didn't provide any arguments, show the full help
    if len(sys.argv) == 1:
        help()

    # If an error occurs while parsing the arguments, the interpreter will exit with value 2
    args, extra = parser.parse_known_args()

    if args.debug is True:
        os.environ["MESSAGELEVEL"] = "DEBUG"

    # Show the version and exit
    if args.command == "version" or args.version:
        print(shpc.__version__)
        sys.exit(0)

    setup_logger(
        quiet=args.quiet,
        debug=args.debug,
    )

    # retrieve subparser (with help) from parser
    helper = None
    subparsers_actions = [
        action
        for action in parser._actions
        if isinstance(action, argparse._SubParsersAction)
    ]
    for subparsers_action in subparsers_actions:
        for choice, subparser in subparsers_action.choices.items():
            if choice == args.command:
                helper = subparser
                break

    # Does the user want a shell?
    if args.command == "add":
        from .add import main
    elif args.command == "config":
        from .config import main
    elif args.command == "check":
        from .check import main
    elif args.command == "docgen":
        from .docgen import main
    elif args.command == "get":
        from .get import main
    elif args.command == "install":
        from .install import main
    elif args.command == "inspect":
        from .inspect import main
    elif args.command == "list":
        from .listing import main
    elif args.command == "namespace":
        from .namespace import main
    elif args.command == "pull":
        from .pull import main
    elif args.command == "remove":
        from .remove import main
    elif args.command == "reinstall":
        from .reinstall import main
    elif args.command == "shell":
        from .shell import main
    elif args.command == "show":
        from .show import main
    elif args.command == "test":
        from .test import main
    elif args.command == "view":
        from .view import main
    elif args.command == "uninstall":
        from .uninstall import main
    elif args.command == "update":
        from .update import main
    elif args.command == "upgrade":
        from .upgrade import main
    elif args.command == "sync-registry":
        from .sync import sync_registry as main

    # Pass on to the correct parser
    return_code = 0
    try:
        main(args=args, parser=parser, extra=extra, subparser=helper)
        sys.exit(return_code)
    except UnboundLocalError:
        return_code = 1

    help(return_code)


if __name__ == "__main__":
    run_shpc()
