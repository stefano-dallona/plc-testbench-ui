
import os

root_folder = os.environ.get("DATA_FOLDER") if "DATA_FOLDER" in os.environ else "/plc-testbench-ui/original_tracks"
db_host = os.environ.get("DB_HOST") if "DB_HOST" in os.environ else "localhost"
db_port = int(os.environ.get("DB_PORT") if "DB_PORT" in os.environ else "27017")
db_database = os.environ.get("DB_DBNAME") if "DB_DBNAME" in os.environ else "plc_database"
db_conn_string = os.environ.get("DB_CONN_STRING") if "DB_CONN_STRING" in os.environ else "mongodb://" + str(db_host) + ":" + str(db_port)
db_username = os.environ.get("DB_USERNAME")
db_password = os.environ.get("DB_PASSWORD")

class Config():
  def __init__(self, data_dir: str,
               db_host: str,
               db_port: str,
               db_database: str,
               db_conn_string: str = None,
               db_name: str = "plc_database",
               db_username: str = None,
               db_password: str = None):
    self.data_dir = data_dir
    self.db_host = db_host
    self.db_port = db_port
    self.db_database = db_database
    self.db_username = db_username
    self.db_password = db_password
    self.db_conn_string = db_conn_string.replace("mongodb://", "mongodb://" + db_username + ":" + db_password + "@") \
                                if db_username != None and db_password != None \
                                else db_conn_string
    self.db_name = db_name
    self.validate()
    
  def validate(self):
    if not (os.path.exists(self.data_dir) and os.access(self.data_dir, os.W_OK)):
      raise Exception(f"Invalid DATA_FOLDER '{self.data_dir}'. Please ensure that the environment variable is set to a valid and writable path in your system.")

config = Config(data_dir=root_folder,
                db_host=db_host,
                db_port=db_port,
                db_database=db_database,
                db_conn_string=db_conn_string,
                db_username=db_username,
                db_password=db_password)