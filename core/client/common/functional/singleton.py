class Singleton(type):
    _instances = {}

    def _hash_key(cls, *args, **kwargs) -> str:
        """
        Generates a consistent hash key for the given class instance. This function constructs
        a string representation of the arguments and returns it in a specified format.

        Args:
            *args: Positional arguments to be included in the hash key.
            **kwargs: Keyword arguments to be included in the hash key.

        Returns:
            str: The calculated hash key in the format `ClassName(arg1, arg2, ..., kwarg1=value1, ...)`.
        """
        positional = [str(v) for v in args]
        keyword = [f"{k}={v}" for k, v in sorted(kwargs.items(), key=lambda x: x[0])]
        arg = ', '.join(positional + keyword)
        return f"{cls.__name__}({arg})"

    def __call__(cls, *args, **kwargs):
        _hash = cls._hash_key(*args, **kwargs)
        if _hash not in cls._instances:
            cls._instances[_hash] = super(Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[_hash]
