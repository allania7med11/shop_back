from django.core.management.base import BaseCommand

from core.management.commands.utils.runscripts.script import AppliedError, NotExecuteError, Script


class Command(BaseCommand):
    help = "Command to run list of commands for each deploy"

    scripts = [
        Script("create_rebuild_task"),
    ]

    def handle(self, *args, **options):
        for script in self.scripts:
            try:
                script.execute()
            except AppliedError as e:
                self.stdout.write(str(e))
            except NotExecuteError as e:
                self.stdout.write(str(e))
