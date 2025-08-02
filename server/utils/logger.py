import logging

# Define logger for the server
logger = logging.getLogger("uvicorn.error")
logger.setLevel(logging.INFO)


if not logger.hasHandlers():  # Prevent double logging
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        "[%(asctime)s] %(levelname)s - %(name)s - %(message)s"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
