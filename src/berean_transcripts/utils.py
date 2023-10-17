import time
from pathlib import Path
from functools import wraps

project_dir = Path(__file__).resolve().parents[2]
data_dir = project_dir / "data"
raw_dir = data_dir / "raw"
interim_dir = data_dir / "interim"
processed_dir = data_dir / "processed"
external_dir = data_dir / "external"
model_dir = project_dir / "models"
transcripts_dir = data_dir / "transcripts"
html_berean_dir = project_dir / "docs"
whispercpp_dir = project_dir / "whisper.cpp"


def timeit(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        elapsed_time = end_time - start_time
        print(
            f"{func.__name__} completed. Time elapsed: {elapsed_time:.2f} seconds."
        )
        return result

    return wrapper
