from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.bulk_import.schema import FILES, SCHEMAS
from apps.bulk_import.services.importer import import_csv


class Command(BaseCommand):
    help = "Load the labeled synthetic demonstration dataset, idempotently."

    @transaction.atomic
    def handle(self, *args, **options):
        for kind in SCHEMAS:
            path = settings.BASE_DIR.parent / "datasets" / "demo" / (FILES.get(kind, kind) + ".csv")
            result = import_csv(kind, path.read_bytes(), commit=True)
            if not result["valid"]:
                raise CommandError(str(result["errors"]))
        self.stdout.write(
            "Synthetic DEMO records loaded. Forecast 2026-2027, capacity 30, program DEMO-CS."
        )
