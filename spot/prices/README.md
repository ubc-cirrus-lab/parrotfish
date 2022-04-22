## AWS Price Retriever
The pricing scheme for serverless functions is retrieved using Infracost's Cloud Pricing API which aggregates pricing information from major cloud vendors. The API requires specification of cloud vendor, service, product family and region to fetch the pricing scheme with the indicated parameters. In our tool, we are interested in the pricing scheme of the AWS Lambda serverless functions, which differs by region and is calculated in direct relation to the invocation duration per MB & fixed per request price. Upon the successful return of the request, the price retriever parses the response to save Request Price, Duration Price and the Region to the local database. This ensures our model always has up-to-date prices. Furthermore, it also ensures that the historical logs are associated with the respective pricing scheme that generated the log.

### Example Pricing Scheme:
```
{
  "request_price": 2e-7,
  "duration_price": 0.0000166667,
  "timestamp": 163980957281,
  "Region": "us-east-1"
}
```