"""A program to execute parameterized sql queries against a postgresql database.

Copyright (C) 2022-2026  Amelia Sutton
This software is distributed under the terms of the GNU General Public License
as published by the Free Software Foundation, either version 3 of the License, or
(at your option) any later version. See the file "[COPYING](COPYING)" for more details.
"""

import logging
import os
from datetime import datetime
from pathlib import Path

import dotenv

from ldlite_reporting_tool import launch

if __name__ == "__main__":
    dotenv.load_dotenv()

    Path.mkdir(Path(os.getenv("LOG_FILE_OUTPUT_FILEPATH", "")), exist_ok=True)

    start_time = datetime.now()
    log_file = "{}/LDlite Reporting - {}-{}-{}--{}-{}-{}.log".format(
        os.getenv("LOG_FILE_OUTPUT_FILEPATH"),
        start_time.year,
        start_time.month,
        start_time.day,
        start_time.hour,
        start_time.minute,
        start_time.second,
    )
    logger = logging.getLogger(__name__)
    logging.basicConfig(
        filename=log_file,
        encoding="utf-8",
        level=logging.DEBUG,
        format="%(asctime)s | %(levelname)s | %(message)s",
        datefmt="%m/%d/%Y %H:%M:%S",
    )
    logger.info("Beginning Log")

    launch()
