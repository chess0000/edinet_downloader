from logging import getLogger

from common.configs import configs
from common.logger import init_logger
from edinet_downlaod import (
    download_securities_report_zip,
    generate_date_sequence,
    get_edinet_document_id,
)

init_logger(configs.LOGGER_CONFIG_PATH)

logger = getLogger(__name__)


def main() -> None:
    logger.info("Start main")

    from datetime import date

    date_list = generate_date_sequence(date(2024, 3, 25), date(2024, 3, 25))

    doc_id = get_edinet_document_id(date_list[0])
    download_securities_report_zip(doc_id, date_list[0])

    logger.info("End main")


if __name__ == "__main__":
    main()
