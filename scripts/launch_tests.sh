#!/bin/bash

coverage run -m pytest
EXIT=$?
coverage html

exit $EXIT
