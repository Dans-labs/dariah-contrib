# Workflow Engine

## Description

The workflow engine of this app is a system to handle business logic.

Whereas the database consists of neutral things (fields, records, lists), the
workflow engine weaves additional attributes around it, that indicate additional
constraints.

These additional *workflow* attributes are computed by the server on the fly,
and then stored in a separate table in the database: `workflow`. From then on
the following happens with the workflow attributes:

*   the server uses the workflow info to enforce the business logic;
*   the server updates the workflow attributes after any insert/update/delete
    action.

## Realization

Workflow is realized at the server. Its
rules are specified in the code that is
[specific]({{repBase}}/server/control/cust}})
for the concepts of contribution, assessment, and review.

The engine itself is in
[workflow]({{repBase}}/server/control/workflow).

[compute.py]({{repBase}}/server/control/workflow/compute.py)
is responsible for computiong the workflow attributes for each contribution, and updating
them after changes.

[apply.py]({{repBase}}/server/control/workflow/apply.py)
is used to apply and enforce the workflow rules. 
