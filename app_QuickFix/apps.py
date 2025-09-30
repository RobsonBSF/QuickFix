
from django.apps import AppConfig
from django.conf import settings

from django_master_sync import sync_db
class AppQuickfixConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'app_QuickFix'

    def ready(self):
        from django.db.models.signals import post_migrate
        
        def handler(sender, **kwargs):
            sync_db(sender,db_settings=settings.DATABASES,DEBUG=False) 

        post_migrate.connect(handler, sender=self)

