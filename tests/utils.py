import inspect
from typing import Type, TypeVar

T = TypeVar("T")


def instantiate_assert_all_args_provided(
    cls: Type[T], kwargs: dict, arguments_to_ignore: set | None = None
) -> T:
    """
    Assert that the kwargs are covering all the expected arguments by the class,
    event if they have a default value

    :param cls: class to be instantiated by the kwargs
    :type cls: Type
    :param kwargs: kwargs to instantiate the class
    :type kwargs: dict
    :param arguments_to_ignore: arguments to ignore if missing, defaults to None
    :type arguments_to_ignore: None
    :return: _description_
    :rtype: _type_
    """
    if arguments_to_ignore is None:
        arguments_to_ignore = set()
    # Get the signature of the __init__ method
    sig = inspect.signature(cls.__init__)

    # Exclude 'self' from parameters
    expected_params = [param for param in sig.parameters.keys() if param != "self"]

    # Get the provided kwargs keys
    provided_params = set(kwargs.keys())

    # Check if all expected parameters are in the provided kwargs
    missing_params = set(expected_params) - provided_params - arguments_to_ignore

    if missing_params:
        raise ValueError(
            f"Missing parameters: {missing_params} for class {cls.__name__}"
        )
    return cls(**kwargs)
