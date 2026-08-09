"""Decimal formatter algorithm module."""


def baoliuxiaoshu(value, digits):
    digits = int(digits)
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return ("{:." + str(digits) + "f}").format(value)
    if isinstance(value, dict):
        items = []
        for item_key, item_value in value.items():
            items.append("{}:{}".format(item_key, baoliuxiaoshu(item_value, digits)))
        return "{" + ", ".join(items) + "}"
    if isinstance(value, (list, tuple)):
        return "[" + ", ".join(baoliuxiaoshu(item, digits) for item in value) + "]"
    return str(value)
