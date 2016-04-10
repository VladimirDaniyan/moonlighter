#!venv/bin/python
from flask import Flask, render_template
from subprocess import Popen, PIPE
from flask.ext.script import Manager, Server, Command, Option

# http://stackoverflow.com/questions/14566570/how-to-use-flask-script-and-gunicorn
class GunicornServer(Command):
    """Run the app within Gunicorn"""

    def get_options(self):
        from gunicorn.config import make_settings

        settings = make_settings()
        options = (
            Option(*klass.cli, action=klass.action)
            for setting, klass in settings.iteritems() if klass.cli
        )
        return options

    def run(self, *args, **kwargs):
        from gunicorn.app.wsgiapp import WSGIApplication

        app = WSGIApplication()
        app.app_uri = 'moonlighty:app'
        return app.run()


app = Flask(__name__)

manager = Manager(app)
manager.add_command("runserver", Server(host='0.0.0.0'))
manager.add_command("gunicorn", GunicornServer())

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/launch')
def moonlight():
    logfile = open('/var/log/moonlighty/moonlight.log', 'w')
    cmd = ['sudo', '-u', 'pi', 'moonlight', 'stream', '-app', 'Steam', '-mapping', '/home/pi/xbox.conf', '-1080', '-30fps']
    p = Popen(cmd, stdout=logfile, stderr=logfile)
    output = p.communicate()
    return output

if __name__ == '__main__':
    manager.run()
