def parameters(scenario):
    rules = {(r["faculty"], r["subject"]): r["rule"] for r in scenario.rules}
    faculty_subject = [
        [rules.get((f["index"], s["index"]), "CANNOT") for s in scenario.subjects]
        for f in scenario.faculty
    ]
    offering_block = [
        [int(b["index"] in o["blocks"]) for b in scenario.blocks] for o in scenario.offerings
    ]
    compatibility = [
        [
            int(r["type"] == o["room_type"] and r["capacity"] >= o["students"])
            for r in scenario.rooms
        ]
        for o in scenario.offerings
    ]
    return {
        "faculty_subject": faculty_subject,
        "offering_block": offering_block,
        "room_compatibility": compatibility,
    }
