#!/bin/bash

pip install --upgrade pip
pip install -r requirements.dev.txt
python manage.py migrate