import os
import pickle
import logging

from typing import List

from plctestbench.plc_testbench import PLCTestbench

from ..models.run import Run

class RunRepository:
    '''
        Handles persistence of EccTestbench objects to support run concept
    '''
    __default_pagination__ = { 'page': 0, 'pageSize': 10 }
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def add(self, item: Run):
        pass
     
    def update(self, item):
        pass
    
    def delete(self, id):
        pass
    
    def find_by_id(self,
                   id,
                   projection = None) -> Run:
        pass
    
    def find_by_predicate(self,
                          predicate,
                          projection = None,
                          pagination = __default_pagination__) -> List[Run]:
        pass
    
    def find_by_query(self,
                      query,
                      projection,
                      pagination = __default_pagination__) -> List[Run]:
        pass

