## Log Parser
After invoking the serverless function synchronously and wait for the response, we parse the log result based on the log keys specific for each cloud provider.

### Example AWS Lambda Log Result from the HTTP Body of the response:
[Reference]("https://docs.aws.amazon.com/lambda/latest/dg/API_Invoke.html#API_Invoke_ResponseSyntax")
Here the LogResult contains the last 4 KB of the execution log, which is base64-encoded.
#### After decoding the retrieved logs:
```
b'START RequestId: 03d92713-a4b2-4b07-a07a-653087817262 Version: $LATEST\\nEND RequestId: 03d92713-a4b2-4b07-a07a-653087817262\\n
REPORT RequestId: 03d92713-a4b2-4b07-a07a-653087817262\\tDuration: 18179.84 ms\\tBilled Duration: 18180 ms\\tMemory Size: 512 MB\\tMax Memory Used: 506 MB\\t\\n'
```
#### After parsing the response:
```python
Result = {'Duration': 18179.84, 'Billed Duration': 18180.0, 'Max Memory Used': 506.0, 'Memory Size': 512.0}
```
