#!/usr/bin/python

# Copyright (C) 2021-2023 Vanessa Sochat.

# This Source Code Form is subject to the terms of the
# Mozilla Public License, v. 2.0. If a copy of the MPL was not distributed
# with this file, You can obtain one at http://mozilla.org/MPL/2.0/.

import io
import os
import shutil
from unittest import mock

import pytest

import shpc.main.modules.views as views
import shpc.main.registry as registry
import shpc.utils
from shpc.client.upgrade import get_latest_version as glv

from .helpers import here, init_client


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
def test_install_get(tmp_path, module_sys, module_file, container_tech, remote):
    """
    Test install and get
    """
    client = init_client(str(tmp_path), module_sys, container_tech, remote=remote)

    # Install known tag
    client.install("python:3.9.2-alpine")

    # Modules folder is created
    assert os.path.exists(client.settings.module_base)

    module_dir = os.path.join(client.settings.module_base, "python", "3.9.2-alpine")
    wrapper_dir = os.path.join(client.settings.wrapper_base, "python", "3.9.2-alpine")

    assert os.path.exists(module_dir)
    module_file = os.path.join(module_dir, module_file)
    assert os.path.exists(module_file)

    # Environment file is in wrapper directory
    env_file = os.path.join(wrapper_dir, client.settings.environment_file)
    assert os.path.exists(env_file)

    assert client.get("python:3.9.2-alpine")

    client.install("python:3.9.2-alpine")


@pytest.mark.parametrize(
    "module_sys,module_file,remote",
    [
        ("lmod", "module.lua", True),
        ("tcl", "module.tcl", True),
        ("lmod", "module.lua", False),
        ("tcl", "module.tcl", False),
    ],
)
def test_features(tmp_path, module_sys, module_file, remote):
    """
    Test adding features.
    Features are currently only supported for Singularity.
    """
    client = init_client(str(tmp_path), module_sys, "singularity", remote=remote)

    module_file_392 = os.path.join(
        client.settings.module_base, "python", "3.9.2-alpine", module_file
    )
    module_file_394 = os.path.join(
        client.settings.module_base, "python", "3.9.4-alpine", module_file
    )

    # Install known tag
    client.install("python:3.9.2-alpine")

    # Should not have nvidia flag
    content = shpc.utils.read_file(module_file_392)
    assert "--nv" not in content

    client.install("python:3.9.4-alpine")
    assert os.path.exists(module_file_392)
    assert os.path.exists(module_file_394)

    client.uninstall("python:3.9.2-alpine", force=True)
    assert not os.path.exists(module_file_392)
    assert os.path.exists(module_file_394)

    client.uninstall("python", force=True)
    assert not os.path.exists(module_file_394)

    # Now update settings
    client.settings.set("container_features", "gpu:nvidia")

    # Install known tag, add extra feature of gpu
    client.install("python:3.9.2-alpine", features=["gpu"])
    content = shpc.utils.read_file(module_file_392)
    assert "--nv" in content


@pytest.mark.parametrize(
    "default_version,remote",
    [
        (True, True),
        (False, True),
        ("module_sys", True),
        (None, True),
        ("first_installed", True),
        ("last_installed", True),
        (True, False),
        (False, False),
        ("module_sys", False),
        (None, False),
        ("first_installed", False),
        ("last_installed", False),
    ],
)
def test_tcl_default_version(tmp_path, default_version, remote):
    """
    Test tcl default versions.

    True or module_sys: no .version file
    False or None: .version file with faux number
    first_installed: we maintain first installed version number
    last_installed: version is updated to last installed
    """
    client = init_client(str(tmp_path), "tcl", "singularity", remote=remote)

    # Customize config settings
    client.settings.set("default_version", default_version)

    # Install known tag
    client.install("python:3.9.2-alpine")

    # Get paths
    module_dir = os.path.join(client.settings.module_base, "python")
    version_file = os.path.join(module_dir, ".version")

    if default_version in ["module_sys", True]:
        assert not os.path.exists(version_file)

    elif default_version in [False, None]:
        assert os.path.exists(version_file)
        content = shpc.utils.read_file(version_file)
        assert "please_specify_a_version_number" in content

    elif default_version == "first_installed":
        assert os.path.exists(version_file)
        content = shpc.utils.read_file(version_file)
        assert "3.9.2-alpine" in content
        client.install("python:3.9.5-alpine")
        content = shpc.utils.read_file(version_file)
        assert "3.9.2-alpine" in content

    elif default_version == "last_installed":
        assert os.path.exists(version_file)
        content = shpc.utils.read_file(version_file)
        assert "3.9.2-alpine" in content
        client.install("python:3.9.5-alpine")
        content = shpc.utils.read_file(version_file)
        assert "3.9.5-alpine" in content


@pytest.mark.parametrize(
    "default_version,remote",
    [
        (True, True),
        (False, True),
        ("module_sys", True),
        (None, True),
        ("first_installed", True),
        ("last_installed", True),
        (True, False),
        (False, False),
        ("module_sys", False),
        (None, False),
        ("first_installed", False),
        ("last_installed", False),
    ],
)
def test_lmod_default_version(tmp_path, default_version, remote):
    """
    Test lmod (lua) default versions.

    True or module_sys: file with non-existent version number
    False or None: no .version file
    first_installed: we maintain first installed version number
    last_installed: version is updated to last installed
    """
    client = init_client(str(tmp_path), "lmod", "singularity", remote=remote)

    # Customize config settings
    client.settings.set("default_version", default_version)

    # Install known tag
    client.install("python:3.9.2-alpine")

    # Get paths
    module_dir = os.path.join(client.settings.module_base, "python")
    version_file = os.path.join(module_dir, ".version")

    if default_version in ["module_sys", True]:
        assert os.path.exists(version_file)
        content = shpc.utils.read_file(version_file)
        assert "please_specify_a_version_number" in content

    elif default_version in [False, None]:
        assert not os.path.exists(version_file)

    elif default_version == "first_installed":
        assert os.path.exists(version_file)
        content = shpc.utils.read_file(version_file)
        assert "3.9.2-alpine" in content
        client.settings.set("default_version", default_version)
        client.install("python:3.9.5-alpine")
        content = shpc.utils.read_file(version_file)
        assert "3.9.2-alpine" in content

    elif default_version == "last_installed":
        assert os.path.exists(version_file)
        content = shpc.utils.read_file(version_file)
        assert "3.9.2-alpine" in content
        client.install("python:3.9.5-alpine")
        content = shpc.utils.read_file(version_file)
        assert "3.9.5-alpine" in content


@pytest.mark.parametrize(
    "module_sys,remote",
    [("lmod", True), ("tcl", True), ("lmod", False), ("tcl", False)],
)
def test_docgen(tmp_path, module_sys, remote):
    """
    Test docgen
    """
    client = init_client(str(tmp_path), module_sys, "singularity", remote=remote)
    client.install("python:3.9.2-slim")
    out = io.StringIO()
    docs = client.docgen("python:3.9.2-slim", out=out)
    docs = docs.getvalue()
    assert "python:3.9.2-slim" in docs


@pytest.mark.parametrize(
    "module_sys,container_tech,remote",
    [
        ("lmod", "singularity", True),
        ("lmod", "podman", True),
        ("tcl", "singularity", True),
        ("tcl", "podman", True),
        ("lmod", "singularity", False),
        ("lmod", "podman", False),
        ("tcl", "singularity", False),
        ("tcl", "podman", False),
    ],
)
def test_inspect(tmp_path, module_sys, container_tech, remote):
    """
    Test inspect
    """
    client = init_client(str(tmp_path), module_sys, container_tech, remote=remote)
    client.install("python:3.9.2-slim")
    # Python won't have much TODO we should test a custom container
    metadata = client.inspect("python:3.9.2-slim")
    if container_tech == "singularity":
        assert "attributes" in metadata
    else:
        assert isinstance(metadata, list)


@pytest.mark.parametrize(
    "module_sys,remote",
    [
        ("lmod", True),
        ("tcl", True),
        ("lmod", False),
        ("tcl", False),
    ],
)
def test_namespace_and_show(tmp_path, module_sys, remote):
    """
    Test namespace and show
    """
    client = init_client(str(tmp_path), module_sys, "singularity", remote=remote)
    client.show("vanessa/salad:latest")

    with pytest.raises(SystemExit):
        client.show("salad:latest")
    client.settings.set("namespace", "vanessa")
    client.show("salad:latest")
    client.settings.set("namespace", None)


@pytest.mark.parametrize(
    "module_sys,container_tech,remote",
    [
        ("lmod", "singularity", True),
        ("lmod", "podman", True),
        ("tcl", "singularity", True),
        ("tcl", "podman", True),
        ("lmod", "singularity", False),
        ("lmod", "podman", False),
        ("tcl", "singularity", False),
        ("tcl", "podman", False),
    ],
)
def test_check(tmp_path, module_sys, container_tech, remote):
    """
    Test check
    """
    client = init_client(str(tmp_path), module_sys, container_tech, remote=remote)
    client.install("vanessa/salad:latest")
    client.check("vanessa/salad:latest")


@pytest.mark.parametrize(
    "module_sys,remote",
    [("lmod", True), ("tcl", True), ("lmod", False), ("tcl", False)],
)
def test_install_local(tmp_path, module_sys, remote):
    """
    Test adding a custom container associated with an existing recipe
    """
    client = init_client(str(tmp_path), module_sys, "singularity", remote=remote)

    # Create a copy of the latest image to add
    container = os.path.join(str(tmp_path), "salad_latest.sif")
    shutil.copyfile(os.path.join(here, "testdata", "salad_latest.sif"), container)

    # It still needs to be a known tag!
    with pytest.raises(SystemExit):
        client.install(
            "quay.io/biocontainers/samtools:1.2--0", container_image=container
        )

    # This should install our custom image using samtools metadata
    container_image = "quay.io/biocontainers/samtools:1.10--h2e538c0_3"
    client.install(container_image, container_image=container)
    assert os.path.basename(client.get(container_image)) == os.path.basename(container)


@pytest.mark.parametrize(
    "module_sys,remote",
    [("lmod", True), ("tcl", True), ("lmod", False), ("tcl", False)],
)
def test_add(tmp_path, module_sys, remote):
    """
    Test adding a custom container
    """
    client = init_client(str(tmp_path), module_sys, "singularity", remote=remote)

    # Create a copy of the latest image to add
    container = os.path.join(str(tmp_path), "salad_latest.sif")
    shutil.copyfile(os.path.join(here, "testdata", "salad_latest.sif"), container)

    # Add only works for local filesystem registry
    if remote:
        with pytest.raises(SystemExit):
            client.add(container, "dinosaur/salad:latest")
        return

    client.add(container, "dinosaur/salad:latest")

    # Ensure this creates a container.yaml in the registry
    container_yaml = os.path.join(
        client.settings.registry[0], "dinosaur", "salad", "container.yaml"
    )
    assert os.path.exists(container_yaml)

    # Add does not install!
    with pytest.raises(SystemExit):
        client.get("dinosaur/salad:latest")
    client.install("dinosaur/salad:latest")
    assert client.get("dinosaur/salad:latest")


def test_remove(tmp_path):
    """
    Test removing a container recipe
    """
    client = init_client(str(tmp_path), "lmod", "singularity")

    # Create temporary registry that will be empty
    registry_path = os.path.join(tmp_path, "registry")
    client.settings.registry = [registry_path]
    os.makedirs(registry_path)
    client.reload_registry()
    assert client.settings.filesystem_registry == registry_path

    # Wrap local test filesystem registry and add module to it
    test_registry_path = os.path.join(here, "testdata", "registry")
    test_registry = registry.Filesystem(test_registry_path)
    module = "dinosaur/salad"

    client.registry.sync_from_remote(test_registry, module)

    # It should exist in the registry
    assert client.registry.exists(module) is not None
    # Remove the module (with force)
    client.remove(module, force=True)
    assert client.registry.exists(module) is None


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
def test_upgrade_software_with_force(
    tmp_path, module_sys, module_file, container_tech, remote, dryrun
):
    """
    Test upgrading a software where uninstalling older versions and installing latest version to view is also done.
    """
    client = init_client(str(tmp_path), module_sys, container_tech, remote=remote)

    # Install an outdated version of a software
    client.install("quay.io/biocontainers/samtools:1.18--h50ea8bc_1")

    # Create the default view if it doesn't exist
    view_handler = views.ViewsHandler(
        settings_file=client.settings.settings_file, module_sys=module_sys
    )
    assert "mpi" not in client.views
    view_handler.create("mpi")
    client.detect_views()
    assert "mpi" in client.views
    view = client.views["mpi"]
    assert view.path == os.path.join(tmp_path, "views", "mpi") and os.path.exists(
        view.path
    )
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
        module_dir = os.path.join(
            client.settings.module_base,
            "quay.io/biocontainers/samtools",
            latest_version,
        )
        assert os.path.exists(module_dir), "Latest version directiory should exist."
        module_file_path = os.path.join(module_dir, module_file)
        assert os.path.exists(
            module_file_path
        ), "Latest version's module files should be installed."

        # Check if the older version's module directory was removed and if its module files were uninstalled
        module_dir_old = os.path.join(
            client.settings.module_base,
            "quay.io/biocontainers/samtools",
            "1.18--h50ea8bc_1",
        )
        assert not os.path.exists(module_dir_old), "Older version should be uninstalled"
        module_file_path = os.path.join(module_dir_old, module_file)
        assert not os.path.exists(
            module_file_path
        ), "Older version's module files should be uninstalled."

        # Ensure the latest version was added to the view
        assert client.views["mpi"].exists(
            module_dir
        ), "Upgraded software should be added to the view 'mpi'"

    # Verify that the latest version of the software was not installed if dry-run is TRUE
    else:
        module_dir = os.path.join(
            client.settings.module_base,
            "quay.io/biocontainers/samtools",
            latest_version,
        )
        assert not os.path.exists(module_dir), "Latest version should not be installed."
        module_file_path = os.path.join(module_dir, module_file)
        assert not os.path.exists(
            module_file_path
        ), "Latest version's module files should not be installed."


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
def test_upgrade_software_without_force(
    mock_confirm_action, tmp_path, module_sys, module_file, container_tech, remote
):
    """
    Test upgrading a software where uninstalling older versions and installing latest version to view is not done.
    """
    client = init_client(str(tmp_path), module_sys, container_tech, remote=remote)

    # Install an outdated version of a software
    client.install("quay.io/biocontainers/samtools:1.18--h50ea8bc_1")

    # Create the default view if it doesn't exist
    view_handler = views.ViewsHandler(
        settings_file=client.settings.settings_file, module_sys=module_sys
    )
    assert "mpi" not in client.views
    view_handler.create("mpi")
    client.detect_views()
    assert "mpi" in client.views
    view = client.views["mpi"]
    assert view.path == os.path.join(tmp_path, "views", "mpi") and os.path.exists(
        view.path
    )
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
    module_dir = os.path.join(
        client.settings.module_base, "quay.io/biocontainers/samtools", latest_version
    )
    assert os.path.exists(module_dir), "Latest version directiory should exist."
    module_file_path = os.path.join(module_dir, module_file)
    assert os.path.exists(
        module_file_path
    ), "Latest version's module files should be installed."

    # Ensure the older version's module directory still exists and its module files were not uninstalled
    module_dir_old = os.path.join(
        client.settings.module_base,
        "quay.io/biocontainers/samtools",
        "1.18--h50ea8bc_1",
    )
    assert os.path.exists(module_dir_old), "Old version should not be uninstalled"
    module_file_path = os.path.join(module_dir_old, module_file)
    assert os.path.exists(
        module_file_path
    ), "Older version's module files should not be uninstalled."

    # Ensure the latest version was not added to the view
    assert not client.views["mpi"].exists(
        module_dir
    ), "Upgraded software should not added to the view 'mpi'"


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
def test_upgrade_with_latest_already_installed(
    tmp_path, module_sys, module_file, container_tech, remote
):
    client = init_client(str(tmp_path), module_sys, container_tech, remote=remote)

    # Load the container configuration for the software and get is latest version
    name = client.add_namespace("quay.io/biocontainers/samtools")
    config = client._load_container(name)
    latest_version = glv(name, config)

    # Install an outdated and the latest version of a software
    client.install(f"quay.io/biocontainers/samtools:{latest_version}")
    client.install("quay.io/biocontainers/samtools:1.18--h50ea8bc_1")

    # Verify the latest version's module directory exists and module files were installed
    module_dir = os.path.join(
        client.settings.module_base, "quay.io/biocontainers/samtools", latest_version
    )
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
    assert (
        module_dir_mtime_after == module_dir_mtime_before
    ), "Upgrade should not occur if latest is installed already."


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
def test_upgrade_all_software(
    tmp_path, module_sys, module_file, container_tech, remote
):
    """
    Test upgrading a software where uninstalling older versions and installing latest version to view is also done.
    """
    client = init_client(str(tmp_path), module_sys, container_tech, remote=remote)

    # Install two different outdated software
    client.install("quay.io/biocontainers/samtools:1.18--h50ea8bc_1")
    client.install("quay.io/biocontainers/bwa:0.7.18--he4a0461_0")

    # Create the default view if it doesn't exist
    view_handler = views.ViewsHandler(
        settings_file=client.settings.settings_file, module_sys=module_sys
    )
    assert "mpi" not in client.views
    view_handler.create("mpi")
    client.detect_views()
    assert "mpi" in client.views
    view = client.views["mpi"]
    assert view.path == os.path.join(tmp_path, "views", "mpi") and os.path.exists(
        view.path
    )
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
        assert os.path.exists(
            module_file_path
        ), "Latest version's module files should be installed."

        for older_version in versions:
            # Check if the older version's module directory was removed and if its module files were uninstalled
            module_dir_old = os.path.join(
                client.settings.module_base, software, older_version
            )
            assert not os.path.exists(
                module_dir_old
            ), "Older version should be uninstalled"
            module_file_path = os.path.join(module_dir_old, module_file)
            assert not os.path.exists(
                module_file_path
            ), "Older version's module files should be uninstalled."

        # Ensure the latest versions were added to the view
        assert client.views["mpi"].exists(
            module_dir
        ), "Upgraded software should be added to the view 'mpi'"


@pytest.mark.parametrize(
    "module_sys,module_file,container_tech,remote,update_containers",
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
def test_reinstall_specific_software_version(
    tmp_path, module_sys, module_file, container_tech, remote, update_containers
):
    """
    Test reinstalling a specific version of a software.
    """
    client = init_client(str(tmp_path), module_sys, container_tech, remote=remote)

    # Install a specific version of a software
    client.install("quay.io/biocontainers/samtools:1.20--h50ea8bc_0")

    # Create the default view if it doesn't exist
    view_handler = views.ViewsHandler(
        settings_file=client.settings.settings_file, module_sys=module_sys
    )
    assert "mpi" not in client.views
    view_handler.create("mpi")
    client.detect_views()
    assert "mpi" in client.views
    view = client.views["mpi"]
    assert view.path == os.path.join(tmp_path, "views", "mpi") and os.path.exists(
        view.path
    )
    assert os.path.exists(view.config_path)
    assert view._config["view"]["name"] == "mpi"
    assert not view._config["view"]["modules"]
    assert not view._config["view"]["system_modules"]

    # Install the specific version to a view
    client.view_install("mpi", "quay.io/biocontainers/samtools:1.20--h50ea8bc_0")

    # Verify its container's existence
    container_dir = os.path.join(
        client.settings.container_base,
        "quay.io/biocontainers/samtools",
        "1.20--h50ea8bc_0",
    )
    assert os.path.exists(container_dir)

    # Get modification time of its container before reinstall
    container_mtime_before = os.path.getmtime(container_dir)

    # Reinstall the specific version
    client.reinstall(
        "quay.io/biocontainers/samtools:1.20--h50ea8bc_0",
        update_containers=update_containers,
    )

    # Verify that it was reinstalled
    module_dir = os.path.join(
        client.settings.module_base,
        "quay.io/biocontainers/samtools",
        "1.20--h50ea8bc_0",
    )
    assert os.path.exists(module_dir)

    # Verify that its module files were reinstalled
    module_file_path = os.path.join(module_dir, module_file)
    assert os.path.exists(module_file_path)

    # Get modification time of the container after reinstall
    container_mtime_after = os.path.getmtime(container_dir)

    # Verify that its container was preserved or updated depending on update_container flag
    if update_containers:
        assert (
            container_mtime_after > container_mtime_before
        ), "Container should be updated when update_containers=True."
    else:
        assert (
            container_mtime_after == container_mtime_before
        ), "Container should be preserved when update_containers=False."

    # Check if it was restored to its views
    for view_name in client.views.keys():
        assert client.views[view_name].exists(
            module_dir
        ), f"Software was not restored to view: {view_name}"


@pytest.mark.parametrize(
    "module_sys,module_file,container_tech,remote,update_containers",
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
def test_reinstall_all_software_versions(
    tmp_path, module_sys, module_file, container_tech, remote, update_containers
):
    """
    Test reinstalling all versions of a specific software.
    """
    client = init_client(str(tmp_path), module_sys, container_tech, remote=remote)

    # Install two versions of a software
    client.install("quay.io/biocontainers/samtools:1.20--h50ea8bc_0")
    client.install("quay.io/biocontainers/samtools:1.20--h50ea8bc_1")

    # Create the default view if it doesn't exist
    view_handler = views.ViewsHandler(
        settings_file=client.settings.settings_file, module_sys=module_sys
    )
    assert "mpi" not in client.views
    view_handler.create("mpi")
    client.detect_views()
    assert "mpi" in client.views
    view = client.views["mpi"]
    assert view.path == os.path.join(tmp_path, "views", "mpi") and os.path.exists(
        view.path
    )
    assert os.path.exists(view.config_path)
    assert view._config["view"]["name"] == "mpi"
    assert not view._config["view"]["modules"]
    assert not view._config["view"]["system_modules"]

    # Install both versions to a view
    client.view_install("mpi", "quay.io/biocontainers/samtools:1.20--h50ea8bc_0")
    client.view_install("mpi", "quay.io/biocontainers/samtools:1.20--h50ea8bc_1")

    # Verify their container's existence
    container_0_dir = os.path.join(
        client.settings.container_base,
        "quay.io/biocontainers/samtools",
        "1.20--h50ea8bc_0",
    )
    container_1_dir = os.path.join(
        client.settings.container_base,
        "quay.io/biocontainers/samtools",
        "1.20--h50ea8bc_1",
    )
    assert os.path.exists(container_0_dir)
    assert os.path.exists(container_1_dir)

    # Get modification time of their container before reinstall
    container_0_mtime_before = os.path.getmtime(container_0_dir)
    container_1_mtime_before = os.path.getmtime(container_1_dir)

    # Reinstall all versions of the specific software
    client.reinstall(
        "quay.io/biocontainers/samtools", update_containers=update_containers
    )

    # Verify that both versions exist after reinstall
    module_0_dir = os.path.join(
        client.settings.module_base,
        "quay.io/biocontainers/samtools",
        "1.20--h50ea8bc_0",
    )
    module_1_dir = os.path.join(
        client.settings.module_base,
        "quay.io/biocontainers/samtools",
        "1.20--h50ea8bc_1",
    )
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
        assert (
            container_0_mtime_after > container_0_mtime_before
        ), "Container should be updated when update_containers=True."
        assert (
            container_1_mtime_after > container_1_mtime_before
        ), "Container should be updated when update_containers=True."
    else:
        assert (
            container_0_mtime_after == container_0_mtime_before
        ), "Container should be preserved when update_containers=False."
        assert (
            container_1_mtime_after == container_1_mtime_before
        ), "Container should be preserved when update_containers=False."

    # Check if both versions were restored to their views
    for view_name in client.views.keys():
        assert client.views[view_name].exists(
            module_0_dir
        ), f"Software was not restored to view: {view_name}"
    for view_name in client.views.keys():
        assert client.views[view_name].exists(
            module_1_dir
        ), f"Software was not restored to view: {view_name}"


@pytest.mark.parametrize(
    "module_sys,module_file,container_tech,remote,update_containers",
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
def test_reinstall_all_software(
    tmp_path, module_sys, module_file, container_tech, remote, update_containers
):
    """
    Test reinstalling all installed software.
    """
    client = init_client(str(tmp_path), module_sys, container_tech, remote=remote)

    # Install two different software
    client.install("quay.io/biocontainers/samtools:1.20--h50ea8bc_0")
    client.install("quay.io/biocontainers/bwa:0.7.18--he4a0461_0")

    # Create the default view if it doesn't exist
    view_handler = views.ViewsHandler(
        settings_file=client.settings.settings_file, module_sys=module_sys
    )
    assert "mpi" not in client.views
    view_handler.create("mpi")
    client.detect_views()
    assert "mpi" in client.views
    view = client.views["mpi"]
    assert view.path == os.path.join(tmp_path, "views", "mpi") and os.path.exists(
        view.path
    )
    assert os.path.exists(view.config_path)
    assert view._config["view"]["name"] == "mpi"
    assert not view._config["view"]["modules"]
    assert not view._config["view"]["system_modules"]

    # Install both software to a view
    client.view_install("mpi", "quay.io/biocontainers/samtools:1.20--h50ea8bc_0")
    client.view_install("mpi", "quay.io/biocontainers/bwa:0.7.18--he4a0461_0")

    # Verify the existence of their containers
    container_samtools_dir = os.path.join(
        client.settings.container_base,
        "quay.io/biocontainers/samtools",
        "1.20--h50ea8bc_0",
    )
    container_bwa_dir = os.path.join(
        client.settings.container_base,
        "quay.io/biocontainers/bwa",
        "0.7.18--he4a0461_0",
    )
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
    module_samtools_dir = os.path.join(
        client.settings.module_base,
        "quay.io/biocontainers/samtools",
        "1.20--h50ea8bc_0",
    )
    module_bwa_dir = os.path.join(
        client.settings.module_base, "quay.io/biocontainers/bwa", "0.7.18--he4a0461_0"
    )
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
        assert (
            container_samtools_mtime_after > container_samtools_mtime_before
        ), "Container should be updated when update_containers=True."
        assert (
            container_bwa_mtime_after > container_bwa_mtime_before
        ), "Container should be updated when update_containers=True."

    else:
        assert (
            container_samtools_mtime_after == container_samtools_mtime_before
        ), "Container should be preserved when update_containers=False."
        assert (
            container_bwa_mtime_after == container_bwa_mtime_before
        ), "Container should be preserved when update_containers=False."

    # Check if both software were restored to their views
    for view_name in client.views.keys():
        assert client.views[view_name].exists(
            module_samtools_dir
        ), f"Software was not restored to view: {view_name}"
    for view_name in client.views.keys():
        assert client.views[view_name].exists(
            module_bwa_dir
        ), f"Software was not restored to view: {view_name}"
