#!/usr/bin/env bash

set -o errexit  # exit on error

git clone https://github.com/KatarinaPopikova/yolov7.git

cd yolov7

pip install -r requirements.txt

cd ..

pip install -r requirements.txt

python manage.py collectstatic --no-input
python manage.py migrate