#!flask/bin/python
from flask import Flask, render_template
from subprocess import Popen, PIPE
from flask.ext.script import Manager, Server

app = Flask(__name__)

manager = Manager(app)
manager.add_command("runserver", Server(host='0.0.0.0'))

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/launch')
def moonlight():
    cmd = ['moonlight', 'stream', '-app', 'Steam', '-mapping', 'xbox.conf', '-1080', '-30fps']
    #cmd = ["ls", "-l"]
    p = Popen(cmd, stdout=PIPE, stderr=PIPE)
    output, err = p.communicate()
    if p.returncode != 0:
        print ("moonlight failed %d %s" % (p.returncode, err))
    else:
        return output

if __name__ == '__main__':
    manager.run()
