# routers.py

class PointOfInterestRouter:
    def db_for_model(self, model):
        if model._meta.app_label == 'maps' and model._meta.model_name == 'pointofinterest':
            return 'postgis'
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        if app_label == 'maps' and model_name == 'pointofinterest':
            return db == 'postgis'
        return None
