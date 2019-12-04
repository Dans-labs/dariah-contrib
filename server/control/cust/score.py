"""Handles assessment scores.
"""

from config import Names as N
from control.utils import pick as G, E
from control.html import HtmlElements as H


def presentScore(score, eid, derivation=True):
    """Presents the result of a score computation.

    It shows the overall score, but it can also expand a derivation of the
    overall score.

    Parameters
    ----------
    score: dict
        Quantities relevant to the score and its derivation
    eid: ObjectId
        Id of the assessment of which the score has been taken.
        Only used to give the score presentation a unique identifier on the
        interface, so that the derivation can be collapsed and expanded
        in the presence of other score presentations.
    derivation: boolean, optional `True`
        If `False`, the derivation will be suppressed.
    """

    overall = G(score, N.overall, default=0)
    relevantScore = G(score, N.relevantScore, default=0)
    relevantMax = G(score, N.relevantMax, default=0)
    relevantN = G(score, N.relevantN, default=0)
    allMax = G(score, N.allMax, default=0)
    allN = G(score, N.allN, default=0)
    irrelevantN = allN - relevantN

    fullScore = H.span(
        f"Score {overall}%", title="overall score of this assessment", cls="ass-score",
    )
    if not derivation:
        return fullScore

    scoreMaterial = H.div(
        [
            H.div(
                [
                    H.p(f"""This assessment scores {relevantScore} points."""),
                    H.p(
                        f"""For this type of contribution there is a total of
                          {allMax} points, divided over {allN} criteria.
                      """
                    ),
                    (
                        H.p(
                            f"""However,
                              {irrelevantN}
                              rule{" is " if irrelevantN == 1 else "s are"}
                              not applicable to this contribution,
                              which leaves the total amount to
                              {relevantMax} points,
                              divided over {relevantN} criteria.
                          """
                        )
                        if irrelevantN
                        else E
                    ),
                    H.p(
                        f"""The total score is expressed as a percentage:
                          the fraction of {relevantScore} scored points
                          with respect to {relevantMax} scorable points:
                          {overall}%.
                      """
                    ),
                ],
                cls="ass-score-deriv",
            ),
        ],
        cls="ass-score-box",
    )

    scoreWidget = H.detailx(
        (N.calc, N.dismiss),
        scoreMaterial,
        f"""{N.assessment}/{eid}/scorebox""",
        openAtts=dict(cls="button small", title="Show derivation"),
        closeAtts=dict(cls="button small", title="Hide derivation"),
    )
    return (fullScore, *scoreWidget)
