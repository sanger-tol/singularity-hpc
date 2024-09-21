__author__ = "Ausbeth Aguguo"
__copyright__ = "Copyright 2021-2024, Ausbeth Aguguo"
__license__ = "MPL 2.0"

import shpc.utils as utils
from shpc.logger import logger
import subprocess

def main(args, parser, extra, subparser):
    from shpc.main import get_client
    utils.ensure_no_extra(extra)

    cli = get_client(quiet=args.quiet, settings_file=args.settings_file)

    # Update config settings on the fly
    cli.settings.update_params(args.config_params)

    # Get the list of installed software
    installed_software = cli.list(return_modules=True)

    # Ensure the user has software installed before carrying out upgrade
    if not installed_software:
        logger.exit("Cannot perform shpc upgrade because you currently do not have any software installed.", 0)

    # Upgrade a specific installed software 
    if args.upgrade_recipe:
        # Check if the provided recipe is known in any registry
        try:
            cli._load_container(args.upgrade_recipe)
        except SystemExit:
            # Give additional messages relating to shpc upgrade, to the original exit message in _load_container function 
            logger.exit("This means it cannot be upgraded because it is not installed, and cannot be installed because it is not known in any registry.\nPlease check the name or try a different recipe.")
        # Check if the user typed an invalid argument combination
        if args.upgrade_all:
            logger.exit("Cannot use '--all' with a specific recipe. Please choose one option.")
        # Check if the user specified a version
        if ":" in args.upgrade_recipe:
            logger.exit("Please use 'shpc upgrade recipe' without including a version.")
        # Check if the specific software is installed
        if args.upgrade_recipe not in installed_software:
            logger.exit(f"You currently do not have {args.upgrade_recipe} installed.\nYou can install it with this command: shpc install {args.upgrade_recipe}", 0)
        
        # Does the user just want a dry-run of the specific software?
        if args.dry_run:
            upgrade_info = upgrade(args.upgrade_recipe, cli, args, dry_run=True) # This returns {software:latest_version} if latest is available and None otherwise
            if upgrade_info:
                for version in upgrade_info.values():
                    logger.info(f"You do not have the latest version installed.\nLatest version avaiable is {version}")
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
        if args.dry_run:
            print("Performing a dry-run on all your software...")
            for software in installed_software.keys():
                upgrade_info = upgrade(software, cli, args, dry_run=True)
                if upgrade_info:
                    for software, version in upgrade_info.items():
                        logger.info(f"{software} is outdated. Latest version available is {version}")
                    outdated_software.append(software)
                else:
                    logger.info(f"{software} is up to date.")
            # Provide a report on the dry-run
            num_outdated = len(outdated_software)
            if num_outdated == 0:
                logger.info("All your software are currently up to date.")
            else:
                logger.info(f"You have a total of {num_outdated} outdated software.")
                msg = "Do you want a simple list of only your outdated software?"
                if utils.confirm_action(msg, force=args.force):
                    for software in outdated_software:
                        print(software)

        # Upgrade all software
        else:
            print("Checking your list to upgrade outdated software...")
            for software in installed_software.keys():
                upgrade_info = upgrade(software, cli, args, dry_run=True)
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

    # Warn the user for not providing an argument
    else:
        subparser.error("Incomplete command. The following arguements are required: upgrade_recipe, --all, or -h for more details ")


def upgrade(name, cli, args, dry_run=False):
    """
    Upgrade a software to its latest version. Or preview available upgrades from the user's software list
    """
    # Add namespace 
    name = cli.add_namespace(name)
    
    # Load the container configuration for the specified recipe
    config = cli._load_container(name)

    #Store the installed versions and the latest version tag
    installed_versions = get_installed_versions(name)
    latest_version_tag = get_latest_version(name, config)

    # Compare the latest version with the user's installed version
    if latest_version_tag in installed_versions:
        if dry_run:
            return None  # No upgrade available
        logger.info("You have the latest version of " + name + " installed already")
    else:
        if dry_run:
            return {name: latest_version_tag}  # Return the upgrade info
        print("Upgrading " + name + " to its latest version. Version " + latest_version_tag)

        # Get the list of views the software was in
        views_with_module = set()
        for view_name, entry in cli.views.items():
            if entry.exists(cli.new_module(name).module_dir):
                views_with_module.add(view_name)

        # Ask if the user wants to unintall old versions
        if not cli.uninstall(name, force=args.force):
            logger.info("Old versions of " + name + " were preserved")
        
        # Install the latest version
        cli.install(name)

        # Install the latest version to views where the outdated version was found
        msg = f"Do you also want to install the latest version of {name} to the view(s) of the previous version(s)?"
        if utils.confirm_action(msg, force=args.force):
            for view_name in views_with_module:
                cli.view_install(view_name, name)
                logger.info(f"Installed the latest version of {name} to view: {view_name}")


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


def get_latest_version(name, config):
        '''
        Retrieve the latest version tag from the container configuration.
        '''
        latest_version_info = config.get('latest')
        if not latest_version_info:
            logger.exit(f"No latest version found for {name}")
        
        # Extract the latest version tag
        latest_version_tag = list(latest_version_info.keys())[0]
        return latest_version_tag



        

