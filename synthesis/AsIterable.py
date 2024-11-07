from typing import Generator, TypeVar, Callable


T = TypeVar("T")


class AsIterable:
    """
    A wrapper for generator functions that turns them into iterables.

    You can use it with generator functions like this:
    >>> def foo():
    ...     yield 1
    ...     yield 2
    ...
    >>> iterable_foo = AsIterable(foo)
    >>> for x in iterable_foo:
    ...     print(x)

    The 'iterable_foo' can now be re-iterated indefinitely.
    (whereas the generator returned by the foo function can only
    be iterated once)

    You can also pass in lambda generators:
    >>> foo = AsIterable(lambda: (yield from range(10)))
    """

    def __init__(
        self,
        generator_factory: Callable[[], Generator[T, None, None]]
    ):
        self.generator_factory = generator_factory
    
    def __iter__(self) -> Generator[T, None, None]:
        return self.generator_factory()
    
    def __call__(self) -> Generator[T, None, None]:
        return self.generator_factory()
