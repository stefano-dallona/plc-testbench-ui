
class Serializable:
    
    @staticmethod
    def to_json():
        return lambda o : o.__dict__ if hasattr(o, '__dict__') else o