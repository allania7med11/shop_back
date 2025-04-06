import json
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils.timezone import now
from django_celery_beat.models import IntervalSchedule, PeriodicTask


class Command(BaseCommand):
    help = "Create periodic task 'Rebuild Product Vector Index' if it does not exist."

    def handle(self, *args, **kwargs):
        # Ensure the interval schedule exists for daily execution
        interval_schedule, created = IntervalSchedule.objects.get_or_create(
            every=1, period=IntervalSchedule.DAYS  # Every 1 day
        )
        if created:
            self.stdout.write(self.style.SUCCESS("Daily interval schedule created."))

        # Set the start time to the next day at zero hours
        current_time = now()
        start_time = (current_time + timedelta(days=1)).replace(
            hour=0, minute=0, second=0, microsecond=0
        )

        # Define the task keyword arguments
        task_kwargs = {"reason": "Scheduled daily rebuild"}

        # Check if the task already exists
        if PeriodicTask.objects.filter(name="Rebuild Product Vector Index").exists():
            self.stdout.write(self.style.WARNING("Periodic task already exists. No action taken."))
            return

        # Create the periodic task
        PeriodicTask.objects.create(
            name="Rebuild Product Vector Index",
            task="products.tasks.rebuild_product_index_task",  # Ensure this path is correct
            interval=interval_schedule,
            start_time=start_time,
            kwargs=json.dumps(task_kwargs),
            enabled=True,
        )

        self.stdout.write(
            self.style.SUCCESS("Periodic task for rebuilding product vector index created.")
        )
