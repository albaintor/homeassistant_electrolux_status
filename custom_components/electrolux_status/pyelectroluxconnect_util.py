from logging import Logger
from pyelectroluxocp.oneAppApi import OneAppApi

class pyelectroluxconnect_util:
    @staticmethod
    def get_session(username, password, logger: Logger, language ="eng") -> OneAppApi:
        return OneAppApi(username, password, logger=logger)

