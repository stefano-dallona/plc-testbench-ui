import os
import pickle
import logging

from typing import List

from plctestbench.plc_testbench import PLCTestbench

from ...models.run import Run
from ..run_repository import RunRepository as BaseRunRepository

class RunRepository(BaseRunRepository):
    '''
        Handles persistence of EccTestbench objects to support run concept
    '''
    
    def __init__(self, root_folder):
        super().__init__()
        self.logger = logging.getLogger(__name__)
        self.root_folder = root_folder
    
    def add(self, run: Run):
        file = self.__generate_filename__(self.root_folder, run.run_id)
        self.logger.info("Saving run %s to file %s", run.run_id, file)
        with open(file, 'wb') as handle:
            pickle.dump(run, handle)
    
    def find_by_id(self, id) -> Run:
        file = self.__generate_filename__(self.root_folder, id)
        self.logger.info("Loading run %s from file %s", id, file)
        if os.path.exists(file):
            with open(file, 'rb') as handle:
                return pickle.load(handle)
        else:
            return None
    
    def find_by_predicate(self,
                          predicate = lambda x: True,
                          projection = None,
                          pagination = BaseRunRepository.__default_pagination__) -> List[Run]:
        run_ids = [d for d in os.listdir(self.root_folder) if os.path.isdir(os.path.join(self.root_folder, d))]
        runs = list(map(lambda r: self.find_by_id(r), filter(predicate, run_ids)))
        runs.sort(key=lambda r: os.path.getmtime(os.path.join(self.root_folder, r.run_id)), reverse=True)
        runs_projection = list(map(lambda r: dict(filter(lambda elem: not elem[0].startswith("_"), r.__dict__.items())), runs))
        return {
            'data': runs_projection[pagination["page"] * pagination["pageSize"]:(pagination["page"] + 1) * pagination["pageSize"]],
            'totalRecords': len(runs)
        }
    
    ### Private methods ###
    def __generate_filename__(self, root_folder, reference):
        run_root_folder = os.path.join(root_folder, reference)
        filename = os.path.join(run_root_folder, 'plctestbench.pickle')
        return filename
