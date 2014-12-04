# printurls.py - returns command for downloading CalISO "renewables watch" data.

import datetime

URL_FORMAT = "http://content.caiso.com/green/renewrpt/%Y%m%d_DailyRenewablesWatch.txt"
START="2014/05/20"
END="2014/05/30"
DATEFORMAT="%Y/%m/%d"

def daterange(s, e):
    for i in range((e - s).days):
        yield s + datetime.timedelta(i)

cmd = "wget --directory-prefix=cache"

for d in daterange(datetime.datetime.strptime(START, DATEFORMAT),
                   datetime.datetime.strptime(END, DATEFORMAT)):
    cmd += " "
    cmd += d.strftime(URL_FORMAT)

print cmd
