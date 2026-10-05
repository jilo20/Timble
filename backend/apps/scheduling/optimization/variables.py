from collections import defaultdict

import pyomo.environ as pyo


def add_variables(model, scenario):
    model.O = pyo.RangeSet(1, len(scenario.offerings))
    model.F = pyo.RangeSet(1, len(scenario.faculty))
    model.R = pyo.RangeSet(1, len(scenario.rooms))
    model.B = pyo.RangeSet(1, len(scenario.blocks))
    model.D = pyo.RangeSet(1, len(scenario.days))
    model.P = pyo.RangeSet(1, len(scenario.periods) - 1)
    rules = {(r["faculty"], r["subject"]): r["rule"] for r in scenario.rules}
    candidates = []
    by_meeting = defaultdict(list)
    by_faculty = defaultdict(list)
    by_room = defaultdict(list)
    by_block = defaultdict(list)
    by_ofm = defaultdict(list)
    by_day = defaultdict(list)
    eligible = []
    for o in scenario.offerings:
        oi = o["index"]
        if o["meetings"] > len(scenario.days):
            raise ValueError(f"{o['label']}: more meetings than distinct days.")
        for f in scenario.faculty:
            fi = f["index"]
            if rules.get((fi, o["subject"]), "CANNOT") == "CANNOT":
                continue
            eligible.append((oi, fi))
            for r in scenario.rooms:
                ri = r["index"]
                if r["type"] != o["room_type"] or r["capacity"] < o["students"]:
                    continue
                for m in range(1, o["meetings"] + 1):
                    for d in model.D:
                        for p in range(1, len(scenario.periods) - o["duration"] + 1):
                            key = (oi, m, fi, ri, d, p)
                            candidates.append(key)
                            by_meeting[oi, m].append(key)
                            by_ofm[oi, fi, m].append(key)
                            by_day[oi, d].append(key)
                            for occupied in range(p, p + o["duration"]):
                                by_faculty[fi, d, occupied].append(key)
                                by_room[ri, d, occupied].append(key)
                                for b in o["blocks"]:
                                    by_block[b, d, occupied].append(key)
        for m in range(1, o["meetings"] + 1):
            if not by_meeting[oi, m]:
                raise ValueError(f"{o['label']}: no eligible faculty/room/start combination.")
    model.C = pyo.Set(dimen=6, initialize=candidates)
    model.E = pyo.Set(dimen=2, initialize=eligible)
    model.x = pyo.Var(model.C, domain=pyo.Binary)
    model.y = pyo.Var(model.E, domain=pyo.Binary)
    return dict(
        meeting=by_meeting,
        faculty=by_faculty,
        room=by_room,
        block=by_block,
        ofm=by_ofm,
        day=by_day,
        rules=rules,
    )
