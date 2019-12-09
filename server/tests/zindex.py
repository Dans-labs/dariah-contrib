"""Testing the Contribution tool

## Auxiliary

`client`
:   Wrap the Flask test-`client` in something more capable.

`clean`
:   Provides a clean slate test database

`starters`
:   Provide test functions with a well-defined initial state.

`helpers`
:   Low-level library functions for testers.

`subtest`
:   Higher-level `assert` functions.

`example`
:   Concrete example values for testers to work with.

`analysis`
:   Interpret the request log after testing.

## Test batches

The following files can be run individually, or as part of an all-tests-run,
in alphabetical order of the file names.

### Tests: setup

`test_10_factory10`
:   How the app is set up.

`test_20_users10`
:   Getting to know all users.

### Tests: Contributions

`test_30_contrib10`
:   Getting started with contributions.

`test_30_contrib20`
:   Modifying contribution fields that are typed in by the user.

`test_30_contrib30`
:   Modifying contribution fields that have values in value tables.

`test_30_contrib40`
:   Checking the visibility of sensitive fields.

### Tests: assessments

`test_40_assess10`
:   Starting an assessment.

`test_40_assess20`
:   Starting a second assessment.

`test_40_assess30`
:   Filling out an assessment.

`test_40_assess30`
:   Assigning reviewers.

### Tests: Reviews: filling out and deciding.

`test_50_review10`
:   Checking out the sidebar for each user when an assessment is under review.

`test_50_review20`
:   Starting a review, filling it out, and deciding.

`test_50_assess30`
:   Revising and resubmitting assessments.

### Tests: contributions: selection.

`test_60_contrib10`
:   Selecting contributions.

"""

import test_10_factory10  # noqa
