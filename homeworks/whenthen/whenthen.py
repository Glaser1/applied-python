class WhenThen:
    def __init__(self, base_func):
        self.base_func = base_func
        self.conditions = []
        self.last_condition = None

    def when(self, func):
        if self.last_condition is not None:
            raise RuntimeError("Every new @then must follow @when")

        self.last_condition = func
        return self

    def then(self, func):
        if self.last_condition is None:
            raise RuntimeError("Every new @then must follow @when")

        self.conditions.append((self.last_condition, func))
        self.last_condition = None
        return self

    def __call__(self, *args, **kwargs):
        if self.last_condition is not None:
            raise RuntimeError("Every new @then must follow @when")

        for condition, call in self.conditions:
            if condition(*args, **kwargs):
                return call(*args, **kwargs)

        return self.base_func(*args, **kwargs)


def whenthen(func):
    return WhenThen(func)


@whenthen
def factorial(x):
    return x * factorial(x - 1)


@factorial.when
def factorial(x):
    return x == 0


@factorial.then
def factorial(x):
    return 1


@factorial.when
def factorial(x):
    return x > 5


@factorial.then
def factorial(x):
    return x * (x - 1) * (x - 2) * (x - 3) * (x - 4) * factorial(x - 5)


print(factorial(6))
