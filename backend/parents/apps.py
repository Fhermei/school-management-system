from django.apps import AppConfig

class ParentsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'parents'  # MUST be 'parents' (same as folder name)
    verbose_name = 'Parents Management'

    def ready(self):
        """Initialize the app"""
        # Don't import anything here yet to avoid circular imports
        pass