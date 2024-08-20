__author__ = "Vanessa Sochat"
__copyright__ = "Copyright 2021-2024, Vanessa Sochat"
__license__ = "MPL 2.0"

import shpc.utils
from shpc.logger import logger
import subprocess

def main(args, parser, extra, subparser):
    from shpc.main import get_client
    shpc.utils.ensure_no_extra(extra)

    cli = get_client(quiet=args.quiet, settings_file=args.settings_file)

    # Update config settings on the fly
    cli.settings.update_params(args.config_params)

    if args.preview:
        installed_modules = cli.list(return_modules=True)
        upgrades_available = {}
        for module in installed_modules.keys():
            upgrade_info = upgrade(module, cli, args, preview=True)
            if upgrade_info:
                upgrades_available.update(upgrade_info)
        
        if upgrades_available:
            print("These are the latest versions available for your modules:")
            for module, version in upgrades_available.items():
                print(f"{module}: {version}")
        else:
            print("No upgrade needed. All your modules are up to date.")

    elif args.upgrade_all:
        # Upgrade all installed modules
        installed_modules = cli.list(return_modules=True)
        print("Checking your installed modules for version updates...")
        outdated_modules = []
        for module in installed_modules.keys():
            upgrade_info = upgrade(module, cli, args, preview=True)
            if upgrade_info:
                outdated_modules.append(module)

        # Get the number of available module upgrades
        num_outdated = len(outdated_modules)

        # Perform upgrade on all outdated modules
        if num_outdated == 0:
            print("No upgrade needed. All your modules are up to date.")
        else:
            print(f"Found {num_outdated} outdated module(s)")
            for module in outdated_modules:
                upgrade(module, cli, args)
            print("All your modules are now up to date.")

    else:
        # Upgrade a specific installed module
        upgrade(args.upgrade_recipe, cli, args)

def upgrade(name, cli, args, preview=False):
    """
    Upgrade a module to its latest version. Or preview available upgrades from the user's module list
    """
    # Add namespace 
    name = cli.add_namespace(name)

    def get_latest_version(config):
        '''
        Retrieve the latest version tag from the container configuration.
        '''
        latest_version_info = config.get('latest')
        if not latest_version_info:
            logger.exit(f"No latest version found for {name}")
        
        # Extract the latest version tag
        latest_version_tag = list(latest_version_info.keys())[0]
        return latest_version_tag

    def get_current_version(recipe):
        '''
        Retrieve the current version from the user's list of installed modules
        '''
        try:
            result = subprocess.run(
                ['shpc', 'list', recipe],
                capture_output=True,
                text=True,
                check=True
            )
            output = result.stdout
            return output
        except subprocess.CalledProcessError as e:
            print(f"Failed to execute shpc list command: {e}")
            return None
        
    def get_tag(output):
        '''
        Retrieve the current version tag from the current version
        '''
        parts = output.strip().split(':', 1)
        if len(parts) == 2:
            return parts[1].strip()
        return None
    
    # Load the container configuration for the specified recipe
    config = cli._load_container(name)

    #Store the latest version and current version tags
    current_version_info = get_current_version(name)
    latest_version_tag = get_latest_version(config)
    current_version_tag = get_tag(current_version_info)

    # Compare the latest version with the user's installed version
    if latest_version_tag == current_version_tag:
        if preview:
            return None  # No upgrade available
        print("You have the latest version of " + name + " installed already")
    else:
        if preview:
            return {name: latest_version_tag}  # Return the upgrade info
        print("Upgrading " + name + " to its latest version. Version " + latest_version_tag)
        # Proceed with uninstallation
        if not cli.uninstall(name, force=args.force):
            print("You must uninstall the current version of " + name + " before you can upgrade it")
        else:
            # Install the latest version
            cli.install(
                name,
                force=args.force,
                container_image=args.container_image,
                keep_path=args.keep_path,
            )
            if cli.settings.default_view and not args.no_view:
                cli.view_install(
                cli.settings.default_view,
                name,
                force=args.force,
                container_image=args.container_image,
            )
    

