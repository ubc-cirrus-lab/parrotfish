from src.exploration.log_parser import LogParser


class GCPLogParser(LogParser):
    def __init__(self):
        super().__init__(['Function execution took', 'finished with status'])

    def parse_log(self, log: str) -> int:
        pass
