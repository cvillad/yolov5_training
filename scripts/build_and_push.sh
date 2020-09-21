·!/bin/bash
echo "ECR Login"
aws ecr get-login-password --region us-west-2 | docker login --username AWS --password-stdin 430127992102.dkr.ecr.us-west-2.amazonaws.com

echo "Building image"
docker build --rm -t train .

docker tag train:latest 430127992102.dkr.ecr.us-west-2.amazonaws.com/yolov5_train:latest

echo "Pushing to ECR"
docker push 430127992102.dkr.ecr.us-west-2.amazonaws.com/yolov5_train:latest
