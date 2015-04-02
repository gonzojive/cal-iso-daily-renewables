# report.py: Downloads a renewable energy report from California ISO and parses
# it.

import datetime
import urllib2
import re

#DAILY_RENEWABLES_TXT_TEMPLATE_ = "http://content.caiso.com/green/renewrpt/%02d%02d%02d_DailyRenewablesWatch.txt"
DAILY_RENEWABLES_TXT_TEMPLATE_ = "http://localhost:8000/%02d%02d%02d_DailyRenewablesWatch.txt"

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

    def Total(self):
        total = 0
        for x in self.outputs_:
            if x == None:
                continue
            total += x
        return total

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

def parseOutputValue(value):
    if value == "#REF!":
        #raise ValueError("value not float: %s" % value)
        return None
    if value == "[-11059] No Good Data For Calculation":
        #raise ValueError("value not float: %s" % value)
        return None
    return float(value)

def parseTypesAndOutputs(date, lines):
    types = re.split('\t+', lines[0].rstrip())[2:]
    for outputLine in lines[1:25]:
        cells = re.split('\t+', outputLine.rstrip())
        hour = int(float((cells[1])))
        outputs = [parseOutputValue(mw) for mw in cells[2:]]
        yield HourlyAverageOutput(date, hour, types, outputs)

def parseDailyTXT(txt):
    lines = re.split('\r\n|\n', txt)
    if len(lines) != 55:
        raise Exception("expected 55 lines, got %d" % len(lines))
    date = lines[0].split('\t')[0]
    return Report([x for x in parseTypesAndOutputs(date, lines[1:1+25])],
                  [x for x in parseTypesAndOutputs(date, lines[29:29+25])])


START="2013/04/15"
END="2014/12/01"
DATEFORMAT="%Y/%m/%d"

def daterange(s, e):
    for i in range((e - s).days):
        yield s + datetime.timedelta(i)

def csvexample():
    print "Time,Wind,Solar,Wind+Solar,Total"
    for d in daterange(datetime.datetime.strptime(START, DATEFORMAT),
                       datetime.datetime.strptime(END, DATEFORMAT)):
        report = None
        try:
            report = parseDailyTXT(downloadDailyTXT(d.year, d.month, d.day))
        except urllib2.HTTPError:
            continue
        for n in xrange(0, 24):
            t = d + datetime.timedelta(hours=n)
            solar = report.renewablesHourly_[n].OutputForType("SOLAR PV")
            wind = report.renewablesHourly_[n].OutputForType("WIND TOTAL")
            print "%s,%s,%s,%s,%s" % (
                str(t),
                str(wind),
                str(solar),
                str(wind+solar),
                str(report.overallHourly_[n].Total()))

def rollingMean(numbers, windowSize):
    def gen():
        total = 0
        for i in xrange(0, len(numbers)):
            total += numbers[i]
            if i - windowSize >= 0:
                total -= numbers[i - windowSize]
            if i + 1 < windowSize:
                yield None
            else:
                yield total / windowSize
    return [x for x in gen()]

def graph():
    print "Time,Wind,Solar,Wind+Solar,Total"
    def data():
        for d in daterange(datetime.datetime.strptime(START, DATEFORMAT),
                           datetime.datetime.strptime(END, DATEFORMAT)):
            report = None
            try:
                report = parseDailyTXT(downloadDailyTXT(d.year, d.month, d.day))
            except urllib2.HTTPError:
                continue
            for n in xrange(0, 24):
                t = d + datetime.timedelta(hours=n)
                solar = report.renewablesHourly_[n].OutputForType("SOLAR PV")
                wind = report.renewablesHourly_[n].OutputForType("WIND TOTAL")
                yield (
                    t,
                    wind,
                    solar,
                    wind+solar,
                    report.overallHourly_[n].Total())
    tuples = [x for x in data()]

    print "Gathered data, proceeding to plot."
    import plotly
    plotly.plotly.sign_in("username", "access code")

    scatters = [
            plotly.graph_objs.Scatter(
                name="Wind",
                x=[tup[0] for tup in tuples],
                y=[tup[1] for tup in tuples]
                ),
            plotly.graph_objs.Scatter(
                name="Wind, 3-hour average",
                x=[tup[0] for tup in tuples],
                y=rollingMean([tup[1] for tup in tuples], 3)
                ),
            plotly.graph_objs.Scatter(
                name="Wind, 2-day average",
                x=[tup[0] for tup in tuples],
                y=rollingMean([tup[1] for tup in tuples], 48)
                ),
            plotly.graph_objs.Scatter(
                name="Wind, 7-day average",
                x=[tup[0] for tup in tuples],
                y=rollingMean([tup[1] for tup in tuples], 7*24)
                ),
            plotly.graph_objs.Scatter(
                name="Solar, 2-day average",
                x=[tup[0] for tup in tuples],
                y=rollingMean([tup[2] for tup in tuples], 48)
                )
            ]
    d = plotly.graph_objs.Data(scatters[3:])
    plotly.plotly.plot(d, filename='testing-caliso-hourly')
    

graph()
