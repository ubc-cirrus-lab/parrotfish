## AWS Log Retriever
The logs are retrieved using Boto3. The log retrieval was designed to work independently of the invocation of the function. Therefore, the function can continue to run and the logs are only retrieved when necessary for optimizing the configuration of the serverless function. When the retriever is used, it gathers all logs since the last retrieval, parses them so that their data is indexed for easy searching, and stores them in the database.

A list of invocation IDs that were triggered using the automatic function invocator is also stored in the database and matched with the logs as they are retrieved from AWS. This confirms that all invocated functions have matching logs and the dataset is complete.
Logs for a particular function can be retrieved through the CLI tool using the ‘--fetch’ flag.


### Example Log Output:
```json
{
        "_id" : ObjectId("61b3b35cb537d4c93cb3c8b7"),
        "events" : [
                {
                        "timestamp" : NumberLong("1637821607905"),
                        "message" : "START RequestId: 0fb4aad7-d79f-450a-ba14-be3a69f322ac Version: $LATEST\n",
                        "ingestionTime" : NumberLong("1637821610412")
                },
                {
                        "timestamp" : NumberLong("1637821607910"),
                        "message" : "END RequestId: 0fb4aad7-d79f-450a-ba14-be3a69f322ac\n",
                        "ingestionTime" : NumberLong("1637821610412")
                },
                {
                        "timestamp" : NumberLong("1637821607910"),
                        "message" : "REPORT RequestId: 0fb4aad7-d79f-450a-ba14-be3a69f322ac\tDuration: 1.26 ms\tBilled Duration: 2 ms\tMemory Size: 150 MB\tMax Memory Used: 39 MB\tInit Duration: 127.51 ms\t\n",
                        "ingestionTime" : NumberLong("1637821610412")
                }
        ],
        "nextForwardToken" : "f/36524642358648637365024290440755907809751973742718156802/s",
        "nextBackwardToken" : "b/36524642358537133639031637325048229218388731935188254720/s"
}
```