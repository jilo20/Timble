from django.core.management.base import BaseCommand

from apps.scheduling.services.schedule_service import execute_run


class Command(BaseCommand):
    help = "Claim and solve one queued schedule run. Safe to retry a queued run."

    def add_arguments(self, parser):
        parser.add_argument("run_id", type=int)

    def handle(self, *args, **options):
        execute_run(options["run_id"])
