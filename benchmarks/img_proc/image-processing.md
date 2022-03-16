THIS README FILE IS TAKEN FROM https://github.com/kmu-bigdata/serverless-faas-workbench/wiki/image-processing
Originally Written by: Jeongchul Kim and Kyungyong Lee
## Image Processing
**Library** : (boto3 / azure.functions, azure.storage.file / google.cloud.storage), time, uuid, Pillow
 - aws : build your deployment package

[aws-build-deployment-package](https://github.com/kmu-bigdata/serverless-faas-workbench/wiki/aws-build-deployment-package) -> pillow

Tried the commands and install package
```bash
sudo yum install -y libjpeg-devel zlib-devel
```

 - google : requirements.txt 
```
pillow
google-cloud-storage
```

 - azure : requirements.txt
```
az==0.1.0.dev1
azure-functions==1.0.0b3
azure-functions-worker==1.0.0b3
grpcio==1.14.2
grpcio-tools==1.14.2
protobuf==3.6.1
six==1.12.0
azure_storage_blob==1.0.0
azure-storage-file==1.0.0
cryptography==2.0
numpy
pillow
```
**Workload Input**: Image

**Workload Output**: Image

**Lambda Payload**(test-event) example:

image : [image.jpg](https://github.com/kmu-bigdata/serverless-faas-workbench/blob/master/dataset/image/image.jpg) or https://www.pexels.com/royalty-free-images/ or https://sample-videos.com/download-sample-jpg-image.php
```json
{
    "input_bucket": [INPUT_BUCKET_NAME],
    "object_key": [IMAGE_FILE_NAME],
    "output_bucket": [OUTPUT_BUCKET_NAME],
}
```
or Storage service trigger example(AWS S3):
```python
for record in event['Records']:
   input_bucket = record['s3']['bucket']['name']
   object_key = record['s3']['object']['key']
```
**Lambda Output** : latency
