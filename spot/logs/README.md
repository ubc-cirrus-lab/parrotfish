## AWS Log Retriever
* Retrieves logs of the given function 
* Populates them in the MongoDB database

### Example Log Output:
```
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