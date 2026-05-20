from datetime import datetime as dt
from functools import wraps
from inspect import isclass, isfunction


def new_method(method):
    method_name = method.__name__
    @wraps(method)
    def wrapper(self):
        class_name = self.__class__.__name__
        start_time = dt.now()
        print(f"`{class_name}.{method_name}` started")
        res = method(self)
        print(f"`{class_name}.{method_name}` finished in {(dt.now() - start_time).total_seconds():.2f}s")
        return res

    return wrapper


def profile(obj):
    if isclass(obj):
        for attr_name, attr in obj.__dict__.items():
            if callable(attr):
                setattr(obj, attr_name, new_method(attr))
        return obj

    elif isfunction(obj):
        @wraps(obj)
        def wrapper(*args, **kwargs):
            obj_name = f"`{obj.__name__}`"
            start_time = dt.now()
            print(f"{obj_name} started")
            res = obj(*args, **kwargs)
            print(f"{obj_name} finished in {(dt.now() - start_time).total_seconds():.2f}s")
            return res
        return wrapper



@profile
class Bar:
    def __init__(self):
        pass

    def method_1(self):
        pass

    def method_2(self):
        pass


@profile
def foo():
    pass


foo()
bar = Bar()
bar.method_1()
bar.method_2()
