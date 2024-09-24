__author__ = "Ausbeth Aguguo"
__copyright__ = "Copyright 2021-2024, Ausbeth Aguguo"
__license__ = "MPL 2.0"

#!/bin/bash

echo
echo "************** START: test_client.sh **********************"

# Create temporary testing directory
echo "Creating temporary directory to work in."
here="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
shpc_root="$( dirname "${here}" )"

. $here/helpers.sh

# Create temporary testing directory
tmpdir=$(mktemp -d)
output=$(mktemp ${tmpdir:-/tmp}/shpc_test.XXXXXX)
printf "Created temporary directory to work in. ${tmpdir}\n"

# Make sure it's installed
if ! command -v shpc &> /dev/null
then
    printf "shpc is not installed\n"
    exit 1
else
    printf "shpc is installed\n"
fi

# Create a temporary config file, module folder, etc.
settings=$tmpdir/settings.yaml
modules=$tmpdir/modules
cp $shpc_root/settings.yml $settings

# Prepare a container to install
container=$tmpdir/salad_latest.sif
cp $here/testdata/salad_latest.sif $container

echo
echo "#### Testing base client "
runTest 0 $output shpc --settings-file $settings --version

echo
echo "#### Testing upgrade "
runTest 0 $output shpc --settings-file $settings upgrade --help
runTest 0 $output shpc --settings-file $settings install quay.io/biocontainers/samtools:1.20--h50ea8bc_0
runTest 0 $output shpc --settings-file $settings install quay.io/biocontainers/bioconductor-bags:2.40.0--r43ha9d7317_0
runTest 0 $output shpc --settings-file $settings install quay.io/biocontainers/bwa:0.7.18--he4a0461_1
runTest 0 $output shpc --settings-file $settings upgrade quay.io/biocontainers/samtools --dry-run
runTest 0 $output shpc --settings-file $settings upgrade quay.io/biocontainers/samtools --force
runTest 0 $output shpc --settings-file $settings upgrade --all --dry-run
runTest 0 $output shpc --settings-file $settings upgrade --all --force