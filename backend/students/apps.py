# from django.apps import AppConfig
# import logging
#
# logger = logging.getLogger(__name__)
#
#
# class StudentsConfig(AppConfig):
#     default_auto_field = 'django.db.models.BigAutoField'
#     name = 'students'
#     verbose_name = 'Student Management'
#
#     def ready(self):
#         """Initialize the app and connect signals"""
#         try:
#             # Import and connect signals
#             from . import signals
#             signals.setup_student_signals()
#
#             logger.info(f"{self.verbose_name} app initialized with signals")
#         except Exception as e:
#             logger.error(f"Error initializing {self.name} app: {str(e)}")


from django.apps import AppConfig


class StudentsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'students'
    verbose_name = 'Student Management'

    def ready(self):
        """Initialize the app - TEMPORARILY REMOVE SIGNALS"""
        pass  # Remove signals for now