"""Top-level package for checkmate"""

__version__ = "0.1.0"
__app__ = "checkmate"
__description__ = "Model-agnostic LLM vulnerability scanner"

import logging
import os
from checkmate import _config

CHECKMATE_LOG_FILE_VAR = "CHECKMATE_LOG_FILE"

# allow for a file path configuration from the ENV and set for child processes
_log_filename = os.getenv(CHECKMATE_LOG_FILE_VAR, default=None)
if _log_filename is None:
    _log_filename = _config.transient.data_dir / "checkmate.log"
    os.environ[CHECKMATE_LOG_FILE_VAR] = str(_log_filename)

_config.transient.log_filename = _log_filename

logging.basicConfig(
    filename=_log_filename,
    level=logging.DEBUG,
    format="%(asctime)s  %(levelname)s  %(message)s",
)