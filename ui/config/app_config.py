
import os

class Config():
  def __init__(self, data_dir):
    self.data_dir = data_dir

root_folder = os.environ.get("DATA_FOLDER") if "DATA_FOLDER" in os.environ else "/plc-testbench-ui/original_tracks"
config = Config(data_dir=root_folder)