from django.apps import AppConfig

class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.core'

    def ready(self):
        # Import here to avoid AppRegistryNotReady exception
        from .utils import initialize_minio_bucket

        # Initialize MinIO bucket
        initialize_minio_bucket()

        # Import signals
        import apps.core.signals