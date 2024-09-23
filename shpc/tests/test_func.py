import os
import pytest
from .helpers import init_client
from unittest import mock
import shpc.main.modules.views as views
from shpc.client.upgrade import  get_latest_version as glv


@pytest.mark.parametrize("module_sys, module_file, container_tech, remote",
    [
        ("lmod", "module.lua", "singularity", True),  
        ("tcl", "module.tcl", "singularity", True),  
        ("lmod", "module.lua", "singularity", False),  
        ("tcl", "module.tcl", "singularity", False), 
    ],
)

@mock.patch("shpc.utils.confirm_action")
def test_upgrade(mock_confirm_action, tmp_path, module_sys, module_file, container_tech,remote):
    client = init_client(str(tmp_path), module_sys, container_tech,remote=remote)

    print("Installing initial version...")
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

    # Load the container configuration for the software
    name = client.add_namespace("quay.io/biocontainers/samtools")
    config = client._load_container(name)

    # Get the latest version tag from the software's configuration
    latest_version = glv(name, config)
    print(f"Latest version expected: {latest_version}")

    installed_version = client.list(pattern=name, return_modules=True)
    print(f"Installed versions expected {installed_version}")

    # Simulate user's choice
    mock_confirm_action.return_value = False

    print("Attempting upgrade...")
    client.upgrade("quay.io/biocontainers/samtools", dry_run=False, force=False)

    module_dir = os.path.join(client.settings.module_base, "quay.io/biocontainers/samtools", latest_version)
    print(f"Checking module directory: {module_dir}")
    assert os.path.exists(module_dir), f"Module directory for {latest_version} should be created."

    module_file_path = os.path.join(module_dir, module_file)
    print(f"Checking if module file exists: {module_file}")
    assert os.path.exists(module_file_path), "Latest version's module files should be installed."

    # Check if the older version's module directory was removed and if its module files were uninstalled
    module_dir_old = os.path.join(client.settings.module_base, "quay.io/biocontainers/samtools", "1.18--h50ea8bc_1")
    assert os.path.exists(module_dir_old), "Older version should not be uninstalled"
    module_file_path = os.path.join(module_dir_old, module_file)
    assert os.path.exists(module_file_path), "Older version's module files should not be uninstalled."

    # Do not install the latest version to the existing view and ensure it was added not added to the  view 
    assert not client.views["mpi"].exists(module_dir), f"Upgraded software should not added to the view 'mpi'"

'''
def test_upgrade(tmp_path, module_sys, module_file, container_tech,remote):
    client = init_client(str(tmp_path), module_sys, container_tech,remote=remote)

    print("Installing initial version...")
    client.install("quay.io/biocontainers/samtools:1.18--h50ea8bc_1")

    # Load the container configuration for the software
    name = client.add_namespace("quay.io/biocontainers/samtools")
    config = client._load_container(name)

    # Get the latest version tag from the software's configuration
    latest_version = glv(name, config)
    print(f"Latest version expected: {latest_version}")

    installed_version = client.list(pattern=name, return_modules=True)
    print(f"Installed versions expected {installed_version}")

    print("Attempting upgrade...")
    client.upgrade("quay.io/biocontainers/samtools", dry_run=False, force=True)

    module_dir = os.path.join(client.settings.module_base, "quay.io/biocontainers/samtools", latest_version)
    print(f"Checking module directory: {module_dir}")
    assert os.path.exists(module_dir), f"Module directory for {latest_version} should be created."

    module_file_path = os.path.join(module_dir, module_file)
    print(f"Checking if module file exists: {module_file}")
    assert os.path.exists(module_file_path), "Latest version's module files should be installed."


@pytest.mark.parametrize("module_sys, module_file, container_tech, remote",
    [
        ("lmod", "module.lua", "singularity", True),  
        ("tcl", "module.tcl", "singularity", True),  
        ("lmod", "module.lua", "singularity", False),  
        ("tcl", "module.tcl", "singularity", False), 
    ],
)

def test_upgrade_with_latest_already_installed(tmp_path, module_sys, module_file, container_tech,remote):
    client = init_client(str(tmp_path), module_sys, container_tech,remote=remote)

    # Load the container configuration for the software
    name = client.add_namespace("quay.io/biocontainers/samtools")
    config = client._load_container(name)
    latest_version = glv(name, config)

    client.install(f"quay.io/biocontainers/samtools:{latest_version}")
    client.install("quay.io/biocontainers/samtools:1.18--h50ea8bc_1")

    module_dir = os.path.join(client.settings.module_base, "quay.io/biocontainers/samtools", latest_version)
    assert os.path.exists(module_dir)
    module_file_path = os.path.join(module_dir, module_file)
    assert os.path.exists(module_file_path)

    module_dir_mtime_before = os.path.getmtime(module_dir)

    client.upgrade("quay.io/biocontainers/samtools", dry_run=False, force=True)

    module_dir_mtime_after = os.path.getmtime(module_dir)

    assert module_dir_mtime_after == module_dir_mtime_before, "Upgrade should not occur if latest is installed already."
''' 
