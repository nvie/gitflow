def odd(n):
    """Tells is a number is odd."""
    if n <= 0:
        return False
    return not odd(n-1)
