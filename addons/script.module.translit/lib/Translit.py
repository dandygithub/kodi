#!/usr/bin/python
# Writer (c) 2012-2017, MrStealth, dandy
# Rev. 2.1.0
# License: GPLv3

import os, sys, json
import xbmc, xbmcaddon, xbmcvfs
import importlib

#importlib.reload(sys)
#sys.setdefaultencoding("UTF8")

class Translit():
    def __init__(self, encoding='utf-8'):
        self.version = "2.1.0"
        self.plugin = "Translit" + self.version

        self.id = 'script.module.translit'
        self.addon = xbmcaddon.Addon(self.id)
        self.icon = self.addon.getAddonInfo('icon')
        self.path = xbmcvfs.translatePath(self.addon.getAddonInfo('path'))
        self.resource = xbmcvfs.translatePath(os.path.join(self.path, 'lib'))

        self.encoding = encoding
        self.transtable = self.getTranstable()

        sys.path.append(self.path)


    def getTranstable(self):
        try:
            file_path = os.path.join(self.resource, "transtable.json" )
            json_tuple = open(file_path).read()

            try:
              transtable = json.loads(json_tuple)
              return transtable
            except Exception as e:
              print(e)
              return ()

        except IOError as e:
            print(e)
            return ()

    def rus(self, in_string):
        russian = str(in_string)
        for symb_out, symb_in in self.transtable:
          russian = russian.replace(symb_in, symb_out)
        return russian

    def eng(self, in_string):
        translit = str(in_string)
        for symb_out, symb_in in self.transtable:
          translit = translit.replace(symb_out, symb_in)
        return translit
