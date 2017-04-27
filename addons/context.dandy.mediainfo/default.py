# -*- coding: utf-8 -*-
# Writer (c) 2017, dandy
# Rev. 1.0.0
# Licence: GPL v.3: http://www.gnu.org/copyleft/gpl.html

import xbmc
import re

def get_media_title():
    title = xbmc.getInfoLabel("ListItem.Title")
    return title.split('[')[0].split('(')[0].split('/')[0].strip()

def get_media_meta_year():
    title = xbmc.getInfoLabel("ListItem.Title")
    pattern = r"[([]([12][90]\d\d)[])]"
    match = re.search(pattern, title)
    return match.group(1) if match else ""

def main():
    xbmc.executebuiltin("RunScript(script.extendedinfo,info=extendedinfo,name=%s,year=%s,dbid=%s,id=%s)" % (get_media_title(), get_media_meta_year(), xbmc.getInfoLabel("ListItem.DBID"), xbmc.getInfoLabel("ListItem.Property(id)")))

if __name__ == '__main__':
    main()
