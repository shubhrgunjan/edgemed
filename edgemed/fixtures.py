"""Only these reviewed synthetic reference templates can cross the sync boundary."""

from uuid import uuid5, NAMESPACE_URL

REFERENCES = {
    "reference-hydration": {
        "title": "Hydration observation checklist",
        "variants": [
            "Synthetic training reference: record oral intake, temperature, and reported dizziness during a hydration observation.",
            "Synthetic training reference: hydration observations include intake, temperature, dizziness, and an explicit observation time.",
            "Synthetic training reference: hydration observations include intake, temperature, dizziness, and a second reviewer field.",
        ],
    },
    "reference-handoff": {
        "title": "Offline handoff checklist",
        "variants": [
            "Synthetic training reference: an offline handoff preserves observation time, source, and unresolved contradictions.",
            "Synthetic training reference: an offline handoff includes observation time, source, unresolved contradictions, and review owner.",
            "Synthetic training reference: an offline handoff includes observation time, source, unresolved contradictions, and next review time.",
        ],
    },
}


def fixture_id(name):
    return str(uuid5(NAMESPACE_URL, "https://local.edgemed.invalid/fixtures/" + name))


def initial_revision(name):
    return str(uuid5(NAMESPACE_URL, "https://local.edgemed.invalid/revisions/" + name))


NOTES = [
    {
        "title": "Persistent cough and fever",
        "content": "Synthetic patient SYN-001 reports persistent dry cough and elevated temperature for two days. Observation awaits review.",
        "subject": "SYN-001",
        "category": "OBSERVATION",
        "importance": 0.7,
    },
    {
        "title": "Penicillin allergy reported",
        "content": "Synthetic patient SYN-002 reports a penicillin allergy with prior rash. Source is a training fixture, not a verified clinical diagnosis.",
        "subject": "SYN-002",
        "category": "ALLERGY",
        "importance": 0.95,
    },
    {
        "title": "Blood pressure observation",
        "content": "Synthetic patient SYN-003 has a training blood pressure reading of 128/82 mmHg. Record the measurement with its observation time.",
        "subject": "SYN-003",
        "category": "VITAL_SIGN",
        "importance": 0.45,
    },
    {
        "title": "Private follow-up note",
        "content": "Synthetic patient SYN-001 shares a private follow-up observation. This note and its embedding must remain on this device.",
        "subject": "SYN-001",
        "category": "NOTE",
        "privacy": "HIGHLY_SENSITIVE",
        "importance": 0.6,
    },
    {
        "title": "Dizziness after limited fluid intake",
        "content": "Synthetic patient SYN-004 reports dizziness and limited fluid intake. This is an observation for the offline demonstration.",
        "subject": "SYN-004",
        "category": "OBSERVATION",
        "importance": 0.65,
    },
]
