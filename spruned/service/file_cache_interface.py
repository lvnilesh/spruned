import os
import pickle
import shutil
from spruned.service.abstract import CacheInterface


class FileCacheInterface(CacheInterface):
    def __init__(self, directory, cache_limit=None):
        self.directory = directory
        if not os.path.exists(directory):
            os.makedirs(directory)
        if cache_limit:
            raise NotImplementedError

    def set(self, *a, ttl=None):
        if ttl:
            raise NotImplementedError
        args = list(a)[:-1]
        prefix = a[1].lstrip('0')[:2] + '/'
        if not os.path.exists(self.directory + prefix):
            os.makedirs(self.directory + prefix)
        file = self.directory + prefix + '.'.join(args) + '.bin'
        with open(file, 'wb') as pointer:
            pickle.dump(a[-1], pointer)

    def get(self, *a):
        prefix = a[1].lstrip('0')[:2] + '/'
        file = self.directory + prefix + '.'.join(a) + '.bin'
        try:
            with open(file, 'rb') as pointer:
                res = pickle.load(pointer)
        except FileNotFoundError:
            return None
        return res

    def remove(self, *a, may_fail=True):
        prefix = a[1].lstrip('0')[:2] + '/'
        file = self.directory + prefix + '.'.join(a) + '.bin'
        try:
            os.remove(file)
        except OSError:
            raise OSError

    def purge(self):
        folder = self.directory
        for the_file in os.listdir(folder):
            file_path = os.path.join(folder, the_file)
            try:
                if os.path.isfile(file_path):
                    os.unlink(file_path)
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
            except Exception as e:
                print(e)
