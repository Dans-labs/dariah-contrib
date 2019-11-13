# Tables with custom logic

Here are the particulars of our tables.

## Contrib

### Selection

Contributions can be *selected*  by National Coordinators.
Or they can be rejected.
After a selection decision, the contribution and itts associated assessments and reviews
become *frozen*. Nobody can modify them anymore.

??? note "Stray material"
    There might be stray assessment and reviews associated with a contribution, in the sense
    that they do not belong to the workflow. These stray records are not frozen, and may be deleted
    if the owner wishes to do so.

## Assessment

In particular the current score of the assessment is presented here. The score
is computed workflow function
[computeScore]({{repBase}}/server/control/workflow/compute.py)
and presented by 
[presentScore]({{repBase}}/server/control/cust/score.py)
.
Not only the score is presented, but also its derivation.

### Submission

It is presented whether the assessment currently counts as submitted for review,
and if yes, also the date-time of the last submission. In this case there is
also a button to withdraw the assessment from review.

If the assessment does not count as submitted, a submit button is presented.

??? caution "Permissions"
    This is not the whole truth, the presence of these action buttons is dependent
    on additional constraints, such as whether the current user has rights to
    submit, and whether the assessment is completen and whether the contribution
    is not frozen.

It can also be the case that the assessment has been reviewed with outcome `revise`.
In that case, the submit button changes into an `Enter revisions` button, and
later to `Submit for review (again)`. 

??? caution "Stalled"
    If the contribution has received an other *type* since the creation of this
    assessment, this assessment will count as *stalled*, and cannot be used for
    review.

    In this case, the criteria of the assessment are not the criteria by which the
    contribution should be assessed. So the system stalls this assessment. It is
    doomed, it can never be submitted. Unless you decide to change back the type of
    the contribution. If that is not an option, the best thing to do is to copy the
    worthwhile material from this assessment into a fresh assessment.

## CriteriaEntry

These records are meant to be shown as detail records of an assessment.
As such, they are part of a big form. Each record is a row in that form
in which the user can enter a score and state evidence for that score.

The display of the rows is such that completed entries are clearly differentiated
from incomplete ones.

## Review

The biggest task for review templates is to show the reviews
of both reviewers side by side, and to make the review editable
for the corresponding reviewer.

In doing so, the app needs to know the exact stage the review process is in,
to be able to temporarily lock reviews when they are considered by the final
reviewer.

This is responsible to present the reviewers with controls to make their decisions,
and present to other users the effects of those decisions.

## ReviewEntry

These records are meant to be shown as detail records of a review.
As such, they are part of a big form. Each record is a row in that form
in which the user can enter review comments.
