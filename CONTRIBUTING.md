# Contributing to MxOps

:+1::tada: First off, thanks for taking the time to contribute! :tada::+1:

The following is a set of guidelines for contributing to the MxOps package which is hosted by the [Catenscia Organization](https://github.com/Catenscia) on Github. These are mostly guidelines, not rules. Use your best judgment, and feel free to propose changes to this document in a pull request.

## Reporting an issue

If you encountered an issue or a bug, don't hesitate to write a detailed issue in the repo. the guidelines are [here](./.github/ISSUE_TEMPLATE/bug_report.md)

## Submitting changes

If you fixed an issue or implemented a new feature, please send a pull request with a clear list of what you've done and make sure all of your commits are atomic
(one feature/action/change per commit).
Please write clean commits messages by following the [conventional convention](https://www.conventionalcommits.org/en/v1.0.0/). The automated bump version workflow relies on this convention to opperate well.

To submit your changes, follow this steps:

- Fork this repo
- create a new branch from `develop` and call it `fix...`, `feature...`, `docs...` or else depending on your needs (see below)
- make your changes and commits continuously to your local branch
- If you have a changed or added a functionnality, make sure to add unit tests and/or integration tests to cover your change (don't hesitate to reach out if you need any help)
- execute locally `bash scripts/check_python_code.sh` and ensure that all unit tests pass
- execute locally `bash scripts/launch_integration_tests.sh <devnet/localnet>` and ensure that all integration tests pass (see [here for help](./integration_tests/README.md))
- submit a PR from your branch to the `develop` branch of this repo

## Branch names

Banches names should reflect the type of change they bring.
The examples below should fit most needs.

| **Change type**   | Description                                            | Name                       |
|-------------------|--------------------------------------------------------|----------------------------|
| **Feature**       | For any feature that will be added to the project      | `feature_<feature_name>`   |
| **Fix**           | For any bug fix on the project                         | `fix_<bug_name>`           |
| **Refactor**      | For any change that do not impact the functionalities  | `refactor_<refactor_name>` |
| **Test**          | For any test(s) that will be added to the project      | `test_<test_name>`         |
| **Documentation** | For any change in the documentation                    | `docs_<change_name>`       |

Many thanks! :heart: :heart: :heart:
