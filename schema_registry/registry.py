import json
from pathlib import Path
from jsonschema import validate

SCHEMAS_DIR = Path(__file__) / "schemas"


def validate_event(event: str, payload: dict, version: int = 1):
    steps = event.split(".")
    schema_path = SCHEMAS_DIR.joinpath(*steps) / f"{str(version)}.json"
    with schema_path.open() as file:
        schema = json.load(file)

    validate(payload, schema=schema)
