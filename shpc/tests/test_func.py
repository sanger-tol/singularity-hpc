import os
import pytest
from .helpers import init_client
from shpc.client.upgrade import  get_latest_version as glv
from shpc.client.upgrade import get_installed_versions as giv

@pytest.mark.parametrize("module_sys, module_file, container_tech, remote",
    [
        ("lmod", "module.lua", "singularity", True),  
        ("tcl", "module.tcl", "singularity", True),  
        ("lmod", "module.lua", "singularity", False),  
        ("tcl", "module.tcl", "singularity", False), 
    ],
)

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

    installed_version = client.list(name)
    print(f"Installed version expected {installed_version}")

    print("Attempting upgrade...")
    client.upgrade("quay.io/biocontainers/samtools", dry_run=False, force=True)

    module_dir = os.path.join(client.settings.module_base, "quay.io/biocontainers/samtools", latest_version)
    print(f"Checking module directory: {module_dir}")
    assert os.path.exists(module_dir), f"Module directory for {latest_version} should be created."

    module_file_path = os.path.join(module_dir, module_file)
    print(f"Checking if module file exists: {module_file}")
    assert os.path.exists(module_file_path), "Latest version's module files should be installed."
