"""Held-out synthetic paraphrases; not clinical accuracy validation."""

import secrets
from pathlib import Path

from edgemed.fixtures import NOTES
from edgemed.models import CreateMemory
from edgemed.retrieval import Retrieval
from edgemed.store import Store

CASES = [
    (
        0,
        [
            "fever and coughing",
            "high temperature with respiratory symptoms",
            "persistent cough",
            "cough with raised temperature",
            "patient reports fever",
            "several days of coughing",
            "respiratory observation with fever",
            "temperature elevated and cough",
            "fever breathing complaint",
            "cough and fever history",
        ],
    ),
    (
        1,
        [
            "penicillin allergy",
            "rash after antibiotic",
            "allergic to penicillin",
            "reported penicillin reaction",
            "antibiotic hypersensitivity rash",
            "allergy history penicillin",
            "skin rash from penicillin",
            "medicine allergy penicillin",
            "previous penicillin rash",
            "avoid penicillin allergy record",
        ],
    ),
    (
        2,
        [
            "blood pressure",
            "blood pressure measurement",
            "pressure reading",
            "recorded blood pressure",
            "systolic diastolic measurement",
            "blood pressure vital sign",
            "pressure check observation",
            "blood pressure follow up",
            "arterial pressure reading",
            "blood pressure recorded today",
        ],
    ),
    (
        3,
        [
            "private follow up",
            "confidential follow-up",
            "sensitive follow up note",
            "private observation",
            "highly sensitive note",
            "confidential observation record",
            "private discussion follow up",
            "restricted follow up information",
            "sensitive follow-up history",
            "private follow-up conversation",
        ],
    ),
    (
        4,
        [
            "dizzy after drinking little water",
            "dizziness and low fluid intake",
            "poor hydration and dizziness",
            "not drinking enough and feeling dizzy",
            "lightheaded with little fluid",
            "dizziness hydration observation",
            "reduced water intake",
            "dizzy after low fluids",
            "fluid intake concern",
            "hydration history with dizziness",
        ],
    ),
]


def test_fifty_synthetic_paraphrases_find_expected_category(tmp_path):
    store = Store(tmp_path, secrets.token_hex(32))
    for note in NOTES:
        store.create(CreateMemory(**note))
    retrieval = Retrieval(store, Path(__file__).resolve().parents[1] / ".cache/models")
    while retrieval.drain():
        pass
    try:
        ranks = []
        for expected, queries in CASES:
            for query in queries:
                found = retrieval.search(query, limit=3)
                titles = [r["title"] for r in found]
                ranks.append(
                    titles.index(NOTES[expected]["title"]) + 1 if NOTES[expected]["title"] in titles else 99
                )
        assert sum(rank <= 3 for rank in ranks) / len(ranks) >= 0.9
        assert sum(rank == 1 for rank in ranks) / len(ranks) >= 0.7
    finally:
        retrieval.close()
        store.close()
