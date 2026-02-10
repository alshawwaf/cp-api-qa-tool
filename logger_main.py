import logging
from pathlib import Path

try:
    Path(f"logs").mkdir(parents=True, exist_ok=True)
    print(f"Created the logsfolder")
except Exception as exception:
    print(f"failed to create the logs folder with exception: {exception}")


logging.basicConfig(level=logging.DEBUG, filename='./logs/api_qa.log', filemode='w', format='%(name)s - %(levelname)s - %(message)s')
console = logging.StreamHandler()
console.setLevel(logging.INFO)
console.setFormatter(logging.Formatter("%(levelname)s %(message)s"))
log = logging.getLogger(__name__)
log.addHandler(console)
log.info('Logger created')