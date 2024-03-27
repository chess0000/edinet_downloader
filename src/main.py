from logging import getLogger

from common.configs import configs
from common.logger import init_logger
from edinet_downlaod import (
    download_securities_report_zip,
    extract_securities_info,
    fetch_edinet_document_binary,
    fetch_edinet_submission_documents,
    generate_date_sequence,
)

init_logger(configs.LOGGER_CONFIG_PATH)

logger = getLogger(__name__)


def main() -> None:
    logger.info("Start main")

    from datetime import date

    date_list = generate_date_sequence(date(2024, 3, 25), date(2024, 3, 25))

    for submission_date in date_list:
        res = fetch_edinet_submission_documents(submission_date)
        for filer_name, doc_id, sec_code in extract_securities_info(res):
            binary_res = fetch_edinet_document_binary(doc_id)
            download_securities_report_zip(
                submission_date, filer_name, doc_id, sec_code, binary_res
            )

    logger.info("End main")


if __name__ == "__main__":
    main()
