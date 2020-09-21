#! /usr/bin/env python
import os
import boto3
import logging
import argparse

BASIC_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"
logging.basicConfig(format=BASIC_FORMAT, level=logging.INFO)
logger = logging.getLogger()

s3_resource = boto3.resource('s3')
root = os.getcwd()

def handle_dirs(path):
    if not os.path.exists(path):
        os.makedirs(path)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Tool to download data from s3 providing the bucket"
            " and the place where to save it")
    parser.add_argument("--output-directory", "-od", type=str, help="Output directory wher to save the data"
            " example: data", default="data")
    parser.add_argument("--bucket-name", "-bn", type=str, help="Bucket name where the data is",
            default="sagemaker-us-west-2-256305374409")
    parser.add_argument("--key-name", "-kn", type=str, help="Source directroy where to download data",
            default="TiendaApp/data")
    args = parser.parse_args()
    logger.info("Downloading s3 files from {}".format(args.bucket_name))
    bucket = s3_resource.Bucket(args.bucket_name)

    for obj in bucket.objects.filter(Prefix=args.key_name):
        handle_dirs(os.path.join(*os.path.dirname(obj.key).split(os.sep)[1:]))
        bucket.download_file(obj.key, os.path.join(root, *obj.key.split(os.sep)[1:]))
        logger.info("Downloading {} to: {}".format(obj.key,
             os.path.join(*obj.key.split(os.sep)[1:])))
