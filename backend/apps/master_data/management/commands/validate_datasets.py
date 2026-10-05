from pathlib import Path

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.bulk_import.schema import FILES, SCHEMAS
from apps.bulk_import.services.importer import import_csv


class Command(BaseCommand):
    help = "Validate the revised package using the production importer without retaining changes."

    def add_arguments(self, parser):
        parser.add_argument(
            "--directory", default=str(settings.BASE_DIR.parent / "datasets" / "source")
        )

    def handle(self, *args, **options):
        with transaction.atomic():
            for kind in SCHEMAS:
                path = Path(options["directory"]) / (FILES.get(kind, kind) + ".csv")
                result = import_csv(kind, path.read_bytes(), commit=True)
                if not result["valid"]:
                    raise CommandError(f"{path.name}: {result['errors']}")
                self.stdout.write(
                    f"{path.name}: {result['inserted']} inserted, {result['updated']} updated, {result['skipped']} unchanged (rolled back)"
                )
            transaction.set_rollback(True)
