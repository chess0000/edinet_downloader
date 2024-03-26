from logging import getLogger

from common.configs import configs
from common.logger import init_logger
from edinet_downlaod import fetch_edinet_document_json, generate_date_sequence

init_logger(configs.LOGGER_CONFIG_PATH)

logger = getLogger(__name__)


def main() -> None:
    logger.info("Start main")

    from datetime import date

    date_list = generate_date_sequence(date(2024, 3, 25), date(2024, 3, 25))
    doc_data = fetch_edinet_document_json(day=date_list[0])

    if doc_data is None:
        content = None
    else:
        content = doc_data.text

    logger.info(f"{content=}")
    logger.info("End main")


if __name__ == "__main__":
    main()
