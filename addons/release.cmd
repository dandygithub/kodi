@echo off
echo y | del addons.xml.md5
python.exe postprocess.py
python.exe release.py
