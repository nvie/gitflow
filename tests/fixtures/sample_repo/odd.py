def odd(n):
    if n <= 0:
        return False
    return not odd(n-1)
