"""Small number-list algorithms for competition questions."""


def _numbers(values):
    if values is None:
        return []
    if isinstance(values, str):
        raw = values.replace("，", ",").replace("；", ",").replace(";", ",").split(",")
        values = []
        for item in raw:
            item = item.strip()
            if item:
                values.append(item)
    result = []
    for item in values:
        try:
            result.append(float(item))
        except Exception:
            pass
    return result


def shuzipaixu(values, reverse=False):
    return sorted(_numbers(values), reverse=bool(reverse))


def zuidazhi(values):
    nums = _numbers(values)
    return max(nums) if nums else None


def zuixiao(values):
    nums = _numbers(values)
    return min(nums) if nums else None


def pingjunzhi(values):
    nums = _numbers(values)
    return sum(nums) / len(nums) if nums else None
