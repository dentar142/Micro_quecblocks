"""赛前固件能力预检。"""


def check_modules(names):
    result = {}
    for name in names:
        try:
            __import__(name)
            result[name] = True
        except Exception as exc:
            result[name] = str(exc)
    return result


def missing_modules(names):
    result = check_modules(names)
    return [name for name, ok in result.items() if ok is not True]
