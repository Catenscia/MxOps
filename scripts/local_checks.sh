#!/bin/bash
set -e

scripts/check_python_code.sh
scripts/launch_tests.sh
scripts/build_doc.sh
scripts/build.sh