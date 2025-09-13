# Import Celery app only if it's available
try:
    from .celery import app as celery_app
    __all__ = ('celery_app',)
except ImportError:
    # Celery not installed, but Django should still work
    pass
