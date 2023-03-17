from ecctestbench.ecc_testbench import ECCTestbench
import os
import pickle
import logging

class RunRepository:
    '''
        Handles persistence of EccTestbench objects to support run concept
    '''
    
    def __init__(self, root_folder):
        self.logger = logging.getLogger(__name__)
        self.root_folder = root_folder
    
    def add(self, run: ECCTestbench):
        file = self.__generate_filename__(self.root_folder, run.uuid)
        self.logger.info("Saving run %s to file %s", run.uuid, file)
        with open(file, 'wb') as handle:
            pickle.dump(run, handle)
    
    def get(self, reference):
        file = self.__generate_filename__(self.root_folder, reference)
        self.logger.info("Loading run %s from file %s", reference, file)
        if os.path.exists(file):
            with open(file, 'rb') as handle:
                return pickle.load(handle)
        else:
            return None
    
    def list(self, predicate):
        pass
    
    ### Private methods ###
    def __generate_filename__(self, root_folder, reference):
        filename = os.path.join(root_folder, 'ecctestbench-' + reference + '.pickle')
        return filename
