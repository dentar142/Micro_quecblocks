"""裁判和示例共用的固定格式报告器。"""

PASS = "PASS"
FAIL = "FAIL"
SKIP = "SKIP"
_VALID = (PASS, FAIL, SKIP)


class Reporter:
    def __init__(self, display=None, printer=print):
        self.display = display
        self.printer = printer
        self.results = []

    def record(self, name, status, detail=""):
        if status not in _VALID:
            raise ValueError("invalid status: {}".format(status))
        detail = str(detail).strip()
        line = "[TEST][{}][{}]".format(name, status)
        if detail:
            line += " " + detail
        self.results.append((name, status, detail))
        self.printer(line)
        if self.display:
            self.display.show_test(name, status, detail)
        return status

    def passed(self, name, detail=""):
        return self.record(name, PASS, detail)

    def failed(self, name, detail=""):
        return self.record(name, FAIL, detail)

    def skipped(self, name, detail=""):
        return self.record(name, SKIP, detail)

    def counts(self):
        counts = {PASS: 0, FAIL: 0, SKIP: 0}
        for _, status, _ in self.results:
            counts[status] += 1
        return counts

    def summary(self):
        counts = self.counts()
        line = "[SUMMARY] PASS={} FAIL={} SKIP={}".format(
            counts[PASS], counts[FAIL], counts[SKIP]
        )
        self.printer(line)
        if self.display:
            self.display.show_summary(counts)
        return counts

