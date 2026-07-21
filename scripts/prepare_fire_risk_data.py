from pathlib import Path

import pandas as pd
from sklearn.model_selection import train_test_split


# ---------------------------------------------------------
# PROJECT PATHS
# ---------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent

RAW_DATA_PATH = (
    BASE_DIR
    / "data"
    / "raw"
    / "industrial_fire_risk_data.csv"
)

PROCESSED_DATA_DIR = (
    BASE_DIR
    / "data"
    / "processed"
)

TRAIN_OUTPUT_PATH = (
    PROCESSED_DATA_DIR
    / "fire_risk_train.csv"
)

VALIDATION_OUTPUT_PATH = (
    PROCESSED_DATA_DIR
    / "fire_risk_validation.csv"
)

TEST_OUTPUT_PATH = (
    PROCESSED_DATA_DIR
    / "fire_risk_test.csv"
)

AUDIT_OUTPUT_PATH = (
    PROCESSED_DATA_DIR
    / "fire_risk_data_audit.csv"
)


# ---------------------------------------------------------
# COLUMN CONFIGURATION
# ---------------------------------------------------------

TARGET_COLUMN = "accident"

LEAKAGE_COLUMNS = [
    "risk"
]

REQUIRED_COLUMNS = [
    "date",
    "time",
    "factory",
    "region",
    "shift",
    "workers",
    "experience_level",
    "training",
    "temperature",
    "pressure",
    "humidity",
    "vibration",
    "machine_speed",
    "equipment_age",
    "service_days",
    "gas",
    "sparks",
    "alarm",
    "accident",
]


# ---------------------------------------------------------
# HELPER FUNCTIONS
# ---------------------------------------------------------

def standardize_column_names(
    dataframe: pd.DataFrame
) -> pd.DataFrame:
    """
    Converts the original dataset column names into clear,
    consistent backend column names.
    """

    column_mapping = {
        "Date": "date",
        "Time": "time",
        "Factory": "factory",
        "Region": "region",
        "Shift": "shift",
        "Workers": "workers",
        "Exp": "experience_level",
        "Training": "training",
        "Temp": "temperature",
        "Pressure": "pressure",
        "Humidity": "humidity",
        "Vibration": "vibration",
        "Speed": "machine_speed",
        "Age": "equipment_age",
        "Service_Days": "service_days",
        "Gas": "gas",
        "Sparks": "sparks",
        "Alarm": "alarm",
        "Risk": "risk",
        "Accident": "accident",
    }

    return dataframe.rename(
        columns=column_mapping
    )


def validate_required_columns(
    dataframe: pd.DataFrame
) -> None:
    """
    Stops execution if an important expected column is missing.
    """

    missing_columns = [
        column
        for column in REQUIRED_COLUMNS
        if column not in dataframe.columns
    ]

    if missing_columns:
        raise ValueError(
            "Required columns are missing: "
            + ", ".join(missing_columns)
        )


def create_timestamp(
    dataframe: pd.DataFrame
) -> pd.DataFrame:
    """
    Combines the date and time columns into one timestamp.
    """

    dataframe["timestamp"] = pd.to_datetime(
        dataframe["date"].astype(str)
        + " "
        + dataframe["time"].astype(str),
        errors="coerce",
    )

    invalid_timestamps = (
        dataframe["timestamp"].isna().sum()
    )

    if invalid_timestamps > 0:
        print(
            f"Warning: {invalid_timestamps} rows have "
            "invalid timestamps."
        )

    dataframe["year"] = (
        dataframe["timestamp"].dt.year
    )

    dataframe["month"] = (
        dataframe["timestamp"].dt.month
    )

    dataframe["hour"] = (
        dataframe["timestamp"].dt.hour
    )

    dataframe["day_of_week"] = (
        dataframe["timestamp"].dt.dayofweek
    )

    return dataframe


def clean_categorical_columns(
    dataframe: pd.DataFrame
) -> pd.DataFrame:
    """
    Removes accidental spaces and makes category values
    consistent.
    """

    categorical_columns = [
        "factory",
        "region",
        "shift",
        "experience_level",
        "training",
        "alarm",
    ]

    for column in categorical_columns:
        dataframe[column] = (
            dataframe[column]
            .astype(str)
            .str.strip()
        )

    dataframe["training"] = (
        dataframe["training"]
        .str.lower()
        .map({
            "yes": "yes",
            "no": "no",
        })
        .fillna("unknown")
    )

    dataframe["alarm"] = (
        dataframe["alarm"]
        .str.lower()
        .map({
            "on": "on",
            "off": "off",
        })
        .fillna("unknown")
    )

    dataframe["shift"] = (
        dataframe["shift"]
        .str.lower()
    )

    dataframe["experience_level"] = (
        dataframe["experience_level"]
        .str.lower()
    )

    return dataframe


def handle_missing_values(
    dataframe: pd.DataFrame
) -> pd.DataFrame:
    """
    Handles missing values without using information from
    the accident target.

    The Workers column has missing values in the source data.
    We first use the factory-and-shift median, then the overall
    median as a fallback.
    """

    dataframe["workers"] = (
        dataframe.groupby(
            ["factory", "shift"]
        )["workers"]
        .transform(
            lambda series: series.fillna(
                series.median()
            )
        )
    )

    dataframe["workers"] = (
        dataframe["workers"]
        .fillna(
            dataframe["workers"].median()
        )
    )

    numeric_columns = [
        "temperature",
        "pressure",
        "humidity",
        "vibration",
        "machine_speed",
        "equipment_age",
        "service_days",
        "gas",
        "sparks",
    ]

    for column in numeric_columns:
        dataframe[column] = (
            dataframe[column]
            .fillna(
                dataframe[column].median()
            )
        )

    return dataframe


def validate_target(
    dataframe: pd.DataFrame
) -> None:
    """
    Confirms that Accident is a binary prediction target.
    """

    target_values = set(
        dataframe[TARGET_COLUMN]
        .dropna()
        .unique()
        .tolist()
    )

    if not target_values.issubset({0, 1}):
        raise ValueError(
            "The accident target must contain only 0 and 1. "
            f"Found: {target_values}"
        )


def remove_duplicate_rows(
    dataframe: pd.DataFrame
) -> pd.DataFrame:
    duplicate_count = (
        dataframe.duplicated().sum()
    )

    if duplicate_count > 0:
        print(
            f"Removing {duplicate_count} duplicate rows."
        )

    return dataframe.drop_duplicates().copy()


def create_data_audit(
    dataframe: pd.DataFrame
) -> pd.DataFrame:
    """
    Creates a summary file describing every column.
    """

    audit_rows = []

    for column in dataframe.columns:
        audit_rows.append({
            "column": column,
            "data_type": str(
                dataframe[column].dtype
            ),
            "row_count": len(dataframe),
            "missing_count": int(
                dataframe[column].isna().sum()
            ),
            "missing_percent": round(
                dataframe[column]
                .isna()
                .mean()
                * 100,
                2,
            ),
            "unique_values": int(
                dataframe[column].nunique(
                    dropna=True
                )
            ),
        })

    return pd.DataFrame(audit_rows)


def print_dataset_summary(
    dataframe: pd.DataFrame
) -> None:
    total_rows = len(dataframe)

    accident_count = int(
        dataframe[TARGET_COLUMN].sum()
    )

    non_accident_count = (
        total_rows - accident_count
    )

    accident_rate = (
        accident_count
        / total_rows
        * 100
    )

    print("\nDATASET SUMMARY")
    print("-" * 50)
    print(f"Total rows: {total_rows}")
    print(
        f"Non-accident rows: "
        f"{non_accident_count}"
    )
    print(
        f"Accident rows: {accident_count}"
    )
    print(
        f"Accident rate: "
        f"{accident_rate:.2f}%"
    )
    print("-" * 50)


def split_dataset(
    dataframe: pd.DataFrame
) -> tuple[
    pd.DataFrame,
    pd.DataFrame,
    pd.DataFrame,
]:
    """
    Creates:
    - 70% training data
    - 15% validation data
    - 15% test data

    Stratification keeps the accident proportion similar
    across all three datasets.
    """

    train_dataframe, temporary_dataframe = (
        train_test_split(
            dataframe,
            test_size=0.30,
            random_state=42,
            stratify=dataframe[TARGET_COLUMN],
        )
    )

    validation_dataframe, test_dataframe = (
        train_test_split(
            temporary_dataframe,
            test_size=0.50,
            random_state=42,
            stratify=(
                temporary_dataframe[
                    TARGET_COLUMN
                ]
            ),
        )
    )

    return (
        train_dataframe,
        validation_dataframe,
        test_dataframe,
    )


# ---------------------------------------------------------
# MAIN PIPELINE
# ---------------------------------------------------------

def prepare_fire_risk_dataset() -> None:
    print(
        f"Reading dataset from:\n"
        f"{RAW_DATA_PATH}"
    )

    if not RAW_DATA_PATH.exists():
        raise FileNotFoundError(
            "Fire-risk dataset was not found at:\n"
            f"{RAW_DATA_PATH}"
        )

    PROCESSED_DATA_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    dataframe = pd.read_csv(
        RAW_DATA_PATH
    )

    print(
        f"Original dataset shape: "
        f"{dataframe.shape}"
    )

    dataframe = standardize_column_names(
        dataframe
    )

    validate_required_columns(
        dataframe
    )

    validate_target(
        dataframe
    )

    dataframe = remove_duplicate_rows(
        dataframe
    )

    dataframe = create_timestamp(
        dataframe
    )

    dataframe = clean_categorical_columns(
        dataframe
    )

    dataframe = handle_missing_values(
        dataframe
    )

    # Do not use the existing risk score as a model feature.
    dataframe = dataframe.drop(
        columns=LEAKAGE_COLUMNS,
        errors="ignore",
    )

    # Original date and time are no longer required after
    # creating the timestamp and time-derived features.
    dataframe = dataframe.drop(
        columns=[
            "date",
            "time",
        ],
        errors="ignore",
    )

    # Remove rows where timestamp parsing failed.
    dataframe = dataframe.dropna(
        subset=["timestamp"]
    )

    # Sort chronologically to make later time-aware testing easier.
    dataframe = dataframe.sort_values(
        by="timestamp"
    ).reset_index(drop=True)

    audit_dataframe = create_data_audit(
        dataframe
    )

    audit_dataframe.to_csv(
        AUDIT_OUTPUT_PATH,
        index=False,
    )

    print_dataset_summary(
        dataframe
    )

    (
        train_dataframe,
        validation_dataframe,
        test_dataframe,
    ) = split_dataset(dataframe)

    train_dataframe.to_csv(
        TRAIN_OUTPUT_PATH,
        index=False,
    )

    validation_dataframe.to_csv(
        VALIDATION_OUTPUT_PATH,
        index=False,
    )

    test_dataframe.to_csv(
        TEST_OUTPUT_PATH,
        index=False,
    )

    print("\nOUTPUT FILES CREATED")
    print("-" * 50)

    print(
        f"Training data: "
        f"{TRAIN_OUTPUT_PATH}"
    )

    print(
        f"Training shape: "
        f"{train_dataframe.shape}"
    )

    print(
        f"Validation data: "
        f"{VALIDATION_OUTPUT_PATH}"
    )

    print(
        f"Validation shape: "
        f"{validation_dataframe.shape}"
    )

    print(
        f"Test data: "
        f"{TEST_OUTPUT_PATH}"
    )

    print(
        f"Test shape: "
        f"{test_dataframe.shape}"
    )

    print(
        f"Audit report: "
        f"{AUDIT_OUTPUT_PATH}"
    )


if __name__ == "__main__":
    prepare_fire_risk_dataset()