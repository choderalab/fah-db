import pytest
from fahdb.data.resources import SOURCE_RECORD, SOURCE_JSON
from fahdb.records import NewPDBRecord, ValidatedPDBRecordBase, SourceRecord
from pathlib import Path


def test_new_record():
    return NewPDBRecord.from_json_file(SOURCE_JSON)


@pytest.fixture
def new_record():
    return test_new_record()


def test_source_record(new_record):
    return SourceRecord.from_new_record(new_record, project="test_project")


@pytest.fixture
def source_record(new_record):
    return SourceRecord.from_new_record(new_record, project="test_project")


def test_record_roundtrip(new_record, tmp_path):
    new_record.update_home(tmp_path)
    new_record.write_json_file()
    read_record = NewPDBRecord.from_json_file(new_record.json_path)
    assert read_record == new_record


def test_validation(new_record):
    assert ValidatedPDBRecordBase.from_new_record(new_record).dict() == new_record.dict()


def test_validation_failure(new_record, tmp_path):
    fake_record = new_record.dict()
    fake_record["home"] = "fake_path"
    with pytest.raises(FileNotFoundError):
        ValidatedPDBRecordBase(**fake_record)

