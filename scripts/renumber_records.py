"""Renumber PPRDB release records and their companion audit references.

Run after changing the admitted table, before publishing a release. PPR numbers
are positional release labels, not stable identifiers. Held/excluded claims use
the separate H namespace. A private crosswalk preserves traceability.
"""

from __future__ import annotations

import argparse
import csv
import re
from pathlib import Path


PPR_REFERENCE = re.compile(r"PPR-(\d+)(?:[–-](\d+))?")


def read_tsv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle, delimiter="\t")
        return list(reader.fieldnames or []), list(reader)


def write_tsv(path: Path, fields: list[str], rows: list[dict[str, str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, delimiter="\t", lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def renumber_release(site: Path, audit: Path) -> None:
    official_path = site / "plant_LR_final_verified.tsv"
    held_path = site / "held_or_excluded_candidates.tsv"
    decisions_path = site / "review_22_decisions.tsv"
    manuscript_path = audit / "manuscript_28_pair_validation.tsv"
    full_audit_path = audit / "existing_and_new_pair_audit.tsv"

    official_fields, official = read_tsv(official_path)
    held_fields, held = read_tsv(held_path)
    decision_fields, decisions = read_tsv(decisions_path)
    manuscript_fields, manuscript = read_tsv(manuscript_path)
    audit_fields, all_pairs = read_tsv(full_audit_path)

    old_official = [row["pair_id"] for row in official]
    old_held = [row["candidate_id"] for row in held]
    assert len(old_official) == len(set(old_official))
    assert len(old_held) == len(set(old_held))
    assert not set(old_official) & set(old_held)

    official_map = {old: f"PPR-{i}" for i, old in enumerate(old_official, 1)}
    held_map = {old: f"H-{i}" for i, old in enumerate(old_held, 1)}
    id_map = official_map | held_map
    crosswalk = []
    for row in official:
        old = row["pair_id"]
        crosswalk.append({
            "previous_id": old, "current_id": official_map[old],
            "disposition": "admitted", "species": row["species"],
            "ligand": row["ligand_tested"],
            "receptor": row["receptor_or_complex_tested"],
            "doi": row["primary_doi"],
        })
        row["pair_id"] = official_map[old]
    for row in held:
        old = row["candidate_id"]
        crosswalk.append({
            "previous_id": old, "current_id": held_map[old],
            "disposition": row["status"], "species": row["species"],
            "ligand": row["ligand"], "receptor": row["receptor"],
            "doi": row["doi"],
        })
        row["candidate_id"] = held_map[old]

    for row in decisions:
        row["pair_id"] = id_map[row["pair_id"]]
    for row in all_pairs:
        row["pair_id"] = id_map[row["pair_id"]]

    def replace_reference(match: re.Match[str]) -> str:
        first = f"PPR-{match.group(1)}"
        if first not in id_map:
            raise ValueError(f"Unresolved manuscript database reference: {first}")
        if match.group(2) is None:
            return id_map[first]
        last = int(match.group(2))
        original_range = [f"PPR-{i}" for i in range(int(match.group(1)), last + 1)]
        mapped = [id_map[item] for item in original_range]
        if not all(item.startswith("PPR-") for item in mapped):
            raise ValueError(f"Mixed admitted/held range: {match.group(0)}")
        numbers = [int(item.removeprefix("PPR-")) for item in mapped]
        if numbers != list(range(numbers[0], numbers[-1] + 1)):
            raise ValueError(f"Noncontiguous mapped range: {match.group(0)} -> {mapped}")
        return f"PPR-{numbers[0]}–{numbers[-1]}"

    for row in manuscript:
        row["database_evidence_ids"] = PPR_REFERENCE.sub(replace_reference, row["database_evidence_ids"])

    assert [row["pair_id"] for row in official] == [f"PPR-{i}" for i in range(1, len(official) + 1)]
    assert [row["candidate_id"] for row in held] == [f"H-{i}" for i in range(1, len(held) + 1)]
    assert all(row["pair_id"] in set(official_map.values()) | set(held_map.values()) for row in decisions + all_pairs)

    write_tsv(official_path, official_fields, official)
    write_tsv(held_path, held_fields, held)
    write_tsv(decisions_path, decision_fields, decisions)
    write_tsv(manuscript_path, manuscript_fields, manuscript)
    write_tsv(full_audit_path, audit_fields, all_pairs)
    for name in ("plant_LR_final_verified.tsv", "held_or_excluded_candidates.tsv", "review_22_decisions.tsv"):
        (audit / name).write_bytes((site / name).read_bytes())
    crosswalk_fields = ["previous_id", "current_id", "disposition", "species", "ligand", "receptor", "doi"]
    write_tsv(audit / "id_crosswalk_20261004.tsv", crosswalk_fields, crosswalk)
    print(f"Renumbered {len(official)} admitted records and {len(held)} held/excluded claims.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--site", type=Path, required=True)
    parser.add_argument("--audit", type=Path, required=True)
    args = parser.parse_args()
    renumber_release(args.site, args.audit)
