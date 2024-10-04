import pandas as pd
from pydantic import BaseModel, Field, validator
from pathlib import Path
import abc
import shutil

from fahdb.records import NewRecord, StructureRecord, SourceRecord, ValidatedFAHRecord, NewFAHRecord


class NewStructureDatabase(BaseModel):
    """
    Schema for a database of structures that are not yet in the database
    """

    home: str = Field(..., description="Path to the home directory of the database")
    records: list[NewRecord] = Field(..., description="List of records in the database")

    @classmethod
    def from_csv(cls, home: str, csv_path: str):
        df = pd.read_csv(csv_path)
        df = df.astype(str)
        return cls(
            home=home,
            records=[
                NewRecord(home=home, **record)
                for record in df.to_dict(orient="records")
            ],
        )

    def to_json(self):
        for record in self.records:
            with open(f"{record.unique_id}.json", "w") as f:
                f.write(record.json())


class InputStructureDatabase(BaseModel):
    home: str = Field(..., description="Path to the home directory of the database")
    records: list[StructureRecord] = Field(
        ..., description="List of records in the database"
    )

    @validator("home")
    def home_exists(cls, v):
        """
        Validate that the home directory exists
        :param v:
        :return:
        """
        if not Path(v).exists():
            raise FileNotFoundError(f"Path {v} does not exist")
        return v

    @classmethod
    def from_csv(cls, home: str, csv_path: str):
        df = pd.read_csv(csv_path)
        df = df.astype(str)
        return cls(
            home=home,
            records=[
                StructureRecord(home=home, **record)
                for record in df.to_dict(orient="records")
            ],
        )

    def to_json(self):
        for record in self.records:
            with open(f"{record.unique_id}.json", "w") as f:
                f.write(record.json())


class DatabaseBase(BaseModel):
    home: str = Field(..., description="Path to the home directory of the database")
    records: list[SourceRecord] = Field(
        ..., description="List of records in the project"
    )
    projects: list[str] = Field(..., description="List of projects in the database")

    class Config:
        arbitrary_types_allowed = True

    @abc.abstractmethod
    def from_directory(self, input_dir: str):
        pass


class SourceDatabase(DatabaseBase):
    records: list[SourceRecord] = Field(
        ..., description="List of records in the project"
    )

    @classmethod
    def from_directory(cls, input_dir: str):
        # get list of directories in input_dir
        records = []
        projects = []

        # Iterate through project and run directories, generating records from the files found there
        for project_dir in Path(input_dir).iterdir():
            if project_dir.is_dir():
                projects.append(project_dir.name)
                for run_dir in project_dir.iterdir():
                    if run_dir.is_dir():
                        records.append(
                            SourceRecord.from_directory(run_dir, project=project_dir.name)
                        )
        return SourceDatabase(
            home=str(input_dir), records=records, projects=list(set(projects))
        )

    def report(self):
        print(f"Projects ({len(self.projects)}): ")
        for project in self.projects:
            print(f"\t{project} :")
            print(f"\t\tRuns ({len([record for record in self.records if record.project == project])}):")


class ComparisonReport(BaseModel):
    source: str = Field(..., description="Path to the source database")
    target: str = Field(..., description="Path to the target database")
    missing: list[SourceRecord] = Field(
        ..., description="List of records missing in the target database"
    )
    extra: list[SourceRecord] = Field(
        ...,
        description="List of records in the target database that are not in the source database",
    )

    def report(self):
        print(f"Source: {self.source}")
        print(f"Target: {self.target}")
        print(f"Missing records ({len(self.missing)}):")
        for record in self.missing:
            print(f"\t{record}")
        print(f"Extra records ({len(self.extra)}):")
        for record in self.extra:
            print(f"\t{record}")


class FAHDatabase(DatabaseBase):
    records: list[ValidatedFAHRecord] = Field(
        ..., description="List of records in the project"
    )

    @property
    def max_run_index_per_project(self) -> dict[str, int]:
        max_run_index_per_project = {}
        for project in self.projects:
            max_run_index = max(
                record.run_index for record in self.records if record.project == project
            )
            max_run_index_per_project[project] = max_run_index
        return max_run_index_per_project

    @classmethod
    def from_directory(
        cls, input_dir: str, ignore_missing: bool = False, ignore_extra: bool = False
    ):
        # get list of directories in input_dir
        records = []
        projects = []
        for project_dir in Path(input_dir).iterdir():
            if project_dir.is_dir():
                projects.append(project_dir.name)
                for run_dir in project_dir.iterdir():
                    if run_dir.is_dir():
                        fah_record = list(run_dir.glob("*record.json"))
                        if fah_record:
                            fah_record = fah_record[0]
                        else:
                            continue
                        records.append(ValidatedFAHRecord.from_json_file(fah_record))
        db_from_dir = cls(home=str(input_dir), records=records, projects=list(set(projects)))
        csv_path = Path(input_dir) / "database.csv"
        if csv_path.exists():
            db_from_csv = cls._from_csv(str(csv_path))
            comparison = db_from_dir.compare_to_source(db_from_csv)
            if comparison.missing and not ignore_missing:
                raise FileNotFoundError(f"Missing records: {comparison.missing}")
            if comparison.extra and not ignore_extra:
                raise FileNotFoundError(f"Missing records: {comparison.extra}")
        return db_from_dir

    @classmethod
    def _from_csv(cls, csv_path: str):
        df = pd.read_csv(csv_path, dtype=str)
        return cls(
            home=str(Path(csv_path).parent),
            records=[ValidatedFAHRecord(**record) for record in df.to_dict(orient="records")],
            projects=list(df["project"].astype(str).unique()),
        )

    def _to_csv(self):
        df = pd.DataFrame([record.dict() for record in self.records])
        df.sort_values(["project", "run_index"], inplace=True)
        df.to_csv(Path(self.home) / "database.csv", index=False)

    def compare_to_source(self, source: DatabaseBase) -> ComparisonReport:
        source_unique_ids = {record.unique_id for record in source.records}
        fah_unique_ids = {record.unique_id for record in self.records}
        missing = source_unique_ids - fah_unique_ids
        missing_records = [
            record for record in source.records if record.unique_id in missing
        ]
        missing_records.sort(key=lambda x: x.unique_id)
        extra_records = [
            record
            for record in self.records
            if record.unique_id not in source_unique_ids
        ]
        return ComparisonReport(
            source=source.home,
            target=self.home,
            missing=missing_records,
            extra=extra_records,
        )

    def get_new_record(self, run_index: int, record: SourceRecord):
        return NewFAHRecord(
            run_index=run_index,
            unique_id=record.unique_id,
            project=record.project,
            home=str(Path(self.home) / record.project / f"RUN{run_index}"),
            rcsb_id=record.rcsb_id,
            sequence=record.sequence,
        )

    def get_missing(self, source: DatabaseBase):
        comparison = self.compare_to_source(source)
        new_records = []
        indices = self.max_run_index_per_project.copy()
        for record in comparison.missing:
            indices[record.project] = indices.get(record.project, -1) + 1
            print(record, indices[record.project])
            new_records.append(self.get_new_record(indices[record.project], record))
        return comparison.missing, new_records

    def sync(self, source_db: DatabaseBase, sync: bool = False):
        missing, new_records = self.get_missing(source_db)
        for old, new in zip(missing, new_records):
            if sync:
                shutil.copytree(old.home, new.home)
                new.write_json_file()

            else:
                print(f"Would copy {old.home} to {new.home}")
        if sync:
            validated_records = [
                ValidatedFAHRecord(**record.dict()) for record in new_records
            ]
            self.records.extend(validated_records)
            self._to_csv()

    def report(self):
        print(f"Projects ({len(self.projects)}): ")
        for project in self.projects:
            print(f"\t{project} :")
            print(f"\t\tRuns ({len([record for record in self.records if record.project == project])}):")
