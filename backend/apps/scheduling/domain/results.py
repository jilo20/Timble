from collections import Counter, defaultdict


def inspect_result(scenario, assignments):
    """Independent validation and occupancy reconstruction; no Pyomo dependency."""
    occupied = {kind: Counter() for kind in ["offering", "faculty", "room", "block"]}
    meetings = Counter()
    days = Counter()
    teachers = defaultdict(set)
    loads = Counter()
    errors = []
    waste = 0
    rules = {(r["faculty"], r["subject"]): r["rule"] for r in scenario.rules}
    for a in assignments:
        o = scenario.offerings[a["offering"] - 1]
        r = scenario.rooms[a["room"] - 1]
        meetings[a["offering"], a["meeting"]] += 1
        days[a["offering"], a["day"]] += 1
        teachers[a["offering"]].add(a["faculty"])
        loads[a["faculty"]] += a["duration"]
        if not 1 <= a["meeting"] <= o["meetings"]:
            errors.append("Invalid meeting number")
        if rules.get((a["faculty"], o["subject"]), "CANNOT") == "CANNOT":
            errors.append("Faculty is ineligible")
        if r["type"] != o["room_type"] or r["capacity"] < o["students"]:
            errors.append("Incompatible room")
        if (
            a["duration"] != o["duration"]
            or a["start"] < 1
            or a["start"] + a["duration"] > len(scenario.periods)
            or not 1 <= a["day"] <= len(scenario.days)
        ):
            errors.append("Invalid duration or boundary")
        waste += r["capacity"] - o["students"]
        for p in range(a["start"], a["start"] + a["duration"]):
            for kind, index in [
                ("offering", a["offering"]),
                ("faculty", a["faculty"]),
                ("room", a["room"]),
            ] + [("block", b) for b in o["blocks"]]:
                occupied[kind][index, a["day"], p] += 1
    for o in scenario.offerings:
        for m in range(1, o["meetings"] + 1):
            if meetings[o["index"], m] != 1:
                errors.append(f"O{o['index']} M{m}: meeting count is not one")
        if len(teachers[o["index"]]) != 1:
            errors.append(f"O{o['index']}: inconsistent faculty")
    for kind, counts in occupied.items():
        for key, value in counts.items():
            if value > 1:
                errors.append(f"{kind} {key}: occupancy {value} exceeds 1")
    if any(v > 1 for v in days.values()):
        errors.append("Repeated meeting on the same day")
    for f in scenario.faculty:
        if loads[f["index"]] > f["max_load"]:
            errors.append("Faculty teaching load exceeded")
    for (f, s), rule in rules.items():
        relevant = [o for o in scenario.offerings if o["subject"] == s]
        if (
            rule == "MUST_TEACH"
            and relevant
            and not any(f in teachers[o["index"]] for o in relevant)
        ):
            errors.append("MUST_TEACH not satisfied")
    return {
        "valid": not errors,
        "violations": errors,
        "room_waste": waste,
        "occupancy": {
            kind: [
                {"index": i, "day": d, "period": p, "count": v}
                for (i, d, p), v in sorted(counts.items())
            ]
            for kind, counts in occupied.items()
        },
    }


def explanation(scenario, assignment):
    o = scenario.offerings[assignment["offering"] - 1]
    r = scenario.rooms[assignment["room"] - 1]
    rules = {(x["faculty"], x["subject"]): x["rule"] for x in scenario.rules}
    return {
        "offering": o,
        "chosen_faculty": scenario.faculty[assignment["faculty"] - 1],
        "chosen_room": r,
        "faculty_candidates": [
            {
                "label": f["label"],
                "rule": rules.get((f["index"], o["subject"]), "CANNOT"),
            }
            for f in scenario.faculty
        ],
        "room_candidates": [
            {
                "label": room["label"],
                "capacity": room["capacity"],
                "reason": "Eligible"
                if room["type"] == o["room_type"] and room["capacity"] >= o["students"]
                else (
                    "Incompatible type"
                    if room["type"] != o["room_type"]
                    else "Insufficient capacity"
                ),
            }
            for room in scenario.rooms
        ],
        "waste": r["capacity"] - o["students"],
        "occupied_periods": list(
            range(assignment["start"], assignment["start"] + assignment["duration"])
        ),
        "note": "This is a feasible assignment chosen by the global room-waste objective. Equal-cost alternatives may exist.",
    }
