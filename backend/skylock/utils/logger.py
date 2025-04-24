import logging

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger("skylock")

if not any(isinstance(h, logging.FileHandler) for h in logger.handlers):
    log_file = logging.FileHandler("totp.log")
    log_file.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(message)s"))
    logger.addHandler(log_file)
