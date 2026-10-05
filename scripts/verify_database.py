"""Verify the configured database with a full workflow, rolling back every data mutation."""

import json
import os
import sys
import uuid
from pathlib import Path

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root / "backend"))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
import django

django.setup()
from apps.bulk_import.services.bundle import import_bundle, package_bytes
from apps.forecasting.services.forecast_engine import generate_forecast
from apps.forecasting.services.offering_generator import finalize_forecast
from apps.master_data.models import Program
from apps.scheduling.services.schedule_service import create_run, execute_run
from django.contrib.auth import get_user_model
from django.db import connection, transaction

before = Program.objects.count()
with transaction.atomic():
    imported = import_bundle(package_bytes("demo"), commit=True)
    assert imported["committed"], imported["errors"]
    user = get_user_model().objects.create_user("verification-" + uuid.uuid4().hex[:12])
    program = Program.objects.get(program_code="DEMO-CS")
    forecast = generate_forecast(
        "2026-2027", 30, user, program_ids=[program.pk], failure_rate="0.05"
    )
    finalize_forecast(forecast.pk, user)
    run = create_run(forecast.pk)
    execute_run(run.pk)
    run.refresh_from_db()
    assert run.status == "OPTIMAL", run.diagnostic
    assert run.assignments.count() == 12
    evidence = {
        "database_engine": connection.vendor,
        "zip_files_imported": len(imported["files"]),
        "status": run.status,
        "assignments": run.assignments.count(),
        "objective": run.objective_value,
        "best_bound": run.best_bound,
        "mip_gap": run.mip_gap,
        "nodes": run.nodes_explored,
        "elapsed_seconds": run.elapsed_seconds,
        "data_changes": "rolled back",
    }
    transaction.set_rollback(True)
assert Program.objects.count() == before
(root / "artifacts").mkdir(exist_ok=True)
(root / "artifacts/database-verification.json").write_text(
    json.dumps(evidence, indent=2), encoding="utf-8"
)
print(json.dumps(evidence))
