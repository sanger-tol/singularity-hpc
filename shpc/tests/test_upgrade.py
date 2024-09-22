__author__ = "Ausbeth Aguguo"
__copyright__ = "Copyright 2021-2024, Ausbeth Aguguo"
__license__ = "MPL 2.0"

import os
import pytest
from unittest import mock
from .helpers import init_client
import shpc.main.modules.views as views
from shpc.client.upgrade import  get_latest_version as glv

@pytest.mark.parametrize("module_sys, module_file, container_tech, remote, dry_run, uninstall_prompt, view_prompt",
    [
        ("lmod", "module.lua", "singularity", False, False, True, True),  
        ("lmod", "module.lua", "singularity", False, False, True, False),  
        ("lmod", "module.lua", "singularity", False, False, False, True),  
        ("lmod", "module.lua", "singularity", False, False, False, False),  
        ("tcl", "module.tcl", "singularity", False, False, True, True),  
        ("tcl", "module.tcl", "singularity", False, False, True, False),  
        ("tcl", "module.tcl", "singularity", False, False, False, True),  
        ("tcl", "module.tcl", "singularity", False, False, False, False),  
        ("lmod", "module.lua", "singularity", True, False, True, True),  
        ("lmod", "module.lua", "singularity", True, False, True, False),  
        ("lmod", "module.lua", "singularity", True, False, False, True),  
        ("lmod", "module.lua", "singularity", True, False, False, False),  
        ("tcl", "module.tcl", "singularity", True, False, True, True),  
        ("tcl", "module.tcl", "singularity", True, False, True, False),  
        ("tcl", "module.tcl", "singularity", True, False, False, True),  
        ("tcl", "module.tcl", "singularity", True, False, False, False),  
        ("lmod", "module.lua", "singularity", False, True, True, True),  
        ("lmod", "module.lua", "singularity", False, True, True, False),  
        ("lmod", "module.lua", "singularity", False, True, False, True),  
        ("lmod", "module.lua", "singularity", False, True, False, False),  
        ("tcl", "module.tcl", "singularity", False, True, True, True),  
        ("tcl", "module.tcl", "singularity", False, True, True, False),  
        ("tcl", "module.tcl", "singularity", False, True, False, True),  
        ("tcl", "module.tcl", "singularity", False, True, False, False),  
        ("lmod", "module.lua", "singularity", True, True, True, True),  
        ("lmod", "module.lua", "singularity", True, True, True, False),  
        ("lmod", "module.lua", "singularity", True, True, False, True),  
        ("lmod", "module.lua", "singularity", True, True, False, False),  
        ("tcl", "module.tcl", "singularity", True, True, True, True),  
        ("tcl", "module.tcl", "singularity", True, True, True, False),  
        ("tcl", "module.tcl", "singularity", True, True, False, True),  
        ("tcl", "module.tcl", "singularity", True, True, False, False),  
    ],
)

@mock.patch("shpc.utils.confirm_action")
def test_upgrade_software(mock_confirm_action, tmp_path, module_sys, module_file, container_tech, remote, dry_run, uninstall_prompt, view_prompt):
    """
    Test upgrading a single software.
    """
    client = init_client(str(tmp_path), module_sys, container_tech, remote=remote)

    # Install an outdated version of a software
    client.install("quay.io/biocontainers/samtools:1.18--h50ea8bc_1") 

    # Create the default view if it doesn't exist
    view_handler = views.ViewsHandler(settings_file=client.settings.settings_file, module_sys=module_sys)
    assert "mpi" not in client.views
    view_handler.create("mpi")
    client.detect_views()
    assert "mpi" in client.views
    view = client.views["mpi"]
    assert view.path == os.path.join(tmp_path, "views", "mpi") and os.path.exists(view.path)
    assert os.path.exists(view.config_path)
    assert view._config["view"]["name"] == "mpi"
    assert not view._config["view"]["modules"]
    assert not view._config["view"]["system_modules"]

    # Install the software to the view
    client.view_install("mpi", "quay.io/biocontainers/samtools:1.18--h50ea8bc_1")

    # Upgrade the software to its latest version
    client.upgrade("quay.io/biocontainers/samtools", dry_run=dry_run, force=True)

    # Load the container configuration for the software
    name = client.add_namespace("quay.io/biocontainers/samtools")
    config = client._load_container(name)

    # Get the latest version tag from the software's configuration
    latest_version = glv(name, config)
    print(f"Latest version expected: {latest_version}")


    # Verify if the latest version of the software was installed 
    if not dry_run:
        # Verify the module's directory exists
        module_dir = os.path.join(client.settings.module_base, "quay.io/biocontainers/samtools", latest_version)
        print(f"Checking module directory: {module_dir}")
        assert os.path.exists(module_dir), "Latest version should be installed."
        # Verify that its module files were installed
        module_file_path = os.path.join(module_dir, module_file)
        assert os.path.exists(module_file_path), "Latest version's module files should be installed."

        # Simulate user's choice for uninstalling older versions and installing latest version to the views of the older versions
        mock_confirm_action.side_effect = [uninstall_prompt,view_prompt]

        if uninstall_prompt:
            # Check the older version's module directory
            module_dir_old = os.path.join(client.settings.module_base, "quay.io/biocontainers/samtools", "1.18--h50ea8bc_1")
            assert not os.path.exists(module_dir_old), "Older version should be uninstalled"
            # Verify that its module files were uninstalled
            module_file_path = os.path.join(module_dir_old, module_file)
            assert not os.path.exists(module_file_path), "Older version's module files should be uninstalled."
        else:
            # Check the older version's module directory
            module_dir_old = os.path.join(client.settings.module_base, "quay.io/biocontainers/samtools", "1.18--h50ea8bc_1")
            assert os.path.exists(module_dir_old), "old version should not be uninstalled"
            # Verify that its module files were not uninstalled
            module_file_path = os.path.join(module_dir_old, module_file)
            assert os.path.exists(module_file_path), "Older version's module files should not be uninstalled."

        if view_prompt:
            # Install latest version to views
            client.view_install("mpi", f"quay.io/biocontainers/samtools:{latest_version}")
            # Check if the upgraded software was added to the existing view 
            assert client.views["mpi"].exists(module_dir), f"Upgraded software should be added to the view 'mpi'"
        else:
            # Do not install the latest version to views
            # Check if the upgraded software was added to the existing view 
            assert not client.views["mpi"].exists(module_dir), f"Upgraded software should not added to the view 'mpi'"
    
    # Verify that the latest version of the software was not installed if dry-run is TRUE
    else:
        module_dir = os.path.join(client.settings.module_base, "quay.io/biocontainers/samtools", latest_version)
        assert not os.path.exists(module_dir), "Latest version should not be installed."
        # Verify that its module files were not installed
        module_file_path = os.path.join(module_dir, module_file)
        assert not os.path.exists(module_file_path), "Latest version's module files should not be installed."

    


    