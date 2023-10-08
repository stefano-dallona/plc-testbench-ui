
class Serializable:
    
    @staticmethod
    def to_json():
        return lambda o : o.__dict__ if hasattr(o, '__dict__') else o
    
class DefaultJsonEncoder:
    @classmethod
    def to_json(cls, obj):
        return obj.__dict__ if hasattr(obj, '__dict__') else obj