#!/usr/bin/env python
# coding:utf-8


import argparse
import datetime
import gzip
import os
import tarfile
import requests
from requests.auth import HTTPBasicAuth


class CDDAC(object):
    def __init__(self, user, password):
        self.__user = user
        self.__password = password

    def download(self, start, end, mission, filetype, outdir):
        for i in range((end - start).days + 1):
            t = start + datetime.timedelta(days=i)
            self.__download(t, mission, filetype, outdir)

    def __download(self, t, mission, filetype, outdir):
        doy = t.timetuple().tm_yday
        year = t.year
        filename = '{}_{}_{}_{:03d}.tar'.format(mission, filetype, year, doy)
        baseurl = 'http://cdaac-www.cosmic.ucar.edu/cdaac/rest/tarservice/data'
        url = '{}/{}/{}/{}.{:03d}'.format(baseurl,
                                          mission, filetype, year, doy)
        r = requests.get(url, auth=HTTPBasicAuth(self.__user, self.__password))
        if r.ok:
            filepath = os.path.join(outdir, filename)
            with open(filepath, 'wb') as f:
                f.write(r.content)
            with tarfile.open(filepath) as tar:
                def is_within_directory(directory, target):
                    
                    abs_directory = os.path.abspath(directory)
                    abs_target = os.path.abspath(target)
                
                    prefix = os.path.commonprefix([abs_directory, abs_target])
                    
                    return prefix == abs_directory
                
                def safe_extract(tar, path=".", members=None, *, numeric_owner=False):
                
                    for member in tar.getmembers():
                        member_path = os.path.join(path, member.name)
                        if not is_within_directory(path, member_path):
                            raise Exception("Attempted Path Traversal in Tar File")
                
                    tar.extractall(path, members, numeric_owner=numeric_owner) 
                    
                
                safe_extract(tar, outdir)
            ex_dir = os.path.join(outdir, mission, filetype,
                                  '{}.{:03d}'.format(year, doy))
            for f in os.listdir(ex_dir):
                if f.endswith('gz'):
                    zfilepath = os.path.join(ex_dir, f)
                    with gzip.open(zfilepath) as gz:
                        with open(zfilepath[:-3], 'wb') as fw:
                            fw.write(gz.read())


def valid_date(s):
    try:
        return datetime.datetime.strptime(s, '%Y%m%d')
    except ValueError:
        raise argparse.ArgumentTypeError('Not a valid date: {}'.format(s))


def valid_mission(s):
    missions = ['cosmic2013', 'cosmic', 'cosmicrt',
                'grace',
                'champ2016',
                'gpsmet',
                'sacc', 'saccrt',
                'cnofs', 'cnofsrt',
                'gpsmetas',
                'kompsat5rt',
                'metopa2016', 'metopa',
                'metopb2016', 'metopb',
                'tsx'
                ]
    if s in missions:
        return s
    else:
        raise argparse.ArgumentTypeError('Not a valid mission: {}\n {}'.format(
            s, ' '.join(missions)))


def valid_type(s):
    types = ['opnGps', 'podCrx', 'leoOrb',
             'leoClk', 'leoAtt', 'comClk',
             'atmPhs', 'gpsBit', 'atmPrf',
             'wetPrf', 'bfrPrf', 'sonPrf',
             'ecmPrf', 'echPrf', 'eraPrf',
             'gfsPrf', 'mmcGrd', 'podTec',
             'ionPhs', 'ionPhs', 'ionPrf',
             'tipLv1', 'scnLv1']
    if s in types:
        return s
    else:
        raise argparse.ArgumentTypeError('Not valid file type: {}\n {}'.format(
            s, ' '.join(types)))


def valid_path(s):
    if os.path.isdir(s):
        return s
    else:
        raise argparse.ArgumentTypeError('Not a valid path: {}'.format(s))


if __name__ == '__main__':
    parser = argparse.ArgumentParser('cdaac')
    parser.add_argument('-u', '--user', help='user', type=str, required=True)
    parser.add_argument('-p', '--password', help='password',
                        type=str, required=True)
    parser.add_argument('-s', '--start', help='start date',
                        type=valid_date, required=True)
    parser.add_argument('-e', '--end', help='end date',
                        type=valid_date, required=True)
    parser.add_argument('-m', '--mission', help='mission',
                        type=valid_mission, required=True)
    parser.add_argument('-t', '--type', help='file type',
                        type=valid_type, required=True)
    parser.add_argument('-o', '--out', help='out dir',
                        type=valid_path, required=True)
    args = parser.parse_args()
    cddac = CDDAC(args.user, args.password)
    cddac.download(args.start, args.end, args.mission, args.type, args.out)
