__author__ = "Ausbeth Aguguo"
__copyright__ = "Copyright 2021-2024, Ausbeth Aguguo"
__license__ = "MPL 2.0"

import os
import pytest
from .helpers import init_client
import shpc.main.modules.views as views
from shpc.client.upgrade import  get_latest_version as glv

@pytest.mark.parametrize(
    "module_sys,module_file,container_tech,remote,dry_run",
    [
        ("lmod", "module.lua", "singularity", False, False),
        #("lmod", "module.lua", "podman", False, False),
        ("tcl", "module.tcl", "singularity", False, False),
        #("tcl", "module.tcl", "podman", False, False),
        ("lmod", "module.lua", "singularity", True, False),
        #("lmod", "module.lua", "podman", True, False),
        ("tcl", "module.tcl", "singularity", True, False),
        #("tcl", "module.tcl", "podman", True, False),
        ("lmod", "module.lua", "singularity", False, True),
        #("lmod", "module.lua", "podman", False, True),
        ("tcl", "module.tcl", "singularity", False, True),
        #("tcl", "module.tcl", "podman", False, True),
        ("lmod", "module.lua", "singularity", True, True),
        #("lmod", "module.lua", "podman", True, True),
        ("tcl", "module.tcl", "singularity", True, True),
        #("tcl", "module.tcl", "podman", True, True),
    ],
)

def test_upgrade_software(tmp_path, module_sys, module_file, container_tech, remote, dry_run):
    """
    Test upgrading a single software.
    """
    client = init_client(str(tmp_path), module_sys, container_tech, remote=remote)

    # Install an outdated version of a software
    client.install("quay.io/biocontainers/samtools:1.18--h50ea8bc_0")

    # Load the container configuration for samtools
    name = client.add_namespace("quay.io/biocontainers/samtools")
    config = client._load_container(name)

    # Get the latest version tag from the configuration
    latest_version = glv(config)

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
    client.view_install("mpi", "quay.io/biocontainers/samtools:1.18--h50ea8bc_0")

    # Upgrade the software to its latest version
    client.upgrade(name=name, dry_run=dry_run)

    # Verify the latest version of samtools was installed
    module_dir = os.path.join(client.settings.module_base, "quay.io/biocontainers/samtools", latest_version)
    assert os.path.exists(module_dir), f"Latest version {latest_version} should be installed."

    # Verify that its module files was installed
    module_file_path = os.path.join(module_dir, module_file)
    assert os.path.exists(module_file_path)

    # Check if the upgraded software was added to the existing view
    view = client.views["mpi"]
    assert view.exists(module_dir), f"Upgraded software was not added to the view 'mpi'"


    