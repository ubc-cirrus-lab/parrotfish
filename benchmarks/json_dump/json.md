THIS WIKI PAGE IS TAKEN FROM https://github.com/kmu-bigdata/serverless-faas-workbench/wiki/json
Originally Written by: Jeongchul Kim and Kyungyong Lee
# JSON serialization deserialization

JSON serialize-deserialize module. The application performs JSON deserialization using a JSON-encoded string dataset downloaded from a public object storage service, and it serializes the JSON object again.

**Library** : json

**Input**(test-event) example:
 - JSON DATASET LINK : https://github.com/jdorfman/awesome-json-datasets/
 - link example : http://www.vizgr.org/historical-events/search.php?format=json&begin_date=-3000000&end_date=20151231&lang=en

```json
{
    "link": [JSON DATASET LINK]
}
```

**Output** : network download time and serialization-deserialization time