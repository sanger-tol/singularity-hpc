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
    
    '''
    #TODO
    # Check if the specified module is among the list of installed modules
    installed_modules = cli.list(return_modules=True)
    if args.reinstall_recipe in installed_modules:
    '''
    # Uninstall the software
    cli.uninstall(args.reinstall_recipe, force=args.force)

    # Install the software
    cli.install(
        args.reinstall_recipe,
        force=args.force,
        container_image=args.container_image,
        keep_path=args.keep_path,
    )
    if cli.settings.default_view and not args.no_view:
        cli.view_install(
        cli.settings.default_view,
        args.reinstall_recipe,
        force=args.force,
        container_image=args.container_image,
    )
    '''
    else:
        #exit if its not installed
        logger.exit(f"{args.reinstall_recipe} is not installed, cannot reinstall.")
    '''
    
    
