from random import random


def should_fail(rate: float) -> bool:
    return random() < rate
