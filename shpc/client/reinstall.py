__author__ = "Vanessa Sochat"
__copyright__ = "Copyright 2021-2024, Vanessa Sochat"
__license__ = "MPL 2.0"

import shpc.utils
from shpc.logger import logger

def main(args, parser, extra, subparser):
    from shpc.main import get_client

    shpc.utils.ensure_no_extra(extra)

    cli = get_client(
        quiet=args.quiet,
        settings_file=args.settings_file,
        module_sys=args.module_sys,
        container_tech=args.container_tech,
    )

    # Update config settings on the fly
    cli.settings.update_params(args.config_params)

    # Add namespace
    name = cli.add_namespace(args.reinstall_recipe)
    
    # Reinstall the module
    reinstall(name, cli, args, complete=args.complete)

def reinstall(name, cli, args, complete=False):
    """
    Reinstall a specific version or all versions of a module.
    """
    # Check if the module or version is installed
    installed_versions = cli.list(return_modules=True).get(name.split(":")[0], [])

    if not installed_versions:
        logger.exit(f"You currently don't have '{name}' installed.\nTry: shpc install", 0)
    
    # Determine if a specific version is requested
    specific_version = ":" in name

    if specific_version and name.split(":")[1] not in installed_versions:
        logger.exit(f"You currently don't have '{name}' installed.\nTry: shpc install", 0)

    # Handle reinstallation logic
    if specific_version:
        print(f"Reinstalling {name}...")
        reinstall_version(name, cli, args, complete)
        logger.info(f"Successfully reinstalled of {name}.")
    else:
        print(f"Reinstalling all versions of {name}...")
        for version in installed_versions:
            version_name = f"{name}:{version}"
            reinstall_version(version_name, cli, args, complete)
        logger.info(f"Successfully reinstalled all versions of {name}.")


def reinstall_version(name, cli, args, complete):
    """
    Sub-function to handle the actual reinstallation
    """
    # Uninstallation process. Containers are kept by default except the user wants a complete reinstall
    if complete:
        cli.uninstall(name, force=True, keep_container=True)
    else:
        cli.uninstall(name, force=True, keep_container=False)

    # Installation
    cli.install(name, force=args.force, container_image=args.container_image, keep_path=args.keep_path)

    # Update the view if necessary
    if cli.settings.default_view and not args.no_view:
        cli.view_install(cli.settings.default_view, name, force=args.force, container_image=args.container_image)

    


