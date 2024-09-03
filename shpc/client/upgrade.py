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

    # Get the list of installed modules
    installed_modules = cli.list(return_modules=True)

    # Ensure the user has modules installed before carrying out upgrade
    if not installed_modules:
        logger.exit("Cannot perform shpc upgrade because you currently do not have any module installed.", 0)

    # Upgrade a specific installed module 
    if args.upgrade_recipe:
        # Avoid invalid argument combinations
        if args.upgrade_all or args.preview:
            logger.exit("Cannot use '--all' or '--preview' with a specific recipe. Please choose one option.")
        # Check if the user specified a version
        if ":" in args.upgrade_recipe:
            logger.exit("Please use 'shpc upgrade recipe' without including a version.")
        # Check if the specific module is installed
        if args.upgrade_recipe not in installed_modules:
            logger.exit(f"You currently do not have {args.upgrade_recipe} installed.\nYou can install it with this command: shpc install {args.upgrade_recipe}", 0)
        upgrade(args.upgrade_recipe, cli, args)

    # Upgrade all installed modules
    elif args.upgrade_all:
        # Avoid invalid argument combinations
        if args.preview:
            logger.exit("Cannot use '--all' and '--preview' together. Please choose one option.")
        # Store all outdated modules
        print("Checking your installed modules for version updates...")
        outdated_modules = []
        for module in installed_modules.keys():
            upgrade_info = upgrade(module, cli, args, preview=True)
            if upgrade_info:
                outdated_modules.append(module)
        # Get the number of the outdated modules
        num_outdated = len(outdated_modules)
        # Perform upgrade on each outdated module
        if num_outdated == 0:
            logger.info("No upgrade needed. All your modules are up to date.")
        else:
            logger.info(f"Found {num_outdated} outdated module(s)")
            for module in outdated_modules:
                upgrade(module, cli, args)
            logger.info("All your modules are now up to date.")

    # Display all modules available for upgrade from the user's module list
    elif args.preview:
        upgrades_available = {}
        for module in installed_modules.keys():
            upgrade_info = upgrade(module, cli, args, preview=True)
            if upgrade_info:
                upgrades_available.update(upgrade_info)
        
        if upgrades_available:
            logger.info("These are the latest versions available for your outdated modules:")
            for module, version in upgrades_available.items():
                print(f"{module}: {version}")
        else:
            logger.info("No upgrade needed. All your modules are up to date.")

    # Warn the user for not providing an argument
    else:
        logger.exit("Wrong command. For upgrade description, please use shpc upgrade --h.")


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

    def get_installed_versions(recipe):
        '''
        Retrieve the installed versions of the recipe from the user's module list
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
            logger.error(f"Failed to execute shpc list command: {e}")
            return None
    
    # Load the container configuration for the specified recipe
    config = cli._load_container(name)

    #Store the installed versions and the latest version tag
    installed_versions = get_installed_versions(name)
    latest_version_tag = get_latest_version(config)

    # Compare the latest version with the user's installed version
    if latest_version_tag in installed_versions:
        if preview:
            return None  # No upgrade available
        logger.info("You have the latest version of " + name + " installed already")
    else:
        if preview:
            return {name: latest_version_tag}  # Return the upgrade info
        print("Upgrading " + name + " to its latest version. Version " + latest_version_tag)

        # Ask if the user wants to unintall old versions
        if not cli.uninstall(name, force=args.force):
            logger.info("Old versions of " + name + " were preserved")
        
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
    

