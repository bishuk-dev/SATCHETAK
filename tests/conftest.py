"""Keep automated tests independent from developer credentials and local services."""
import os
from pathlib import Path


os.environ["SATCHETAK_ENV_FILE"] = str(Path(__file__).with_name(".env.test-disabled"))
for variable in (
    "CDSE_CLIENT_ID",
    "CDSE_CLIENT_SECRET",
    "QWEN_BASE_URL",
    "QWEN_MODEL",
    "QWEN_API_KEY",
    "BHOONIDHI_USER_ID",
    "BHOONIDHI_PASSWORD",
    "BHOONIDHI_COLLECTION",
):
    os.environ.pop(variable, None)
