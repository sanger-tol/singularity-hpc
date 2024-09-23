import os
import pytest
from .helpers import init_client
from shpc.client.upgrade import  get_latest_version as glv

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

    print("Attempting upgrade...")
    client.upgrade("quay.io/biocontainers/samtools", dry_run=False, force=True)

    latest_version = "1.21--h50ea8bc_0" 

    module_dir = os.path.join(client.settings.module_base, "quay.io/biocontainers/samtools", latest_version)
    print(f"Checking module directory: {module_dir}")
    assert os.path.exists(module_dir), f"Module directory for {latest_version} should be created."

    module_file_path = os.path.join(module_dir, module_file)
    print(f"Checking if module file exists: {module_file}")
    assert os.path.exists(module_file_path), "Latest version's module files should be installed."
