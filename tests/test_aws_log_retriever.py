import unittest
import boto3
from pymongo import MongoClient

from spot.logs.aws_log_retriever import AWSLogRetriever


class TestLogRetrival(unittest.TestCase):
    # mock log & see if it gets parsed and stored correctly 
    def setUp(self) -> None:
        function = 'AWSHelloWorld'
        logGroup = '/aws/lambda/' + function
        logClient = boto3.client("logs")
        res = logClient.describe_log_streams(
            logGroupName=logGroup, orderBy='LastEventTime', descending=False, limit=1
        )
        stream = res["logStreams"][0]

        res = logClient.get_log_events(
            logGroupName=logGroup,
            logStreamName=stream['logStreamName'],
            startFromHead=True
        )
        self.timestamp = res['events'][0]['timestamp']
        self.logRetriever = AWSLogRetriever(logGroup, 'localhost', 27017, self.timestamp)

        # remove all logs after this timestamp?
        mongoClient = MongoClient('localhost', 27017)
        logCollection = mongoClient[function]['logs']
        self.dbLogs = logCollection.find({'timestamp':{'$ge': self.timestamp}}).sort('timestamp')
        print(self.dbLogs)


    def test_get_logs(self) -> None:
        # assert no logs for a certain timestamp in db
        self.logRetriever.get_logs()
        # assert db populated
        pass
