#!/usr/bin/env bash

set -o errexit  # exit on error

pip install -r requirements.txt

git clone https://github.com/KatarinaPopikova/yolov7.git

cd yolov7

pip install -r requirements.txt

cd ..

git clone https://github.com/KatarinaPopikova/ultralytics.git

cd ultralytics

pip install -r requirements.txt

cd ..

python manage.py collectstatic --no-input
python manage.py migrate