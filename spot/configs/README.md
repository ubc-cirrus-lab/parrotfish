## AWS Config Retriever
This module fetches the current serverless function configuration through Boto3. Then, if the configuration hasn't been updated since the last saved config, configurations are saved to the local database with a timestamp so they can be correlated with logs.

### Example Config Output:
```json
{
        "_id" : ObjectId("61b3beaee841f6f62091b06d"),
        "FunctionName" : "AWSHelloWorld",
        "FunctionArn" : "arn:aws:lambda:us-east-2:113868870694:function:AWSHelloWorld",
        "Runtime" : "python3.8",
        "Role" : "arn:aws:iam::113868870694:role/service-role/AWSHelloWorld-role-gxffonta",
        "Handler" : "lambda_function.lambda_handler",
        "CodeSize" : 299,
        "Description" : "",
        "Timeout" : 3,
        "MemorySize" : 150,
        "LastModified" : "2021-11-12T20:09:07.298+0000",
        "CodeSha256" : "fI06ZlRH/KN6Ra3twvdRllUYaxv182Tjx0qNWNlKIhI=",
        "Version" : "$LATEST",
        "TracingConfig" : {
                "Mode" : "PassThrough"
        },
        "RevisionId" : "cb35ed27-34b0-4bad-89e5-37b03eb374a0",
        "State" : "Active",
        "LastUpdateStatus" : "Successful",
        "PackageType" : "Zip",
        "Architectures" : [
                "x86_64"
        ]
}
```