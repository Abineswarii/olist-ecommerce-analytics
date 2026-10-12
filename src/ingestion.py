import pandas as pd

from config import DATA_DIR, FILES, REQUIRED_COLUMNS
from database import get_engine


def load_raw_tables():
    engine = get_engine()

    for table_name, file_name in FILES.items():

        file_path = DATA_DIR / file_name

        print(f"Loading {file_name}...")

        # Check if file exists
        if not file_path.exists():
            raise FileNotFoundError(
                f"Required file not found: {file_path}"
            )

        # Read CSV
        df = pd.read_csv(file_path)

        print(
            f"{file_name}: "
            f"{len(df)} rows, "
            f"{len(df.columns)} columns"
        )

        # Check required columns
        expected_columns = REQUIRED_COLUMNS[table_name]

        missing_columns = [
            column
            for column in expected_columns
            if column not in df.columns
        ]

        if missing_columns:
            raise ValueError(
                f"{file_name} is missing required columns: "
                f"{missing_columns}"
            )

        # Load into RAW table
        df.to_sql(
            f"raw_{table_name}",
            engine,
            if_exists="replace",
            index=False
        )

        print(f"Created table raw_{table_name}")


if __name__ == "__main__":
    load_raw_tables()