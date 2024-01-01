import logging
import os

class CustomLogger(object):

    """Docstring for CustomLogger. """

    def __init__(self, verbose: bool=False):
        """TODO: to be defined. """
        self.verbose = verbose

    def getLogger(self, name: str):
        """docstring for getLogger"""
        logger = logging.getLogger(__name__)

        # create console handler and set level to debug
        ch = logging.StreamHandler()

        if self.verbose:
            logger.setLevel(self.verbose)
            ch.setLevel(self.verbose)

        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        ch.setFormatter(formatter)
        logger.addHandler(ch)

        return logger
