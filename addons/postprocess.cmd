@echo off
echo y | del addons.xml.md5
C:\Python27\python.exe postprocess.py
