# from django.apps import AppConfig
#
# class AcademicConfig(AppConfig):
#     default_auto_field = 'django.db.models.BigAutoField'
#     name = 'academic'
#     verbose_name = 'Academic Management'
#
#     def ready(self):
#         """Import signals when app is ready"""
#         # Import signals module to connect signals
#         try:
#             import academic.signals
#         except ImportError:
#             pass


from django.apps import AppConfig


class AcademicConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'academic'
    verbose_name = 'Academic Management'

    def ready(self):
        """Initialize the app - TEMPORARILY REMOVE SIGNALS"""
        pass  # Remove signals for now