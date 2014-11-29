# report.py: Downloads a renewable energy report from California ISO and parses
# it.

import urllib2
import re

DAILY_RENEWABLES_TXT_TEMPLATE_ = "http://content.caiso.com/green/renewrpt/%02d%02d%02d_DailyRenewablesWatch.txt"

def downloadDailyTXT(year, month, day):
    url = DAILY_RENEWABLES_TXT_TEMPLATE_ % (year, month, day)
    return urllib2.urlopen(url).read()

class HourlyAverageOutput(object):
    def __init__(self, date, hour, types, outputs):
        self.date_ = date
        self.hour_ = hour
        self.types_ = types
        self.outputs_ = outputs

    def OutputForType(self, t):
        return self.outputs_[self.types_.index(t)]

class Report(object):
    def __init__(self, renewablesHourly, overallHourly):
        self.renewablesHourly_ = renewablesHourly
        self.overallHourly_ = overallHourly

    def PrintForDebugging(self):
        def pr(arr):
            for x in arr:
                print "%s %s %s %s" % (x.date_, x.hour_, x.types_, x.outputs_)
        print "Renewables hourly:"
        pr(self.renewablesHourly_)
        print "Overall hourly:"
        pr(self.overallHourly_)


def parseTypesAndOutputs(date, lines):
    types = re.split('\t+', lines[0].rstrip())[2:]
    for outputLine in lines[1:25]:
        cells = re.split('\t+', outputLine.rstrip())
        hour = int(cells[1])
        outputs = [int(mw) for mw in cells[2:]]
        yield HourlyAverageOutput(date, hour, types, outputs)

def parseDailyTXT(txt):
    lines = re.split('\r\n', txt)
    if len(lines) != 55:
        raise Exception("expected 55 lines, got %d" % len(lines))
    date = lines[0].split('\t')[0]
    return Report([x for x in parseTypesAndOutputs(date, lines[1:1+25])],
                  [x for x in parseTypesAndOutputs(date, lines[29:29+25])])

def example():
    src = "SOLAR PV"  # "WIND TOTAL"
    for day in xrange(1, 32):
        report = parseDailyTXT(downloadDailyTXT(2014, 10, day))
        print "%s output on 10/%02d: %s" % (
            src,
            day,
            " ".join(['{:>5}'.format(str(row.OutputForType(src)))
                      for row in report.renewablesHourly_]))

example()
