
class Serializable:
    
    @staticmethod
    def to_json():
        return lambda o : o.__dict__ if hasattr(o, '__dict__') else o
    
class DefaultJsonEncoder:
    @classmethod
    def to_json(cls, obj):
        if hasattr(obj, 'toJson') and callable(obj.toJson):
            return obj.toJson()
        if hasattr(obj, '__dict__'):
            return obj.__dict__
        return obj