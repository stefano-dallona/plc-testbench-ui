
import os

class Config():
  def __init__(self, data_dir: str,
               db_conn_string: str = None,
               db_name: str = "plc_database",
               db_username: str = None,
               db_password: str = None):
    self.data_dir = data_dir
    self.db_conn_string = db_conn_string.replace("mongodb://", "mongodb://" + db_username + ":" + db_password + "@") \
                                if db_username != None and db_password != None \
                                else db_conn_string
    self.db_name = db_name

root_folder = os.environ.get("DATA_FOLDER") if "DATA_FOLDER" in os.environ else "/plc-testbench-ui/original_tracks"
db_conn_string = os.environ.get("DB_CONN_STRING") if "DB_CONN_STRING" in os.environ else "mongodb://localhost:27017"
db_username = os.environ.get("DB_USERNAME")
db_password = os.environ.get("DB_PASSWORD")

config = Config(data_dir=root_folder,
                db_conn_string=db_conn_string,
                db_username=db_username,
                db_password=db_password)