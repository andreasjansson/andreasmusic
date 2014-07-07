import multiprocessing
import cPickle
import tempfile
import simplejson as json
import os
from contextlib import contextmanager
import hashlib

@contextmanager
def temporary_filename(suffix=''):
    filename = get_temporary_filename(suffix)
    try:
        yield filename
    finally:
        os.unlink(filename)

def get_temporary_filename(suffix=''):
    f, filename = tempfile.mkstemp(suffix=suffix)
    os.unlink(filename)
    os.close(f)
    return filename

def lazy_parallel(obj, inputs, n_workers):
    pool = multiprocessing.Pool(processes=n_workers)
    return pool.imap(obj, inputs)

class Cached(object):

    def run_cached(self, x):
        cache_path = self.cache_path(x)
        cache_dir = os.path.dirname(cache_path)
        if not os.path.exists(cache_dir):
            os.makedirs(cache_dir)

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

    def cache_path(self, x):
        raise NotImplementedError()

    def __call__(self, x):
        return self.run_cached(x)


def cached(filename, fmt='json'):
    assert fmt in ('json', 'pickle')

    filename = os.path.expanduser(filename)

    def decorator(fn):

        def wrapper(*args, **kwargs):

            m = hashlib.md5()
            m.update(json.dumps([args, kwargs]))
            fname = filename % {'args_md5': m.hexdigest()}

            if os.path.exists(fname):
                with open(fname) as f:
                    if fmt == 'json':
                        return json.load(f)
                    elif fmt == 'pickle':
                        return cPickle.load(f)

            ret = fn(*args, **kwargs)

            with open(fname, 'w') as f:
                if fmt == 'json':
                    json.dump(ret, f)
                elif fmt == 'pickle':
                    cPickle.dump(ret, f)

            return ret

        return wrapper

    return decorator
