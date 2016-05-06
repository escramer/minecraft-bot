"""Module for the singleton decorator"""

def singleton(func_or_class):
    """
    Decorator for the Singleton pattern for functions or classes
    Example uses:
        @singleton
        def foo(x, y):
            # Your code here
        @singleton
        class A:
            def __init__(self, x, y):
                # Your code here
            # Rest of your code
        x = foo(3, 4)
        a = A(5, 6)
    """

    val = []
    def rtn(*args, **kwargs):
        """Return the value if already computed."""
        if not val:
            val.append(func_or_class(*args, **kwargs))
        return val[0]
    return rtn
