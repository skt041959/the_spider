# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html


import os
import json
import csv
from scrapy.exceptions import DropItem
from readsetting import ReadSetting
from GlobalLogging import GlobalLogging


class SavePipeline(object): #下载所有item对应的网页

    def __init__(self):
        rs = ReadSetting()
        self.savename = rs.savingname()
        self.location = rs.savinglocation()
        self.savingformat = rs.savingformat()
        self.projectname = rs.projectname()
        self.index = 0 #成功下载页面数

    def process_item(self, item, spider):
        try:
            self.index += 1
            if self.savename == 1:
                path = os.path.normcase("%s/%s.%s" % (self.location, self.index, self.savingformat))
            elif self.savename == 2:
                path = os.path.normcase("%s/%s.%s" % (self.location, self.projectname+"+{0}".format(self.index), self.savingformat))
            elif self.savename == 3:
                number = 0
                path = os.path.normcase("%s/%s.%s" % (self.location, item['title'], self.savingformat))
                while os.path.exists(path):
                    number = number + 1
                    filename = item['title'] + "({0})".format(number)
                    path = os.path.normcase("%s/%s.%s" % (self.location, filename, self.savingformat))

            with open(path, "w") as downpage:
                downpage.write(item['body'])

            GlobalLogging.getInstance().info(u"[success] downloaded {0}\n         url: {1}".format(item['title'], item['url']))
            GlobalLogging.getInstance().info("[stats] downloaditem : {0}".format(self.index))
        except KeyError:
            GlobalLogging.getInstance().error(u"[fail] download\n         url: {0}".format(item['url']))

        return item


class StatisticsPipeline(object):

    def __init__(self):
        print('+StatisticsPipeline')

    def process_item(self, item, spider):

        if spider.linkmatrix.addLink(item['url'], item['referer']):
            #print ("Duplicate item found: %s" % item)
            raise DropItem("Duplicate item found: %s" % item)
        else:
            return item

