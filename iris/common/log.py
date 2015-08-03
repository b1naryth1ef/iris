import logging

FORMAT = "[%(levelname)s] %(asctime)s - %(name)s:%(lineno)d - %(message)s"
logging.basicConfig(level=logging.DEBUG, format=FORMAT)

logging.getLogger('pystun').setLevel(logging.WARN)
logging.getLogger('requests').setLevel(logging.WARN)

