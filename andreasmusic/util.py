import multiprocessing
import cPickle
import tempfile
import os
from contextlib import contextmanager

CACHE_DIR = os.path.expanduser('~/.cache/andreasmusic')

@contextmanager
def temporary_filename(suffix=''):
    f, filename = tempfile.mkstemp(suffix=suffix)
    os.unlink(filename)
    os.close(f)
    try:
        yield filename
    finally:
        os.unlink(filename)

def lazy_parallel(obj, inputs, n_workers):
    pool = multiprocessing.Pool(processes=n_workers)
    return pool.imap(obj, inputs)

class Cached(object):

    def run_cached(self, x):
        cache_filename = self.cache_key(x)
        if not os.path.exists(CACHE_DIR):
            os.path.makedirs(CACHE_DIR)
        cache_path = os.path.join(CACHE_DIR, cache_filename)
        if os.path.exists(cache_path):
            with open(cache_path) as f:
                result = cPickle.load(f)
        else:
            result = self.run(x)
            with open(cache_path, 'w') as f:
                cPickle.dump(result, f, protocol=cPickle.HIGHEST_PROTOCOL)
        return result

    def run(self, x):
        raise NotImplementedError()

    def cache_key(self, x):
        raise NotImplementedError()

    def __call__(self, x):
        return self.run_cached(x)
