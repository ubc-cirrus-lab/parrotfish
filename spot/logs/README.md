## AWS Log Retriever
The logs are retrieved using Boto3. The log retrieval was designed to work independently of the invocation of the function. Therefore, the function can continue to run and the logs are only retrieved when necessary for optimizing the configuration of the serverless function. When the retriever is used, it gathers all logs since the last retrieval, parses them so that their data is indexed for easy searching, and stores them in the database.

A list of invocation IDs that were triggered using the automatic function invocator is also stored in the database and matched with the logs as they are retrieved from AWS. This confirms that all invocated functions have matching logs and the dataset is complete.
Logs for a particular function can be retrieved through the CLI tool using the ‘--fetch’ flag.


### Example Log Output:
```
{
  "ResponseMetadata": {
    "RequestId": "03d92713-a4b2-4b07-a07a-653087817262", 
    "HTTPStatusCode": 200, 
    "HTTPHeaders": {
      "date": "Thu, 25 May 2023 21:46:52 GMT", 
      "content-type": "application/json", 
      "content-length": "508", 
      "connection": "keep-alive", 
      "x-amzn-requestid": "03d92713-a4b2-4b07-a07a-653087817262", 
      "x-amzn-remapped-content-length": "0", 
      "x-amz-executed-version": "$LATEST", 
      "x-amz-log-result": "U1RBUlQgUmVxdWVzdElkOiAwM2Q5MjcxMy1hNGIyLTRiMDctYTA3YS02NTMwODc4MTcyNjIgVmVyc2lvbjogJExBVEVTVApFTkQgUmVxdWVzdElkOiAwM2Q5MjcxMy1hNGIyLTRiMDctYTA3YS02NTMwODc4MTcyNjIKUkVQT1JUIFJlcXVlc3RJZDogMDNkOTI3MTMtYTRiMi00YjA3LWEwN2EtNjUzMDg3ODE3MjYyCUR1cmF0aW9uOiAxODE3OS44NCBtcwlCaWxsZWQgRHVyYXRpb246IDE4MTgwIG1zCU1lbW9yeSBTaXplOiA1MTIgTUIJTWF4IE1lbW9yeSBVc2VkOiA1MDYgTUIJCg==", 
      "x-amzn-trace-id": "root=1-646fd739-681416254b94dc0e0cb32d4f;sampled=0;lineage=cd888fb0:0"
    }, 
    "RetryAttempts": 0
  }, 
  "StatusCode": 200, 
  "LogResult": "U1RBUlQgUmVxdWVzdElkOiAwM2Q5MjcxMy1hNGIyLTRiMDctYTA3YS02NTMwODc4MTcyNjIgVmVyc2lvbjogJExBVEVTVApFTkQgUmVxdWVzdElkOiAwM2Q5MjcxMy1hNGIyLTRiMDctYTA3YS02NTMwODc4MTcyNjIKUkVQT1JUIFJlcXVlc3RJZDogMDNkOTI3MTMtYTRiMi00YjA3LWEwN2EtNjUzMDg3ODE3MjYyCUR1cmF0aW9uOiAxODE3OS44NCBtcwlCaWxsZWQgRHVyYXRpb246IDE4MTgwIG1zCU1lbW9yeSBTaXplOiA1MTIgTUIJTWF4IE1lbW9yeSBVc2VkOiA1MDYgTUIJCg==", 
  "ExecutedVersion": "$LATEST", 
  "Payload": <botocore.response.StreamingBody object at 0x11f4835e0>
}
```

### Example of logs we are parsing
```
"b'START RequestId: 03d92713-a4b2-4b07-a07a-653087817262 Version: $LATEST\\nEND RequestId: 03d92713-a4b2-4b07-a07a-653087817262\\nREPORT RequestId: 03d92713-a4b2-4b07-a07a-653087817262\\tDuration: 18179.84 ms\\tBilled Duration: 18180 ms\\tMemory Size: 512 MB\\tMax Memory Used: 506 MB\\t\\n'"
```