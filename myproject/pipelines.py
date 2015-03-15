# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html


import os, json, csv
from scrapy.exceptions import DropItem

from readsetting import ReadSetting
from GlobalLogging import GlobalLogging
from myproject.items import CrawledItem, PassItem


class SavePipeline(object): #下载符合抓取下载条件的网页

    def __init__(self):
        print('+SavePipeline')
        rs = ReadSetting() #读取setting文件中的保存参数
        self.savename = rs.savingname()
        self.location = rs.savinglocation()
        self.saveingformat = rs.savingformat()

        if self.savename == 1: #判断函数self.getpath对应的函数变量(相当于函数指针)
            self.getpath = self.getpath_1
        elif self.savename == 2:
            self.getpath = self.getpath_2
        elif self.savename == 3:
            self.getpath = self.getpath_3

        self.projectname = rs.projectname()

        try:
            os.mkdir(self.location) #创建下载内容所保存的文件夹(根据保存参数)
        except OSError as e:
            if e.errno == 17: pass


    #关于可变参数的说明: *args表示任何多个无名参数,为tuple即(); **kwargs表示关键字参数,为dict即{}
    #同时使用*args和**kwargs时,*args参数必须要列在**kwargs之前
    #此三个函数需要的参数数目不一致,为统一函数变量的形式而采用**kwargs

    #此三个函数返回标准化的路径名称:在不区分大小写的文件系统上,把路径转换为小写字母; 在Windows上,把正斜杠转换为反斜杠

    def getpath_1(self, **kwargs): #文件的命名方式为"顺序数字"
        return os.path.normcase(u"{0}/{1}.{2}".format(self.location, self.index, self.saveingformat))

    def getpath_2(self, **kwargs): #文件的命名方式为"项目+顺序数字"
        return os.path.normcase(u"{0}/{1}+{2}.{3}".format(self.location, self.projectname, self.index, self.saveingformat))

    def getpath_3(self, **kwargs): #文件的命名方式为"Html:Title"; 若重名,则在结尾添加"(数字)"以区分
        number = 0
        title = kwargs['title']
        path = os.path.normcase(u"{0}/{1}.{2}".format(self.location, title, self.saveingformat))
        while os.path.exists(path): #若重名,则在结尾添加"(数字)"以区分
            number += 1
            filename = u"{0} ({0})".format(title, number)
            path = os.path.normcase(u"{0}/{1}.{2}".format(self.location, filename, self.saveingformat))
        return path

    def open_spider(self, spider): #启动spider进程时,自动调用该函数,初始化页面计数器
        print("+SavePipeline opened spider")
        self.index = 0 #记录符合下载条件的页面数
        self.page_count = dict() #符合下载条件的页面及其对应编号的字典对象
        self.success = 0 #记录成功下载的条目数

    def close_spider(self, spider): #结束spider时,自动调用该函数,传递符合下载条件的页面及其对应编号的字典对象
        spider.linkmatrix.setIndexMap(self.page_count)

    def process_item(self, item, spider): #下载保存(抓取下载范围内的)页面
        try: #try部分: 报错前的程序不回滚,即前两个计数器始终执行+1; 报错后的程序不执行
            self.index += 1
            self.page_count.setdefault(item['url'], self.index)
            GlobalLogging.getInstance().info("[stats] scrapeditem : {0}".format(self.index))

            with open(self.getpath(title = item['title']), "w") as downpage:
                downpage.write(item['body'])

            self.success += 1

            GlobalLogging.getInstance().info(u"[success] downloaded {0}\n         url: {1}".format(item['title'], item['url']))
            GlobalLogging.getInstance().info("[stats] downloaditem : {0}".format(self.success))
        except KeyError:
            GlobalLogging.getInstance().error(u"[fail] download\n         url: {0}".format(item['url']))
        except IOError as e:
            GlobalLogging.getInstance().info(u"[fail] download, {1}: {2}\n         url: {0}".format(item['url'], e.strerror, e.filename))

        return item


class StatisticsPipeline(object): #对爬取到的页面进行分类统计

    def __init__(self):
        print('+StatisticsPipeline')
        rs = ReadSetting() #读取setting文件中的保存参数
        self.pagecount_max = rs.pagenumber() #读取“最大爬取页面数”
        self.itemcount_max = rs.itemnumber() #读取“最大抓取条目数”
        self.pagecount = 0 #设置“爬取页面数”的计数器
        self.itemcount = 0 #设置“抓取下载条目数”的计数器

        #self.page_seen = set()
        #self.item_seen = set()

    def process_item(self, item, spider): #对爬取到的页面进行分类统计,其中的CrawledItem传给SavePipeline类进行下载

        if isinstance(item, PassItem): #若页面是PassItem
            #url = item['url'].strip('/')
            if self.pagecount == self.pagecount_max:
                GlobalLogging.getInstance().info("[stats] reach max pagecount : {0}".format(self.pagecount))

            if not spider.linkmatrix.addentirelink(item['url'], item['referer']): #记录到entire_struct字典对象中
                self.pagecount += 1
                #self.page_seen.add(url)

            raise DropItem("PassItem: %s" % item['url']) #丢弃该item

        elif isinstance(item, CrawledItem): #若页面是CrawledItem
            #url = CrawledItem['url'].strip('/')

            if self.itemcount == self.itemcount_max:
                GlobalLogging.getInstance().info("[stats] reach max itemcount : {0}".format(self.itemcount))

            if not spider.linkmatrix.addforwardlink(item['url'], item['referer']): #若该item已记录,即重复
                #print ("Duplicate item found: %s" % item)
                #self.item_seen.add(url)
                self.itemcount += 1
                return item
            else: #若该item未记录,即新生成的
                raise DropItem("Duplicate item found: %s" % item['url'])

