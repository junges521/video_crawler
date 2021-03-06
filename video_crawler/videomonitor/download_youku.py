#!/usr/bin/env python
# -*- coding: utf-8 -*-
#encoding=utf8

import sys
sys.path.insert(0, '/home/monitor/opt/video_data/')
from resource.http import HTMLResource, JsonResource
from resource.database import DataBase
from resource.util import Util
import os
import threadpool
import datetime
import traceback
from youku import Youku

image_base_path = "/media/image/"
video_base_path = "/media/image/video/"
site = 'youku'
Bad_Datas = []
headers = Youku().get_headers()

def download_video(para):
    _id, sid, date_str = para
    try:
        idstr = str(_id)
        video_path = video_base_path+site+'/'+date_str + '/' + idstr + '.flv'
        jpgdir = image_base_path+site+'/'+date_str + '/' + idstr + '/'
        jpg_path = jpgdir + idstr + '_20.jpg'
        jpg_path1 = jpgdir + idstr + '_5.jpg'
        if not os.path.exists(jpg_path1):
            video_url_cdn = Youku().parse(idstr)
            if not video_url_cdn.startswith('http'):
                code = video_url_cdn
                Bad_Datas.append([idstr, '', code])
                return None
            size = HTMLResource(video_url_cdn, headers=headers).download_video(video_path, 1024*1024*8)
            if size is not None and size > 0:
                # jpgdir = image_base_path+site+'/'+date_str + '/' + idstr + '/'
                returncode = Util.movie_split_image(video_path, jpgdir, idstr)
                if os.path.exists(jpg_path):
                    DataBase.update_data(site, idstr, date_str)
                else:
                    size = HTMLResource(video_url_cdn, headers=headers).download_video(video_path, 1024*1024*20)
                    if size is not None and size > 0:
                        returncode = Util.movie_split_image(video_path, jpgdir, idstr)
                        if os.path.exists(jpg_path):
                            DataBase.update_data(site, idstr, date_str)
                        elif os.path.exists(jpg_path1):
                            DataBase.update_data(site, idstr, date_str, '1')
                        else:
                            print('remove bad jpg dir: ' + jpgdir)
                            for file in os.listdir(jpgdir):
                                os.remove(os.path.join(jpgdir, file))
                            os.removedirs(jpgdir)
                            Bad_Datas.append([idstr, '', '-98'])
            else:
                Bad_Datas.append([idstr, '', '-99'])
            if os.path.exists(video_path):
                os.remove(video_path)
    except Exception as e:
        print e
        traceback.print_exc()
        print _id


def download():
    runday = datetime.date.today()
    exe_time = datetime.datetime.now()
    print runday
    data_list = DataBase.get_new_datas(site)
    count = len(data_list)
    if count > 1000:
        del data_list[1000:]
        count = len(data_list)
    if count >= 20:
        print count
        i = 0

        para_list = data_list
        hour = str(exe_time.hour)
        if len(hour)==1:
            hour = '0' + hour
        date_str = runday.strftime('%Y%m%d') + hour
        print date_str
        videodir = video_base_path+site+'/'+date_str
        jpgdir = image_base_path+site+'/'+date_str
        if not os.path.exists(jpgdir):
            os.makedirs(jpgdir)
        if not os.path.exists(videodir):
            os.makedirs(videodir)

        for para in para_list:
            para[2] = date_str
        pool_size = 8
        pool = threadpool.ThreadPool(pool_size)
        requests = threadpool.makeRequests(download_video, para_list)
        [pool.putRequest(req) for req in requests]
        pool.wait()
        pool.dismissWorkers(pool_size, do_join=True)
        del para_list[0: len(para_list)]
        DataBase.update_datas(site, Bad_Datas)
        del Bad_Datas[0: len(Bad_Datas)]

        Util.delete_empty_dir(jpgdir)
        if os.path.exists(jpgdir):
            DataBase.insert_pathdata(site, image_base_path, date_str)

def download_by_day_hour():
    hour = 10
    runday = datetime.date(2015,12,14)
    oneday = datetime.timedelta(days=1)
    print runday
    data_list, bad_data_list = DataBase.get_datas(site, 'status=0')

    datas = []
    count = len(data_list)
    print len(bad_data_list)
    print count
    for bad_data in bad_data_list:
        datas.append([str(bad_data[0]), '', '-1'])
    DataBase.update_datas(site, datas)
    del datas[0: len(datas)]

    count = len(data_list)
    print count
    para_list = []
    i = 0
    while(i < count):
        para_list.append(data_list[i])
        i += 1
        if i % 500 == 0 or i >= count:
            hour_str = str(hour)
            if len(hour_str) == 1:
                hour_str = '0' + hour_str
            date_str = runday.strftime('%Y%m%d')+hour_str
            print date_str
            videodir = video_base_path+site+'/'+date_str
            jpgdir = image_base_path+site+'/'+date_str
            if not os.path.exists(jpgdir):
                os.makedirs(jpgdir)
            if not os.path.exists(videodir):
                os.makedirs(videodir)
            # _id, sid, date_str
            for para in para_list:
                para[2] = date_str
            pool_size = 8
            pool = threadpool.ThreadPool(pool_size)
            requests = threadpool.makeRequests(download_video, para_list)
            [pool.putRequest(req) for req in requests]
            pool.wait()
            pool.dismissWorkers(pool_size, do_join=True)
            del para_list[0: len(para_list)]
            DataBase.update_datas(site, Bad_Datas)
            del Bad_Datas[0: len(Bad_Datas)]
            Util.delete_empty_dir(jpgdir)
            if os.path.exists(jpgdir):
                if len(os.listdir(jpgdir)) > 500 or i >= count:
                    DataBase.insert_pathdata(site, image_base_path, date_str)
                    hour += 1
            if hour >= 20:
                hour = 10
                runday = runday + oneday

if __name__ == '__main__':
    reload(sys)
    sys.setdefaultencoding('utf8')
    # download()
    download_by_day_hour()