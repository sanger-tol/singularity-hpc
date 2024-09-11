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

    # Get the list of installed software
    installed_software = cli.list(return_modules=True)

    # Ensure the user has software installed before carrying out upgrade
    if not installed_software:
        logger.exit("Cannot perform shpc upgrade because you currently do not have any software installed.", 0)

    # Avoid invalid argument combination
    if args.upgrade_recipe and args.upgrade_all and args.dryrun:
        logger.exit("Cannot use '--all', '--dry-run', and a specific recipe together.\nFor upgrade help description, please use shpc upgrade --help or shpc upgrade -h.")

    # Upgrade a specific installed software 
    if args.upgrade_recipe:
        # Avoid invalid argument combination
        if args.upgrade_all:
            logger.exit("Cannot use '--all' with a specific recipe. Please choose one option.")
        # Check if the user specified a version
        if ":" in args.upgrade_recipe:
            logger.exit("Please use 'shpc upgrade recipe' without including a version.")
        # Check if the specific software is installed
        if args.upgrade_recipe not in installed_software:
            logger.exit(f"You currently do not have {args.upgrade_recipe} installed.\nYou can install it with this command: shpc install {args.upgrade_recipe}", 0)
        # Does the user just want a dry-run of the specific software?
        if args.dryrun:
            upgrade_info = upgrade(args.upgrade_recipe, cli, args, dryrun=True) # This returns {software:latest_version} if latest is available and None otherwise
            if upgrade_info:
                for software, version in upgrade_info.items():
                    logger.info(f"You do not have the latest version installed.\n{software}:{version} is the latest version available to install")
            else:
                logger.info(f"You have the latest version of {args.upgrade_recipe} installed.")
        # Upgade the software
        else:
            upgrade(args.upgrade_recipe, cli, args)

    # Upgrade all installed software
    elif args.upgrade_all:
        # Store a list of all outdated software
        outdated_software = []
        # Does the user just want a dry-run of all software?
        if args.dryrun:
            print("Performing a dry-run on all your software...")
            for software in installed_software.keys():
                upgrade_info = upgrade(software, cli, args, dryrun=True)
                if upgrade_info:
                    logger.info(f"{software} is outdated. {upgrade_info} is the latest version available to install.")
                    outdated_software.append(software)
                else:
                    logger.info(f"{software} is up to date.")
            # Provide a report on the dry-run
            num_outdated = len(outdated_software)
            if num_outdated == 0:
                logger.info("All your software are currently up to date.")
            else:
                logger.info(f"You have a total of {num_outdated} outdated software.")
        # Upgrade all software
        else:
            # Store all outdated software
            print("Checking your list to upgrade outdated software...")
            for software in installed_software.keys():
                upgrade_info = upgrade(software, cli, args, dryrun=True)
                if upgrade_info:
                    outdated_software.append(software)
            # Get the number of the outdated software
            num_outdated = len(outdated_software)
            # Perform upgrade on each outdated software
            if num_outdated == 0:
                logger.info("No upgrade needed. All your software are up to date.")
            else:
                logger.info(f"Found {num_outdated} outdated software")
                for software in outdated_software:
                    upgrade(software, cli, args)
                logger.info("All your software are now up to date.")

    # Display all software available for upgrade from the user's software list
    elif args.dryrun:
        print("Checking your list to preview outdated software...")
        upgrades_available = {}
        for software in installed_software.keys():
            upgrade_info = upgrade(software, cli, args, dryrun=True)
            if upgrade_info:
                upgrades_available.update(upgrade_info)
        # Provide a report on the dry-run
        if upgrades_available:
            logger.info("These are the latest versions available for your outdated software:")
            for software, version in upgrades_available.items():
                print(f"{software}:{version}")
        else:
            logger.info("Nothing to preview. All your software are up to date.")

    # Warn the user for not providing an argument
    else:
        logger.exit("Incomplete command.\nFor upgrade help description, please use shpc upgrade --help or shpc upgrade -h.")


def upgrade(name, cli, args, dryrun=False):
    """
    Upgrade a software to its latest version. Or preview available upgrades from the user's software list
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
        Retrieve the installed versions of the recipe from the user's software list
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
        if dryrun:
            return None  # No upgrade available
        logger.info("You have the latest version of " + name + " installed already")
    else:
        if dryrun:
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
    

