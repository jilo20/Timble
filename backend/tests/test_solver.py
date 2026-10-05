from copy import deepcopy

from apps.forecasting.services.forecast_engine import generate_forecast
from apps.forecasting.services.offering_generator import finalize_forecast
from apps.scheduling.domain.results import inspect_result
from apps.scheduling.domain.scenario import SchedulingScenario
from apps.scheduling.optimization.model_builder import build_model
from apps.scheduling.optimization.solver import solve
from apps.scheduling.services.schedule_service import create_run, execute_run
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import SimpleTestCase, TestCase


def scenario():
    return SchedulingScenario(
        offerings=[
            {
                "index": 1,
                "id": 1,
                "subject": 1,
                "label": "Algorithms A",
                "students": 25,
                "duration": 2,
                "meetings": 2,
                "room_type": "LECTURE",
                "blocks": [1],
            },
            {
                "index": 2,
                "id": 2,
                "subject": 1,
                "label": "Algorithms B",
                "students": 20,
                "duration": 1,
                "meetings": 1,
                "room_type": "LECTURE",
                "blocks": [1],
            },
        ],
        faculty=[
            {"index": 1, "id": 1, "label": "F1", "max_load": 12},
            {"index": 2, "id": 2, "label": "F2", "max_load": 12},
            {"index": 3, "id": 3, "label": "F3", "max_load": 12},
        ],
        rooms=[
            {"index": 1, "id": 1, "label": "R1", "type": "LECTURE", "capacity": 30},
            {"index": 2, "id": 2, "label": "R2", "type": "LAB", "capacity": 50},
            {"index": 3, "id": 3, "label": "R3", "type": "LECTURE", "capacity": 10},
        ],
        blocks=[{"index": 1, "id": 1, "label": "B1"}],
        subjects=[{"index": 1, "id": 1, "label": "Algorithms"}],
        rules=[
            {"faculty": 1, "subject": 1, "rule": "MUST_TEACH"},
            {"faculty": 2, "subject": 1, "rule": "CAN"},
            {"faculty": 3, "subject": 1, "rule": "CANNOT"},
        ],
        days=["Monday", "Tuesday"],
        periods=["07:30", "08:30", "09:30", "10:30"],
    )


class SolverTests(SimpleTestCase):
    def test_real_solver_and_independent_validation(self):
        s = scenario()
        result = solve(s)
        self.assertEqual(result["status"], "OPTIMAL")
        self.assertEqual(result["objective_value"], 20)
        self.assertEqual(result["best_bound"], 20)
        self.assertEqual(result["mip_gap"], 0)
        self.assertTrue(inspect_result(s, result["assignments"])["valid"])
        self.assertEqual(len(result["assignments"]), 3)

    def test_cannot_and_must_teach(self):
        result = solve(scenario())
        faculty = {a["faculty"] for a in result["assignments"]}
        self.assertNotIn(3, faculty)
        self.assertIn(1, faculty)

    def test_must_teach_does_not_require_all_sections(self):
        s = scenario()
        s.rules[1]["rule"] = "MUST_TEACH"
        result = solve(s)
        self.assertEqual(result["status"], "OPTIMAL")
        self.assertEqual({a["faculty"] for a in result["assignments"]}, {1, 2})

    def test_room_capacity_and_type(self):
        result = solve(scenario())
        self.assertEqual({a["room"] for a in result["assignments"]}, {1})

    def test_duration_and_boundary(self):
        s = scenario()
        result = solve(s)
        validation = inspect_result(s, result["assignments"])
        self.assertEqual(sum(x["count"] for x in validation["occupancy"]["block"]), 5)
        for a in result["assignments"]:
            self.assertLessEqual(a["start"] + a["duration"], len(s.periods))

    def test_indices_start_at_one(self):
        model = build_model(scenario())
        self.assertEqual(list(model.O), [1, 2])
        self.assertEqual(min(model.P), 1)
        self.assertTrue(all(all(i >= 1 for i in key) for key in model.C))

    def test_each_collision_independently_infeasible(self):
        for shared in ["faculty", "room", "block"]:
            with self.subTest(shared=shared):
                s = scenario()
                s.days[:] = ["Monday"]
                s.periods[:] = ["07:30", "08:30"]
                s.rules[:] = [{"faculty": f, "subject": 1, "rule": "CAN"} for f in [1, 2]]
                s.offerings[0].update(duration=1, meetings=1)
                s.blocks.append({"index": 2, "id": 2, "label": "B2"})
                s.rooms[:] = [
                    {
                        "index": r,
                        "id": r,
                        "label": f"R{r}",
                        "type": "LECTURE",
                        "capacity": 30,
                    }
                    for r in [1, 2]
                ]
                s.offerings[1]["blocks"] = [2] if shared != "block" else [1]
                if shared == "faculty":
                    s.rules[:] = [{"faculty": 1, "subject": 1, "rule": "CAN"}]
                if shared == "room":
                    s.rooms[:] = s.rooms[:1]
                self.assertEqual(solve(s)["status"], "INFEASIBLE")

    def test_no_eligible_candidates(self):
        s = scenario()
        s.rules.clear()
        with self.assertRaises(ValueError):
            solve(s)

    def test_too_long_duration(self):
        s = scenario()
        s.offerings[0]["duration"] = 4
        with self.assertRaises(ValueError):
            solve(s)

    def test_weekly_load(self):
        s = scenario()
        for f in s.faculty:
            f["max_load"] = 1
        self.assertEqual(solve(s)["status"], "INFEASIBLE")

    def test_validator_detects_corrupted_result(self):
        s = scenario()
        result = solve(s)
        data = result["assignments"]
        data.append(deepcopy(data[0]))
        validation = inspect_result(s, data)
        self.assertFalse(validation["valid"])
        for kind in ["faculty", "room", "block"]:
            self.assertTrue(any(kind in error for error in validation["violations"]))


class PersistenceTests(TestCase):
    def test_end_to_end_persistence_and_snapshot(self):
        call_command("load_demo", verbosity=0)
        user = get_user_model().objects.create_user("demo-test")
        forecast = generate_forecast("2026-2027", 30, user, failure_rate="0.05")
        finalize_forecast(forecast.pk, user)
        run = create_run(forecast.pk)
        execute_run(run.pk)
        run.refresh_from_db()
        self.assertEqual(run.status, "OPTIMAL", run.diagnostic)
        self.assertEqual(run.assignments.count(), 12)
        self.assertEqual(run.metrics.count(), 1)
        self.assertEqual(run.objective_value, 70)
        self.client.force_login(user)
        response = self.client.get(f"/api/schedules/{run.pk}/")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["validation"]["valid"])
        from apps.master_data.models import Room

        Room.objects.all().update(capacity=999)
        self.assertEqual(
            self.client.get(f"/api/schedules/{run.pk}/").json()["validation"]["room_waste"],
            70,
        )
        execute_run(run.pk)
        self.assertEqual(run.assignments.count(), 12)
