#!flask/bin/python
from flask import Flask
from subprocess import Popen, PIPE

app = Flask(__name__)

@app.route('/')
def moonlight():
    # cmd = ['moonlight', 'stream', '-app', 'Steam', '-mapping', 'xbox.conf', '-1080', '-30fps']
    cmd = ["ls", "-l"]
    p = Popen(cmd, stdout=PIPE, stderr=PIPE)
    output, err = p.communicate()
    if p.returncode != 0:
        print ("moonlight failed %d %s" % (p.returncode, err))
    else:
        return output

if __name__ == '__main__':
    app.run(debug=True)
