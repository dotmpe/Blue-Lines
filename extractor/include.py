import logging
from nabu import extract


class RecordDependencies(extract.Extractor):

    default_priority = 500

    def apply(self, unid=None, storage=None, **kwds):
        if not unid or not storage:
            logging.debug("RecordDependencies: no extractor keywords. ")


class DependencyStorage(extract.ExtractorStorage):

    def __init__(self, alias=None):
        self.alias = alias

    def store(self, unid, unids):
        assert self.alias and hasattr(self.alias, 'handle')


