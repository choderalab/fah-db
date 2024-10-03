import pytest
from fahdb.data.resources import SOURCE, FAH
from fahdb.records import NewRecord, ValidatedRecordBase, SourceRecord
from fahdb.database import NewStructureDatabase, InputStructureDatabase, SourceDatabase, FAHDatabase
from pathlib import Path


def test_new_source_database():
    sdb = SourceDatabase.from_directory(SOURCE)
    print(sdb)


def test_comparison():
    sdb = SourceDatabase.from_directory(SOURCE)
    fdb = FAHDatabase.from_directory(FAH)
    comparison = fdb.compare_to_source(sdb)
    fdb.sync(sdb, sync=False)
    fdb.sync(sdb, sync=True)