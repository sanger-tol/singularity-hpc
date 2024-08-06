__author__ = "Vanessa Sochat"
__copyright__ = "Copyright 2021-2024, Vanessa Sochat"
__license__ = "MPL 2.0"

import shpc.utils
from shpc.logger import logger

def main(args, parser, extra, subparser):
    import subprocess
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

    # Load the container configuration for the specified recipe
    config = cli._load_container(name)

    # Retrieve and extract the latest version from the container configuration
    latest_version_info = config.get('latest')
    if not latest_version_info:
        logger.exit(f"No latest version found for {name}")
    latest_version_tag = list(latest_version_info.keys())[0]
    print(f"Latest version is: {latest_version_tag}")

    # Retrieve and extract the currently installed version from the user's list of installed modules
    def get_current_version(name):
        try:
            result = subprocess.run(
                ['shpc', 'list', name],
                capture_output=True,
                text=True,
                check=True
            )
            output = result.stdout
            return output
        except subprocess.CalledProcessError as e:
            print(f"Failed to execute shpc list command: {e}")
            return None

    # Extract the currently installed version
    current_version_info = get_current_version(name)
    print(f"Your current version is: {current_version_info}")
    
    '''   
    def get_tag(output):
        parts = output.strip().split(':', 1)
        if len(parts) == 2:
            return parts[1].strip()
        return None
    '''
    


    

