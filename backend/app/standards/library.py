"""
Shield EPC -- Standards Clause Library
Phase 4, Milestone 4.1 (locked design, resolver-only access)

Read-only clause data for the standards already referenced by the
tenant hazard library (app.hazards.library.Hazard.applicable_standards).
Every clause's applicable_hazard_ids draws exclusively from the six
existing tenant hazard IDs -- no new hazard vocabulary is introduced
here.

This module holds data only. It exposes no accessor functions and no
public names: app.standards.resolver is the sole read path, per the
locked "Resolver-only access" decision. Do not import
_STANDARD_LIBRARY from outside app.standards.
"""

from types import MappingProxyType

from app.standards.models import StandardClause

_CLAUSES_PART1: dict[str, StandardClause] = {
    "iso45001-work-at-height": StandardClause(
        clause_id="iso45001-work-at-height",
        standard_name="ISO 45001:2018",
        clause_reference="Clause 8.1.2",
        requirement_summary=(
            "Operational controls for work at height must include fall "
            "protection systems and a rescue arrangement established "
            "before work begins."
        ),
        applicable_hazard_ids=("work_at_height",),
    ),
    "bocw-reg116-work-at-height": StandardClause(
        clause_id="bocw-reg116-work-at-height",
        standard_name="BOCW Act 1996, Regulation 116",
        clause_reference="Regulation 116",
        requirement_summary=(
            "Sets minimum requirements for guarding of openings and edge "
            "protection on construction sites where persons work at "
            "height."
        ),
        applicable_hazard_ids=("work_at_height",),
    ),
    "iso45001-hot-work": StandardClause(
        clause_id="iso45001-hot-work",
        standard_name="ISO 45001:2018",
        clause_reference="Clause 8.1.2",
        requirement_summary=(
            "Requires a documented permit-to-work process for hazardous "
            "hot work activities such as welding, cutting, and grinding."
        ),
        applicable_hazard_ids=("hot_work",),
    ),
    "factories-s36-hot-work": StandardClause(
        clause_id="factories-s36-hot-work",
        standard_name="Factories Act 1948, Section 36",
        clause_reference="Section 36",
        requirement_summary=(
            "Restricts work involving fire or explosion risk unless "
            "precautions such as clearing combustibles and providing "
            "fire watch are taken first."
        ),
        applicable_hazard_ids=("hot_work",),
    ),
}

_CLAUSES_PART2: dict[str, StandardClause] = {
    "factories-s36a-confined-space": StandardClause(
        clause_id="factories-s36a-confined-space",
        standard_name="Factories Act 1948, Section 36A",
        clause_reference="Section 36A",
        requirement_summary=(
            "Requires precautions, including atmospheric testing and "
            "standby arrangements, before entry into confined spaces."
        ),
        applicable_hazard_ids=("confined_space",),
    ),
    "iso45001-confined-space": StandardClause(
        clause_id="iso45001-confined-space",
        standard_name="ISO 45001:2018",
        clause_reference="Clause 8.1.2",
        requirement_summary=(
            "Requires operational controls for confined space entry, "
            "including permit issuance and emergency retrieval "
            "arrangements."
        ),
        applicable_hazard_ids=("confined_space",),
    ),
    "factories-s29-lifting": StandardClause(
        clause_id="factories-s29-lifting",
        standard_name="Factories Act 1948, Section 29",
        clause_reference="Section 29",
        requirement_summary=(
            "Requires lifting machinery and gear to be of sound "
            "construction, properly maintained, and tested at "
            "prescribed intervals."
        ),
        applicable_hazard_ids=("lifting_operations",),
    ),
    "iso45001-lifting": StandardClause(
        clause_id="iso45001-lifting",
        standard_name="ISO 45001:2018",
        clause_reference="Clause 8.1.2",
        requirement_summary=(
            "Requires a documented lift plan with competent-person "
            "approval before lifting operations commence."
        ),
        applicable_hazard_ids=("lifting_operations",),
    ),
    "factories-s34-electrical": StandardClause(
        clause_id="factories-s34-electrical",
        standard_name="Factories Act 1948, Section 34",
        clause_reference="Section 34",
        requirement_summary=(
            "Restricts work on or near live electrical equipment to "
            "authorized, competent persons following isolation "
            "procedures."
        ),
        applicable_hazard_ids=("electrical_isolation",),
    ),
    "iso45001-electrical": StandardClause(
        clause_id="iso45001-electrical",
        standard_name="ISO 45001:2018",
        clause_reference="Clause 8.1.2",
        requirement_summary=(
            "Requires lock-out/tag-out controls to be applied and "
            "verified before work on electrical equipment begins."
        ),
        applicable_hazard_ids=("electrical_isolation",),
    ),
    "bocw-reg132-excavation": StandardClause(
        clause_id="bocw-reg132-excavation",
        standard_name="BOCW Act 1996, Regulation 132",
        clause_reference="Regulation 132",
        requirement_summary=(
            "Requires shoring or battering of excavation walls above a "
            "specified depth and barricading of the excavation "
            "perimeter."
        ),
        applicable_hazard_ids=("excavation",),
    ),
    "iso45001-excavation": StandardClause(
        clause_id="iso45001-excavation",
        standard_name="ISO 45001:2018",
        clause_reference="Clause 8.1.2",
        requirement_summary=(
            "Requires a permit-to-work and an underground utility "
            "survey to be completed before excavation work commences."
        ),
        applicable_hazard_ids=("excavation",),
    ),
}

_STANDARD_LIBRARY: MappingProxyType[str, StandardClause] = MappingProxyType(
    {**_CLAUSES_PART1, **_CLAUSES_PART2}
)
