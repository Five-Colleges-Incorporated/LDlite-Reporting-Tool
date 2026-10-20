import logging
import os
from datetime import datetime

import dotenv

from ldlite_reporting_tool import launch

if __name__ == "__main__":
    dotenv.load_dotenv()

    os.makedirs(os.getenv('log_file_output_filepath'), exist_ok=True)

    start_time = datetime.now()
    logFile = f"{os.getenv('log_file_output_filepath')}/LDlite Reporting - {start_time.year}-{start_time.month}-{start_time.day}--{start_time.hour}-{start_time.minute}-{start_time.second}.log"
    logging.basicConfig(filename=logFile, encoding='utf-8', level=logging.DEBUG,
                    format='%(asctime)s | %(levelname)s | %(message)s', datefmt='%m/%d/%Y %H:%M:%S')
    logging.info("Beginning Log")

    launch()

