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

    if args.all:
        # Check if the user typed an invalid argument combination
        if args.reinstall_recipe:
            logger.exit("You cannot specify a recipe with --all. Use shpc reinstall --all to reinstall all installed software.")
        
        # Check if the has any software installed
        installed_software = cli.list(return_modules=True)
        if not installed_software:
            logger.exit("You currently don't have any installed software to reinstall.")
        
        # Reinstall all installed software
        print("Reinstalling all installed software...")
        for software in installed_software.keys():
            reinstall(software, cli, args, update_containers=args.update_containers)
        logger.info("All softwares reinstalled.")

    else:
        # Reinstall a specific software
        if not args.reinstall_recipe:
            logger.exit("You must specify a recipe to reinstall or use --all to reinstall all installed software.")

        # Add namespace
        name = cli.add_namespace(args.reinstall_recipe)
    
        # Reinstall the software
        reinstall(name, cli, args, update_containers=args.update_containers)

def reinstall(name, cli, args, update_containers=False):
    """
    Reinstall a specific version or all versions of a software.
    """
    # Check if the software or version is installed
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
        reinstall_version(name, cli, args, update_containers)
        logger.info(f"Successfully reinstalled of {name}.")
    else:
        print(f"Reinstalling all versions of {name}...")
        for version in installed_versions:
            version_name = f"{name}:{version}"
            reinstall_version(version_name, cli, args, update_containers)
        logger.info(f"Successfully reinstalled all versions of {name}.")


def reinstall_version(name, cli, args, update_containers):
    """
    Sub-function to handle the actual reinstallation
    """
    # Uninstallation process. By default, uninstall without prompting the user and keep the container except the user wants a complete reinstall
    cli.uninstall(name, force=True, keep_container=not update_containers) 

    # Display a helpful message to the user about the state of the container during reinstall process
    if not update_containers:
        print("Container was successfully preserved, module files and wrapper scripts will be overwritten...")
    else:
        print("No container was preserved, all files will be overwritten...")
    
    # Installation process
    cli.install(name)

    


