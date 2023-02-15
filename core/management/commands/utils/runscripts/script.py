from django.core import management
import logging

from core.models import CommandHistory

logger = logging.getLogger(__name__)

class Script:
    def __init__(self, name, *args, **kwargs):
        self.name = name
        self.args = args
        self.kwargs = kwargs
    def execute(self):
        if CommandHistory.objects.filter(name=self.name).exists():
            raise AppliedError(f"{self.name} script already applied")
        try:
            management.call_command(self.name, *self.args, **self.kwargs)
            CommandHistory.objects.create(name=self.name)
        except Exception as e:
            raise NotExecuteError(f"Unable to execute {self.name} script: {str(e)}")

class AppliedError(Exception):
    pass

class NotExecuteError(Exception):
    pass