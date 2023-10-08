#from flask_login import UserMixin




#class User(UserMixin):
class User():
    def __init__(self, id_, name, email):
        self.id_ = id_
        self.name = name
        self.email = email
    
    def get_id(self):
        return self.id_
    
    @staticmethod
    def get(user_id):
        return User(user_id, "Stefano", "stefano.dallona@gmail.com")
    
    @staticmethod
    def create(user_id, name, email):
        #User(user_id, name, email)
        pass