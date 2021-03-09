@echo off
echo y | del addons.xml.md5
python.exe xml_generator.py -a addons -x addons/addons.xml
