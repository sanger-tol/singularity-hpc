__author__ = "Ausbeth Aguguo"
__copyright__ = "Copyright 2021-2024, Ausbeth Aguguo"
__license__ = "MPL 2.0"

import os
import pytest
from .helpers import init_client
import shpc.main.modules.views as views

@pytest.mark.parametrize(
    "module_sys,module_file,container_tech,remote,update_containers",
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

def test_reinstall_specific_software_version(tmp_path, module_sys, module_file, container_tech, remote, update_containers):
    """
    Test reinstalling a specific version of a software.
    """
    client = init_client(str(tmp_path), module_sys, container_tech, remote=remote)

    # Install a specific version of a software
    client.install("quay.io/biocontainers/samtools:1.20--h50ea8bc_0")

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

    # Install the specific version to a view
    client.view_install("mpi", "quay.io/biocontainers/samtools:1.20--h50ea8bc_0")

    # Verify its container's existence
    container_dir = os.path.join(client.settings.container_base, "quay.io/biocontainers/samtools", "1.20--h50ea8bc_0")
    assert os.path.exists(container_dir)

    # Get modification time of its container before reinstall
    container_mtime_before = os.path.getmtime(container_dir)

    # Reinstall the specific version
    client.reinstall("quay.io/biocontainers/samtools:1.20--h50ea8bc_0", update_containers=update_containers)

    # Verify that it was reinstalled
    module_dir = os.path.join(client.settings.module_base, "quay.io/biocontainers/samtools", "1.20--h50ea8bc_0")
    assert os.path.exists(module_dir)

    # Verify that its module files were reinstalled
    module_file_path = os.path.join(module_dir, module_file)
    assert os.path.exists(module_file_path)

    # Get modification time of the container after reinstall
    container_mtime_after = os.path.getmtime(container_dir)

    #Verify that its container was preserved or updated depending on update_container flag
    if update_containers:
        assert container_mtime_after > container_mtime_before, "Container should be updated when update_containers=True."
    else:
        assert container_mtime_after == container_mtime_before, "Container should be preserved when update_containers=False."

    # Check if it was restored to its views
    for view_name in client.views.keys():
        assert client.views[view_name].exists(module_dir), f"Software was not restored to view: {view_name}"


@pytest.mark.parametrize(
    "module_sys,module_file,container_tech,remote,update_containers",
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

def test_reinstall_all_software_versions(tmp_path, module_sys, module_file, container_tech, remote, update_containers):
    """
    Test reinstalling all versions of a specific software.
    """
    client = init_client(str(tmp_path), module_sys, container_tech, remote=remote)

    # Install two versions of a software
    client.install("quay.io/biocontainers/samtools:1.20--h50ea8bc_0")
    client.install("quay.io/biocontainers/samtools:1.20--h50ea8bc_1")

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

    # Install both versions to a view
    client.view_install("mpi", "quay.io/biocontainers/samtools:1.20--h50ea8bc_0")
    client.view_install("mpi", "quay.io/biocontainers/samtools:1.20--h50ea8bc_1")

    # Verify their container's existence
    container_0_dir = os.path.join(client.settings.container_base, "quay.io/biocontainers/samtools", "1.20--h50ea8bc_0")
    container_1_dir = os.path.join(client.settings.container_base, "quay.io/biocontainers/samtools", "1.20--h50ea8bc_1")
    assert os.path.exists(container_0_dir)
    assert os.path.exists(container_1_dir)

    # Get modification time of their container before reinstall
    container_0_mtime_before = os.path.getmtime(container_0_dir)
    container_1_mtime_before = os.path.getmtime(container_1_dir)

    # Reinstall all versions of the specific software
    client.reinstall("quay.io/biocontainers/samtools", update_containers=update_containers)

    # Verify that both versions exist after reinstall
    module_0_dir = os.path.join(client.settings.module_base, "quay.io/biocontainers/samtools", "1.20--h50ea8bc_0")
    module_1_dir = os.path.join(client.settings.module_base, "quay.io/biocontainers/samtools", "1.20--h50ea8bc_1")
    assert os.path.exists(module_0_dir)
    assert os.path.exists(module_1_dir)

    # Verify if their module files were reinstalled
    module_0_file_path = os.path.join(module_0_dir, module_file)
    module_1_file_path = os.path.join(module_1_dir, module_file)
    assert os.path.exists(module_0_file_path)
    assert os.path.exists(module_1_file_path)

    # Get modification time of their container after reinstall
    container_0_mtime_after = os.path.getmtime(container_0_dir)
    container_1_mtime_after = os.path.getmtime(container_1_dir)

    # Verify that their containers were preserved or updated depending on update_containers
    if update_containers:
        assert container_0_mtime_after > container_0_mtime_before, "Container should be updated when update_containers=True."
        assert container_1_mtime_after > container_1_mtime_before, "Container should be updated when update_containers=True."
    else:    
        assert container_0_mtime_after == container_0_mtime_before, "Container should be preserved when update_containers=False."
        assert container_1_mtime_after == container_1_mtime_before, "Container should be preserved when update_containers=False."

    # Check if both versions were restored to their views
    for view_name in client.views.keys():
        assert client.views[view_name].exists(module_0_dir), f"Software was not restored to view: {view_name}"
    for view_name in client.views.keys():
        assert client.views[view_name].exists(module_1_dir), f"Software was not restored to view: {view_name}"


@pytest.mark.parametrize(
    "module_sys,module_file,container_tech,remote,update_containers",
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

def test_reinstall_all_software(tmp_path, module_sys, module_file, container_tech, remote, update_containers):
    """
    Test reinstalling all installed software.
    """
    client = init_client(str(tmp_path), module_sys, container_tech, remote=remote)

    # Install two different software
    client.install("quay.io/biocontainers/samtools:1.20--h50ea8bc_0")
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

    # Install both software to a view
    client.view_install("mpi", "quay.io/biocontainers/samtools:1.20--h50ea8bc_0")
    client.view_install("mpi", "quay.io/biocontainers/bwa:0.7.18--he4a0461_0")

    # Verify the existence of their containers
    container_samtools_dir = os.path.join(client.settings.container_base, "quay.io/biocontainers/samtools", "1.20--h50ea8bc_0")
    container_bwa_dir = os.path.join(client.settings.container_base, "quay.io/biocontainers/bwa", "0.7.18--he4a0461_0")
    assert os.path.exists(container_samtools_dir)
    assert os.path.exists(container_bwa_dir)

    # Get modification time of their container before reinstall
    container_samtools_mtime_before = os.path.getmtime(container_samtools_dir)
    container_bwa_mtime_before = os.path.getmtime(container_bwa_dir)

    # Reinstall all software
    installed_software = client.list(return_modules=True)
    for software in installed_software.keys():
        client.reinstall(software, update_containers=update_containers)

    # Verify that both modules exist after reinstall
    module_samtools_dir = os.path.join(client.settings.module_base, "quay.io/biocontainers/samtools", "1.20--h50ea8bc_0")
    module_bwa_dir = os.path.join(client.settings.module_base, "quay.io/biocontainers/bwa", "0.7.18--he4a0461_0")
    assert os.path.exists(module_samtools_dir)
    assert os.path.exists(module_bwa_dir)

    # Verify if their module files were reinstalled
    module_samtools_file_path = os.path.join(module_samtools_dir, module_file)
    module_bwa_file_path = os.path.join(module_bwa_dir, module_file)
    assert os.path.exists(module_samtools_file_path)
    assert os.path.exists(module_bwa_file_path)

    # Get modification time of their container after reinstall
    container_samtools_mtime_after = os.path.getmtime(container_samtools_dir)
    container_bwa_mtime_after = os.path.getmtime(container_bwa_dir)

    # Verify that their containers were preserved or updated depending on update_containers
    if update_containers:
        assert container_samtools_mtime_after > container_samtools_mtime_before, "Container should be updated when update_containers=True."
        assert container_bwa_mtime_after > container_bwa_mtime_before, "Container should be updated when update_containers=True."
        
    else:    
        assert container_samtools_mtime_after == container_samtools_mtime_before, "Container should be preserved when update_containers=False."
        assert container_bwa_mtime_after == container_bwa_mtime_before, "Container should be preserved when update_containers=False."

    # Check if both software were restored to their views
    for view_name in client.views.keys():
        assert client.views[view_name].exists(module_samtools_dir), f"Software was not restored to view: {view_name}"
    for view_name in client.views.keys():
        assert client.views[view_name].exists(module_bwa_dir), f"Software was not restored to view: {view_name}"