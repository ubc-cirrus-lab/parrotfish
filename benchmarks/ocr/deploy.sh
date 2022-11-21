#!/bin/bash

set -eu

lambda_name=$1
s3_bucket=$2
s3_file_key=$3

zip_file_name="lambda-ocrtopdf.zip"
download_url="https://github.com/chronograph-pe/lambda-OCRmyPDF/releases/download/v1.0-alpha/lambda-ocrtopdf.zip"

wget -O $zip_file_name $download_url

aws s3 cp  $zip_file_name s3://$s3_bucket/$s3_file_key
aws lambda update-function-code --function-name $lambda_name --s3-bucket $s3_bucket --s3-key $s3_file_key
aws lambda update-function-configuration --function-name $lambda_name \
                                        --handler apply-ocr-to-s3-object.apply_ocr_to_document_handler \
                                        --environment "Variables={PATH=/var/task/bin,PYTHONPATH=/var/task/python,TESSDATA_PREFIX=/var/task/tessdata}" \
                                        --timeout 900 \
                                        --memory-size 3008 \
                                        --runtime "python3.6"
