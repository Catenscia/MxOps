#!/bin/bash
set -e

CHANGELOG=docs/source/dev_documentation/changelog.md

# Read the version from setup.cfg
version=$(grep "current_version" setup.cfg | awk -F "=" '{print $2}' | tr -d '[:space:]')

# Set the date in the desired format
date=$(date +"%Y-%m-%d")

# Find the line number of the "Unreleased" title in the changelog file
line_number=$(grep -n "## Unreleased" $CHANGELOG | cut -d ":" -f 1)

# Insert the new version and date information below the "Unreleased" title
sed -i "${line_number}a\\\n## ${version} - ${date}" $CHANGELOG