__author__ = "Vanessa Sochat"
__copyright__ = "Copyright 2021-2024, Vanessa Sochat"
__license__ = "MPL 2.0"

import shpc.utils
from shpc.logger import logger

def main(args, parser, extra, subparser):
    from shpc.main import get_client

    shpc.utils.ensure_no_extra(extra)

    cli = get_client(quiet=args.quiet, settings_file=args.settings_file)

    # Update config settings on the fly
    cli.settings.update_params(args.config_params)

    # One off custom registry, reload
    if args.registry:
        cli.settings.registry = [args.registry]
        cli.reload_registry()

    # Add namespace 
    name = cli.add_namespace(args.upgrade_recipe)

    # Load the container configuration for the specified software
    config = cli._load_container(name)

    # Retrieve the latest version
    latest_version_info = config.get('latest')
    if not latest_version_info:
        logger.exit(f"No latest version found for {name}")

    # Extract the latest version
    latest_version = list(latest_version_info.keys())[0]
    print(f"Latest version is: {latest_version}")

    # Extract the currently installed version
    current_version_info = cli.list(pattern=name, names_only=False, short=False)
    current_version = list(current_version_info.keys())[1]
    print(f"Your current version is: {current_version}")
