from logging import getLogger

from common.configs import configs
from common.logger import init_logger
from edinet_downlaod import fetch_edinet_docmment_data, generate_date_sequence

init_logger(configs.LOGGER_CONFIG_PATH)

logger = getLogger(__name__)


def main() -> None:
    logger.info("Start main")

    from datetime import date

    date_list = generate_date_sequence(date(2024, 3, 25), date(2024, 3, 25))
    doc_data = fetch_edinet_docmment_data(day=date_list[0])

    logger.info(f"{doc_data=}")
    logger.info("End main")


if __name__ == "__main__":
    main()
