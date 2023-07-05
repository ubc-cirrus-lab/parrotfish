from src.exploration.log_parser import LogParser


class GCPLogParser(LogParser):
    def __init__(self):
        super().__init__(['finished with status code'])

    def parse_log(self, log: str) -> int:
        pass
