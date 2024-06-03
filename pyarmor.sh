#!/bin/bash

find . -name "*.pyc" -delete -o -type d -name "__pycache__" -exec rm -r {} +

mkdir -p dist
rm -rf dist/*
mkdir -p dist/data/json


cp -r class dist/
cp -r data/json/type.json dist/data/json/
cp -r data/sql dist/data/
cp -r data/tpl dist/data/
cp -r data/vip dist/data/
cp data/control.conf dist/data/
cp data/plugin_* dist/data/
cp data/plugins.json dist/data/
cp data/recycle_bin.pl dist/data/
cp -r geneva dist/
cp -r rewrite dist/
cp -r route dist/
cp -r scripts dist/
cp -r ssl dist/
cp -r tools dist/
cp -r version dist/
cp app.py dist/
cp clear.sh dist/
cp cli.sh dist/
cp requirements.txt dist/
cp setting.py dist/
cp speed_check.py dist/
cp task.py dist/
cp tools.py dist/

pyarmor gen -r class
pyarmor gen -r route
pyarmor gen -r scripts
pyarmor gen -r version
pyarmor gen app.py
pyarmor gen setting.py
pyarmor gen speed_check.py
pyarmor gen task.py
pyarmor gen tools.py