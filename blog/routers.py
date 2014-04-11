from django.conf import settings

class Router(object):


    def db_for_read(self, model, **hints):

        if settings.DATABASE_APPS_MAPPING.has_key(model._meta.app_label):
            return settings.DATABASE_APPS_MAPPING[model._meta.app_label]
        return None

    def db_for_write(self, model, **hints):

        if settings.DATABASE_APPS_MAPPING.has_key(model._meta.app_label):
            return settings.DATABASE_APPS_MAPPING[model._meta.app_label]
        return None

    def allow_relation(self, obj1, obj2, **hints):

        db_obj1 = settings.DATABASE_APPS_MAPPING.get(obj1._meta.app_label)
        db_obj2 = settings.DATABASE_APPS_MAPPING.get(obj2._meta.app_label)
        if db_obj1 and db_obj2:
            if db_obj1 == db_obj2:
                return True
            else:
                return False
        return None

    def allow_syncdb(self, db, model):
        
        if db in settings.DATABASE_APPS_MAPPING.values():
            return settings.DATABASE_APPS_MAPPING.get(model._meta.app_label) == db
        elif settings.DATABASE_APPS_MAPPING.has_key(model._meta.app_label):
            return False
        return None