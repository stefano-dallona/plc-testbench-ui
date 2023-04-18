import os
import pickle
import logging

from typing import List

from ecctestbench.ecc_testbench import ECCTestbench

from ..models.run import Run

class RunRepository:
    '''
        Handles persistence of EccTestbench objects to support run concept
    '''
    
    def __init__(self, root_folder):
        self.logger = logging.getLogger(__name__)
        self.root_folder = root_folder
    
    def add(self, run: Run):
        file = self.__generate_filename__(self.root_folder, run.run_id)
        self.logger.info("Saving run %s to file %s", run.run_id, file)
        with open(file, 'wb') as handle:
            pickle.dump(run, handle)
    
    def get(self, reference) -> Run:
        file = self.__generate_filename__(self.root_folder, reference)
        self.logger.info("Loading run %s from file %s", reference, file)
        if os.path.exists(file):
            with open(file, 'rb') as handle:
                return pickle.load(handle)
        else:
            return None
    
    def list(self, predicate = lambda x : True) -> List[Run]:
        run_ids = [d for d in os.listdir(self.root_folder) if os.path.isdir(os.path.join(self.root_folder, d))]
        runs = list(map(lambda r: self.get(r), filter(predicate, run_ids)))
        runs.sort(key=lambda r: os.path.getmtime(os.path.join(self.root_folder, r.run_id)), reverse=True)
        return list(map(lambda r: dict(filter(lambda elem: not elem[0].startswith("_"), r.__dict__.items())), runs))
    
    ### Private methods ###
    def __generate_filename__(self, root_folder, reference):
        run_root_folder = os.path.join(root_folder, reference)
        filename = os.path.join(run_root_folder, 'ecctestbench.pickle')
        return filename
