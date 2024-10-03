import json
from pathlib import Path

from pydantic import BaseModel, Field, field_validator
from typing import Union


class RecordBase(BaseModel):
    unique_id: str = Field(..., description="Unique identifier for the record")
    home: str = Field(..., description="Path to the home directory of the record")
    rcsb_id: str = Field(..., description="RCSB ID of the record")
    sequence: str = Field(..., description="Protein sequence of the record")

    @property
    def json_path(self) -> Path:
        return Path(self.home) / f"{self.unique_id}_record.json"

    def update_home(self, new_home: Union[str, Path]):
        new_path = Path(new_home)
        if not new_path.exists():
            new_path.mkdir(parents=True, exist_ok=True)
        self.home = str(new_home)

    def write_json_file(self, write_to_home: bool = True):
        if write_to_home:
            output_path = self.json_path
        else:
            output_path = f"{self.unique_id}_record.json"
        with open(output_path, "w") as f:
            json.dump(self.dict(), f)


    @classmethod
    def from_json_file(cls, json_path):
        with open(json_path, "r") as f:
            loaded = json.load(f)
            loaded["home"] = str(json_path.parent)
            return cls(**loaded)


class ValidatedRecordBase(RecordBase):

    @field_validator("home", mode='before')
    def home_exists(cls, v):
        if not Path(v).exists():
            raise FileNotFoundError(f"Path {v} does not exist")
        return v

    @classmethod
    def from_new_record(cls, new_record: RecordBase):
        return cls(**new_record.dict())


class NewRecord(RecordBase):
    pass


class StructureRecord(ValidatedRecordBase):
    filename: str = Field(..., description="Name of the pdb file in the record")
    box_length_nm: float = Field(
        ..., description="Length of the side of the cubic box in nm"
    )

    class Config:
        extra = "allow"

    @field_validator("filename")
    def filename_exists(cls, v, values):
        home = values.get("home")
        if not Path(home) / v:
            raise FileNotFoundError(f"Path {v} does not exist")
        return v

    @property
    def pdb_path(self):
        return Path(self.home) / self.filename


class SourceRecord(ValidatedRecordBase):
    project: str = Field(..., description="Name of the project")

    @classmethod
    def from_json_file(cls, json_path, project: str):
        new_record = NewRecord.from_json_file(json_path)
        new_record.update_home(json_path.parent)
        new_record.write_json_file()
        return cls(project=project, **new_record.dict())

    @classmethod
    def from_directory(cls, directory: Path, project: str):
        json_files = list(directory.glob("*record.json"))
        import pdb
        pdb.set_trace()
        if len(list(json_files)) == 0:
            json_files = directory.glob("*.json")
        try:
            json_file = [file for file in json_files][0]
        except IndexError:
            raise FileNotFoundError(f"No json files found in {directory}")
        return cls.from_json_file(json_file, project)

    @classmethod
    def from_new_record(cls, new_record: NewRecord, project: str):
        return cls(project=project, **new_record.dict())


class ValidatedFAHRecord(SourceRecord):
    run_index: int = Field(..., description="Index of the run")

    @classmethod
    def from_json_file(cls, json_path):
        with open(json_path, "r") as f:
            loaded = json.load(f)
            loaded["home"] = str(json_path.parent)
            return cls(**loaded)

class NewFAHRecord(NewRecord):
    project: str = Field(..., description="Name of the project")
    run_index: int = Field(..., description="Index of the run")
