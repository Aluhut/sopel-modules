# coding=utf8

# flask module
import sopel
from sopel import module
#from flask import Flask, abort, request
from flask import Flask, abort
import threading

# display
import colorsys
import hashlib
import re
import pprint
import dateutil.parser
import os

app = Flask(__name__)
local_bot = None

def setup(bot):
    global local_bot
    global app
    local_bot = bot
    #start_new_thread(app.run,(),{'port': 9999})
    threading.Thread(target=app.run,
        args=(),
        kwargs={'host': '0.0.0.0', 'port': 11111},
    ).start()


def shutdown(bot):
    func = request.environ.get('werkzeug.server.shutdown')
    if func is not None:
        func()

@app.route('/', methods=['GET'])
def flipdot_log():
    with app.test_request_context():
        from flask import request
    css = "::-webkit-scrollbar,::-webkit-scrollbar-button,::-webkit-scrollbar-track,::-webkit-scrollbar-track-piece,::-webkit-scrollbar-thumb,::-webkit-scrollbar-corner,::-webkit-resizer{ background-color:red; };}"
    ret = "<html><head><meta http-equiv=\"refresh\" content='10; URL=/#end'> </head><body onLoad='setTimeout(function() { window.scrollTo(0, document.body.scrollHeight || document.documentElement.scrollHeight) }, 1);' style='font-family:monospace; background: black; color: white; font-size:38px; "+css+"'>"

    chanlogs = getattr(local_bot.config.chanlogs, "dir", None)
    if chanlogs is None:
        raise ConfigurationError("Channel logs needs a 'dir' set.")


    with open("%s/flipdot.log" % chanlogs, "r") as f:
        f.seek (0, 2)           # Seek @ EOF
        fsize = f.tell()        # Get Size
        f.seek (max (fsize-2048, 0), 0) # Set pos @ last n chars
        lines = f.readlines()       # Read to end

    lines = lines[-22:]    # Get last 22 lines

    #stdin,stdout = os.popen2("tail -n 13 "+chanlogs+"/flipdot.log")
    #stdin.close()
    #lines = stdout.readlines()
    lastname = ""
    backlog = []
    names = []
    for l in lines:
        pl = process_line(l)
        if pl is "":
            continue
        print(l, pl, len(pl))
        print(pl[0],pl[1],pl[2],pl[3])
        for p in pl:
            if p is not None:
                print(p)
        date, name, color, text = process_line(l)
        backlog.append((date, name, color, text))
        if not name in names:
            names.append(name)
    #stdout.close()
    for l in backlog:
        date, name, color, text = l
        if name == lastname:
            name = "-"
        else:
            lastname = name
        # highlight nicks in messages
        for n in names:
            text = text.replace(n, "<font color=\"#%s\">%s</font>" % (get_color(n), n))
        # highlight urls in messages
        text = re.sub(r'([a-z]+://[^ ]+/?)', '<font color="#14cc75"><u>\\1</u></font>', text)

        ret += "%s <font color=\"#%s\">%s</font> %s<br>" % (date, color, name, text)
        if name == "ERROR":
            break

    ret += "<div id=\"end\"></div></body></html>"
    return ret

def get_color(string, n=76):
    n = float(n)
    color = colorsys.hsv_to_rgb((abs(hash(string)) % n) / n, .9, .8)
    return "%x%x%x" % (color[0]*255, color[1]*255, color[2]*255)

def process_line(line):
    try:
        # divide by: date user text
        # 1999-04-01T23:42:59+00:00  <nick_name> hello, world!
        # 2016-05-19T07:17:14+00:00  *** flipbot has joined #flipdot
        regex = re.compile("([^<]+) [<*]+ ?([^> ]*)>? (.*)?")
        search = regex.search(line)
        if not search:
            return ""
        date = dateutil.parser.parse(search.group(1))
        datestr = date.strftime("<font color=\"#555\">%H:%M</font>")
        name = search.group(2)
        #text = re.escape(search.group(3))
        text = search.group(3)
        text = re.sub(r"&","&amp;",text)
        text = re.sub(r"\"","&quot;",text)
        text = re.sub(r"<","&lt;",text)
        text = re.sub(r">","&gt;",text)
        color = get_color(name)
        return (datestr, name, color, text)
    except Exception as e:
	#for i in dir(e):
	#	print(i, getattr(e, i))
        try:
            if "nothing to repeat" in e.message:
                return("", "ERROR", "FF0000", "Wrong Python 2 version. Please update to at least version 2.7.9.")
            return("", "ERROR", "FF0000", e.message)
        except AttributeError as e2:
            return("", "ERROR", "FF0000", "LOG FILE IS BR&Ouml;KEN<br>%s<br>%s<br>%s" % (e.args, e.with_traceback, dir(e)))
