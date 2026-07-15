"""
Shield EPC — Tenant Hazard Library
Phase 3, Step 1 (locked design, no free-text fallback)
"""

from dataclasses import dataclass
from types import MappingProxyType

from app.agents.base import InsufficientInformation


@dataclass(frozen=True)
class Hazard:
    hazard_id: str
    hazard_name: str
    default_controls: tuple[str, ...]
    required_ppe: tuple[str, ...]
    applicable_standards: tuple[str, ...]
_HAZARDS_PART1 = {
    "work_at_height": Hazard(
        hazard_id="work_at_height",
        hazard_name="Work at Height",
        default_controls=(
            "Fall protection system (harness + lanyard) mandatory above 1.8m",
            "Guardrails or edge protection on open sides",
            "Toe boards to prevent dropped objects",
            "Rescue plan in place before work commences",
        ),
        required_ppe=(
            "Full body harness",
            "Double lanyard with shock absorber",
            "Safety helmet with chin strap",
        ),
        applicable_standards=(
            "ISO 45001:2018",
            "BOCW Act 1996, Regulation 116",
        ),
    ),
    "hot_work": Hazard(
        hazard_id="hot_work",
        hazard_name="Hot Work (Welding/Cutting/Grinding)",
        default_controls=(
            "Hot work permit issued before start",
            "Fire watch present with extinguisher during and 30 min after work",
            "Combustibles cleared within 10m radius",
            "Gas cylinders secured upright with flashback arrestors",
        ),
        required_ppe=(
            "Welding helmet/goggles with correct shade",
            "Fire-resistant apron and gauntlets",
            "Safety boots",
        ),
        applicable_standards=(
            "ISO 45001:2018",
            "Factories Act 1948, Section 36",
        ),
    ),
    "confined_space": Hazard(
        hazard_id="confined_space",
        hazard_name="Confined Space Entry",
        default_controls=(
            "Confined space entry permit mandatory",
            "Atmospheric testing (O2, LEL, toxic gases) before and during entry",
            "Standby person at entry point with communication link",
            "Continuous ventilation where required",
        ),
        required_ppe=(
            "Gas detector (personal)",
            "Full body harness with retrieval line",
            "Appropriate respiratory protection based on atmosphere test",
        ),
        applicable_standards=(
            "ISO 45001:2018",
            "Factories Act 1948, Section 36A",
        ),
    ),
}
_HAZARDS_PART2 = {
    "lifting_operations": Hazard(
        hazard_id="lifting_operations",
        hazard_name="Lifting Operations",
        default_controls=(
            "Lift plan prepared and approved by competent person",
            "Crane and lifting gear inspected and certified (valid test certificates)",
            "Exclusion zone established under and around the load path",
            "Signalman/banksman assigned with clear communication protocol",
        ),
        required_ppe=(
            "Safety helmet",
            "High-visibility vest",
            "Safety boots",
        ),
        applicable_standards=(
            "ISO 45001:2018",
            "Factories Act 1948, Section 29",
        ),
    ),
    "electrical_isolation": Hazard(
        hazard_id="electrical_isolation",
        hazard_name="Electrical Isolation (LOTO)",
        default_controls=(
            "Lock-out/Tag-out procedure applied before work begins",
            "Isolation verified with voltage tester before touching conductors",
            "Only authorized electrical personnel to perform isolation",
            "Permit to work issued for electrical work above specified voltage threshold",
        ),
        required_ppe=(
            "Insulated gloves rated for system voltage",
            "Arc-rated face shield where applicable",
            "Insulated tools",
        ),
        applicable_standards=(
            "ISO 45001:2018",
            "Factories Act 1948, Section 34",
        ),
    ),
    "excavation": Hazard(
        hazard_id="excavation",
        hazard_name="Excavation",
        default_controls=(
            "Excavation permit issued before digging",
            "Underground utility survey/mapping completed before start",
            "Shoring or battering of excavation walls where depth exceeds 1.2m",
            "Barricading and warning signage around excavation perimeter",
        ),
        required_ppe=(
            "Safety helmet",
            "High-visibility vest",
            "Safety boots",
        ),
        applicable_standards=(
            "ISO 45001:2018",
            "BOCW Act 1996, Regulation 132",
        ),
    ),
}

HAZARD_CATALOG = MappingProxyType({**_HAZARDS_PART1, **_HAZARDS_PART2})


def get_hazard(hazard_id: str) -> Hazard:
    try:
        return HAZARD_CATALOG[hazard_id]
    except KeyError:
        raise InsufficientInformation(
            f"Unknown hazard_id '{hazard_id}': not present in tenant hazard library"
        )


def get_hazards(hazard_ids: tuple[str, ...]) -> tuple[Hazard, ...]:
    return tuple(get_hazard(hazard_id) for hazard_id in hazard_ids)
