"""Project configuration."""

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
ARTIFACT_DIR = PROJECT_ROOT / "artifacts"

DATA_URL = (
    "https://cf-courses-data.s3.us.cloud-object-storage.appdomain.cloud/"
    "_0eYOqji3unP1tDNKWZMjg/weatherAUS-2.csv"
)

MELBOURNE_LOCATIONS = ["Melbourne", "MelbourneAirport", "Watsonia"]
RANDOM_STATE = 42
TEST_SIZE = 0.2
