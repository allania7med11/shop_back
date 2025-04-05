from django.contrib import admin

from .models import ChatSettings


@admin.register(ChatSettings)
class ChatSettingsAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        # Prevent creating multiple settings
        return not ChatSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        # Prevent deleting the settings
        return False
