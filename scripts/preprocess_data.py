#! /usr/bin/env python
import os
import logging
import argparse
import json
import boto3
import shutil
import numpy as np
import pandas as pd
from tqdm import tqdm
from sklearn.model_selection import train_test_split

BASIC_FORMAT="%(asctime)s - %(levelname)s - %(message)s"
logging.basicConfig(level=logging.INFO, format=BASIC_FORMAT)
logger = logging.getLogger()

client = boto3.client("s3")
root = os.getcwd()

def pretty_json(obj):
  return json.dumps(obj, indent=2)

def handle_dirs(path):
  if not os.path.exists(path):
    os.makedirs(path)

def make_all_dirs(*args):
  for path in args:
    logger.info("paths to create: " + path)
    handle_dirs(path)

def delete_missing(txt_paths, path, delete=True):
  txt_paths = [os.path.join(path, txt_path) for txt_path in txt_paths]
  count = 0
  contents = []
  for txt_path in txt_paths:
    file = open(txt_path, "r")
    lines = file.readlines()
    if len(lines)<1 and delete:
      logger.info("Deleting {} does not have any label".format(txt_path[len(root)+1:]))
      # os.remove(txt_path)
      # os.remove(txt_path.replace("txt", "jpg"))
      count += 1
    else:
      contents.append([txt_path, lines])
  if count == 0:
    logger.info("Nothing to delete")
  return contents
    
def clean_dataset(path, delete):
  logger.info("Cleaning data without annotations on {}".format(path))
  img_paths = [os.path.join("obj_train_data", file) for file in os.listdir(os.path.join(path, "obj_train_data"))]
  txt_paths = [img_path for img_path in img_paths if "txt" in img_path]
  # check missing
  return delete_missing(txt_paths, path, delete)

def generating_txt(root, training_path, validation_path, output_directory):
  train_content = [os.path.join(training_path[len(root)+1:], file) for file in os.listdir(training_path) 
                   if "jpg" in file]
  val_content = [os.path.join(validation_path[len(root)+1:], file) for file in os.listdir(validation_path) 
                 if "jpg" in file]
  train_file = open(os.path.join(root, output_directory, "train.txt"), "w")
  val_file = open(os.path.join(root, output_directory, "val.txt"), "w")
  obj_data = open(os.path.join(root, output_directory, "obj.data"), "w")
  obj_name = open(os.path.join(root, output_directory, "obj.names"), "r")
  classes = obj_name.readlines()
  obj_name.close()
  obj_data.write("classes = {}\n".format(len(classes)))
  obj_data.write("train = {}\n".format(os.path.join(output_directory, "train.txt")))
  obj_data.write("valid = {}\n".format(os.path.join(output_directory, "val.txt")))
  obj_data.write("names = {}\n".format(os.path.join(output_directory, "obj.names")))
  obj_data.close()
  write_file(train_content, train_file, "train")
  write_file(val_content, val_file, "val")
  
  
def write_file(file_content, file, name):
  for content in tqdm(file_content, total=len(file_content), desc="Writting {} file".format(name)):
    file.write(content)
    file.write("\n")
  file.close()

def copy_files(data_split, split_destination_file):
  """Save split file to new directory"""
  for idx, row in tqdm(data_split.iterrows(), total=data_split.shape[0], 
                       desc="Copying file with the new layout"):
    # Copying txt
    shutil.copy(src=row.paths, 
                dst=os.path.join(split_destination_file, row.out_name))
    # Copying jpg
    shutil.copy(src=row.paths.replace("txt", "jpg"), 
                dst=os.path.join(split_destination_file, row.out_name.replace("txt", "jpg")))

def upload_directory_s3(local_directory, bucket, destination):
  for root_, dirs, files in os.walk(local_directory):
    for filename in files:
      # construct the full local path
      local_path = os.path.join(root_, filename)
      # construct the full Dropbox path
      relative_path = os.path.relpath(local_path, local_directory)
      s3_path = os.path.join(destination, relative_path)
      # logger paths
      logger.info("Relative path : {} Local Path : ".format(relative_path, local_path))
      # relative_path = os.path.relpath(os.path.join(root_, filename))
      logger.info("Searching %s in %s" % (s3_path, bucket))
      logger.info("Uploading %s..." % s3_path)
      client.upload_file(local_path, bucket, s3_path)

if __name__ == "__main__":
  parser = argparse.ArgumentParser(description="Preprocess images by deleting images without label and"
      " Creating an split train/val dataset for training and upload to s3 bucket")

  parser.add_argument("--train-size","-tz", default=0.70, help="training size number", type=float)
  parser.add_argument("--clean", "-c", action="store_true", help="if you want to clean the dataset") 
  parser.add_argument("--split", "-s", action="store_true", help="if you want to split dataset")
  parser.add_argument("--upload", "-u", action="store_true", help="if you want to upload dataset")
  parser.add_argument("--directory-name", "-d", default="cvat_data", help="relative path where the data is located"
      " It must be a son of the parent directory example=data/training",type=str)
  parser.add_argument("--output-directory", "-od", default="training", help="this is where the clean and split data will be save"
      " in order to upload to s3 bucket", type=str)
  parser.add_argument("-change-path","-cp", action="store_true", help="if you want to change dataset_path only")
  parser.add_argument("--bucket-name", "-bn", default="sagemaker-us-west-2-256305374409",
      help="bucket name where we are going to save the data", type=str)
  parser.add_argument("--key-name", "-kn", default="TiendaApp/training", help="Key name where you want to save"
      " the data in s3 example: TiendaApp/data", type=str)

  args = parser.parse_args()
  
  # See the variables
  logger.info("vars: \n{}".format(pretty_json(vars(args))))
  # Logger the root 
  logger.info(root)
  
  if args.clean:
    contents = clean_dataset(os.path.join(root, args.directory_name), True)
  else:
    pass
    #contents = clean_dataset(os.path.join(root, args.directory_name), False)


  if args.split:
    data = []
    for path, values in tqdm(contents, desc="Getting classes", total=len(contents)):
      class_ = list(set([int(val.split(" ")[0]) for val in values]))[0]
      file_name = path.split("/")[-1]
      data.append([path, class_, file_name])

    data = pd.DataFrame(data, columns=["paths", "classes", "out_name"])
    data.to_csv(os.path.join(root, args.directory_name, "data.csv"), index=False)
    output_path = os.path.join(root, args.output_directory)
    training_path = os.path.join(output_path, "training")
    validating_path = os.path.join(output_path, "validating")
    logger.info("Save clean and splits dataset to {}".format(output_path))
    make_all_dirs(output_path,
                  training_path,
                  validating_path)
    
    logger.info("Splitting...")
    data_train, data_val = train_test_split(data, train_size=args.train_size, stratify=data.classes)
    data_train.to_csv(os.path.join(root, args.directory_name, "data_train.csv"), index=False)
    data_val.to_csv(os.path.join(root, args.directory_name, "data_val.csv"), index=False)
    copy_files(data_train, training_path)
    copy_files(data_val, validating_path)
    # Copying obj.names
    shutil.copy(os.path.join(root, args.directory_name, "obj.names"),
                os.path.join(root, args.output_directory, "obj.names"))
    generating_txt(root, training_path, validating_path, args.output_directory)

  if args.change_path:
    os.rename(os.path.join(root, args.directory_name),os.path.join(root, args.output_directory))
    training_path = os.path.join(root, args.output_directory, "training")
    validating_path = os.path.join(root, args.output_directory, "validating")
    generating_txt(root, training_path, validating_path, args.output_directory)
  
  if args.upload:
    upload_directory_s3(local_directory=os.path.join(root, args.output_directory),
                        bucket=args.bucket_name,
                        destination=args.key_name)
