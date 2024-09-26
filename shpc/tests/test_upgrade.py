__author__ = "Ausbeth Aguguo"
__copyright__ = "Copyright 2021-2024, Ausbeth Aguguo"
__license__ = "MPL 2.0"

import os
import pytest
from unittest import mock
from .helpers import init_client
import shpc.main.modules.views as views
from shpc.client.upgrade import  get_latest_version as glv

@pytest.mark.parametrize(
    "module_sys, module_file, container_tech, remote, dryrun",
    [
    ("lmod", "module.lua", "singularity", False, False),
    ("lmod", "module.lua", "podman", False, False),
    ("tcl", "module.tcl", "singularity", False, False),
    ("tcl", "module.tcl", "podman", False, False),
    ("lmod", "module.lua", "singularity", True, False),
    ("lmod", "module.lua", "podman", True, False),
    ("tcl", "module.tcl", "singularity", True, False),
    ("tcl", "module.tcl", "podman", True, False),
    ("lmod", "module.lua", "singularity", False, True),
    ("lmod", "module.lua", "podman", False, True),
    ("tcl", "module.tcl", "singularity", False, True),
    ("tcl", "module.tcl", "podman", False, True),
    ("lmod", "module.lua", "singularity", True, True),
    ("lmod", "module.lua", "podman", True, True),
    ("tcl", "module.tcl", "singularity", True, True),
    ("tcl", "module.tcl", "podman", True, True),
    ],
)

def test_upgrade_software_with_force(tmp_path, module_sys, module_file, container_tech, remote, dryrun):
    """
    Test upgrading a software where uninstalling older versions and installing latest version to view is also done.
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
    client.upgrade("quay.io/biocontainers/samtools", dryrun=dryrun, force=True)

    # Load the container configuration for the software and get its latest version tag
    name = client.add_namespace("quay.io/biocontainers/samtools")
    config = client._load_container(name)
    latest_version = glv(name, config)

    # Verify if the latest version of the software was installed 
    if not dryrun:
        # Verify the module's directory exists and module files were installed
        module_dir = os.path.join(client.settings.module_base, "quay.io/biocontainers/samtools", latest_version)
        assert os.path.exists(module_dir), "Latest version directiory should exist."
        module_file_path = os.path.join(module_dir, module_file)
        assert os.path.exists(module_file_path), "Latest version's module files should be installed."

        # Check if the older version's module directory was removed and if its module files were uninstalled
        module_dir_old = os.path.join(client.settings.module_base, "quay.io/biocontainers/samtools", "1.18--h50ea8bc_1")
        assert not os.path.exists(module_dir_old), "Older version should be uninstalled"
        module_file_path = os.path.join(module_dir_old, module_file)
        assert not os.path.exists(module_file_path), "Older version's module files should be uninstalled."

        # Ensure the latest version was added to the view 
        assert client.views["mpi"].exists(module_dir), "Upgraded software should be added to the view 'mpi'"
    
    # Verify that the latest version of the software was not installed if dry-run is TRUE
    else:
        module_dir = os.path.join(client.settings.module_base, "quay.io/biocontainers/samtools", latest_version)
        assert not os.path.exists(module_dir), "Latest version should not be installed."
        module_file_path = os.path.join(module_dir, module_file)
        assert not os.path.exists(module_file_path), "Latest version's module files should not be installed."


@pytest.mark.parametrize(
    "module_sys,module_file,container_tech,remote",
    [
        ("lmod", "module.lua", "singularity", False),
        ("lmod", "module.lua", "podman", False),
        ("tcl", "module.tcl", "singularity", False),
        ("tcl", "module.tcl", "podman", False),
        ("lmod", "module.lua", "singularity", True),
        ("lmod", "module.lua", "podman", True),
        ("tcl", "module.tcl", "singularity", True),
        ("tcl", "module.tcl", "podman", True),
    ],
)

@mock.patch("shpc.utils.confirm_action")
def test_upgrade_software_without_force(mock_confirm_action, tmp_path, module_sys, module_file, container_tech, remote):
    """
    Test upgrading a software where uninstalling older versions and installing latest version to view is not done.
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

    # Simulate user's choice for uninstalling older versions and installing latest version to the views of the older versions
    mock_confirm_action.return_value = False

    # Upgrade the software to its latest version
    client.upgrade("quay.io/biocontainers/samtools", dryrun=False, force=False)

    # Load the container configuration for the software and get its latest version tag
    name = client.add_namespace("quay.io/biocontainers/samtools")
    config = client._load_container(name)
    latest_version = glv(name, config)

    # Verify the module's directory exists and module files were installed
    module_dir = os.path.join(client.settings.module_base, "quay.io/biocontainers/samtools", latest_version)
    assert os.path.exists(module_dir), "Latest version directiory should exist."
    module_file_path = os.path.join(module_dir, module_file)
    assert os.path.exists(module_file_path), "Latest version's module files should be installed."

    # Ensure the older version's module directory still exists and its module files were not uninstalled
    module_dir_old = os.path.join(client.settings.module_base, "quay.io/biocontainers/samtools", "1.18--h50ea8bc_1")
    assert os.path.exists(module_dir_old), "Old version should not be uninstalled"
    module_file_path = os.path.join(module_dir_old, module_file)
    assert os.path.exists(module_file_path), "Older version's module files should not be uninstalled."
    
    # Ensure the latest version was not added to the view 
    assert not client.views["mpi"].exists(module_dir), "Upgraded software should not added to the view 'mpi'"


@pytest.mark.parametrize(
    "module_sys,module_file,container_tech,remote",
    [
        ("lmod", "module.lua", "singularity", False),
        ("lmod", "module.lua", "podman", False),
        ("tcl", "module.tcl", "singularity", False),
        ("tcl", "module.tcl", "podman", False),
        ("lmod", "module.lua", "singularity", True),
        ("lmod", "module.lua", "podman", True),
        ("tcl", "module.tcl", "singularity", True),
        ("tcl", "module.tcl", "podman", True),
    ],
)   

def test_upgrade_with_latest_already_installed(tmp_path, module_sys, module_file, container_tech,remote):
    client = init_client(str(tmp_path), module_sys, container_tech,remote=remote)

    # Load the container configuration for the software and get is latest version
    name = client.add_namespace("quay.io/biocontainers/samtools")
    config = client._load_container(name)
    latest_version = glv(name, config)

    # Install an outdated and the latest version of a software
    client.install(f"quay.io/biocontainers/samtools:{latest_version}")
    client.install("quay.io/biocontainers/samtools:1.18--h50ea8bc_1")

    # Verify the latest version's module directory exists and module files were installed
    module_dir = os.path.join(client.settings.module_base, "quay.io/biocontainers/samtools", latest_version)
    assert os.path.exists(module_dir), "Latest version directiory should exist."
    module_file_path = os.path.join(module_dir, module_file)
    assert os.path.exists(module_file_path), "Latest version module files should exist."

    # Capture the time the directory was created
    module_dir_mtime_before = os.path.getmtime(module_dir)

    # Perform upgrade
    client.upgrade("quay.io/biocontainers/samtools", dryrun=False, force=True)

    # Capture the time of the directory after upgrade was done
    module_dir_mtime_after = os.path.getmtime(module_dir)

    # Ensure the directory did not change, to signify upgrade was not performed when the latest was already installed
    assert module_dir_mtime_after == module_dir_mtime_before, "Upgrade should not occur if latest is installed already."


@pytest.mark.parametrize(
    "module_sys,module_file,container_tech,remote",
    [
        ("lmod", "module.lua", "singularity", False),
        ("lmod", "module.lua", "podman", False),
        ("tcl", "module.tcl", "singularity", False),
        ("tcl", "module.tcl", "podman", False),
        ("lmod", "module.lua", "singularity", True),
        ("lmod", "module.lua", "podman", True),
        ("tcl", "module.tcl", "singularity", True),
        ("tcl", "module.tcl", "podman", True),
    ],
)

def test_upgrade_all_software(tmp_path, module_sys, module_file, container_tech, remote):
    """
    Test upgrading a software where uninstalling older versions and installing latest version to view is also done.
    """
    client = init_client(str(tmp_path), module_sys, container_tech, remote=remote)

    # Install two different outdated software
    client.install("quay.io/biocontainers/samtools:1.18--h50ea8bc_1")
    client.install("quay.io/biocontainers/bwa:0.7.18--he4a0461_0")

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
    client.view_install("mpi", "quay.io/biocontainers/bwa:0.7.18--he4a0461_0")

    # Upgrade all software to thei latest version
    installed_software = client.list(return_modules=True)
    for software, versions in installed_software.items():
        client.upgrade(software, dryrun=False, force=True)

        # Load the container configuration for the software and get their latest version tag
        name = client.add_namespace(software)
        config = client._load_container(name)
        latest_version = glv(name, config)
    
        # Verify the module's directory exists and module files were installed
        module_dir = os.path.join(client.settings.module_base, software, latest_version)
        assert os.path.exists(module_dir), "Latest version directiory should exist."
        module_file_path = os.path.join(module_dir, module_file)
        assert os.path.exists(module_file_path), "Latest version's module files should be installed."

        for older_version in versions:
            # Check if the older version's module directory was removed and if its module files were uninstalled
            module_dir_old = os.path.join(client.settings.module_base, software, older_version)
            assert not os.path.exists(module_dir_old), "Older version should be uninstalled"
            module_file_path = os.path.join(module_dir_old, module_file)
            assert not os.path.exists(module_file_path), "Older version's module files should be uninstalled."

        # Ensure the latest versions were added to the view 
        assert client.views["mpi"].exists(module_dir), "Upgraded software should be added to the view 'mpi'"

    
   
