"""Logger module"""


import logging
from logging.handlers import TimedRotatingFileHandler
import os

from config import PATH


LOGGER = logging.getLogger('main')


if 'log' not in os.listdir(PATH):
    os.mkdir(f'{PATH}/log')

FORMATTER = logging.Formatter()
HANDLER = TimedRotatingFileHandler(
    filename=f'{PATH}/log/log.log',
    when='midnight',
    interval=1,
    backupCount=7,
    encoding='utf-8'
)
HANDLER.setFormatter(FORMATTER)
HANDLER.setLevel(logging.ERROR)
LOGGER.addHandler(HANDLER)
LOGGER.setLevel(logging.ERROR)
