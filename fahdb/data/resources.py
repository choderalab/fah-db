from importlib import resources

DATA = resources.files("fahdb") / "data"
SOURCE = DATA / "source"
FAH = DATA / "fah"
SOURCE_PROJECT = SOURCE / "test_project"
SOURCE_RECORD = SOURCE_PROJECT / "1CC8_73"
SOURCE_JSON = SOURCE_RECORD / "1CC8_73_report.json"