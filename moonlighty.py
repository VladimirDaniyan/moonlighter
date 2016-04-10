#!venv/bin/python
from flask import Flask, render_template, Response, jsonify
from flask.ext.script import Manager, Server, Command, Option
from subprocess import Popen, PIPE
import re
import time
import sys

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

@app.route('/list')
def game_list():

    def moonlight_games():
        #logfile = open('/var/log/moonlighty/moonlight.log', 'w')
        #cmd = ['sudo', '-u', 'pi', 'moonlight', 'stream', '-app', 'Steam', '-mapping', '/home/pi/xbox.conf', '-1080', '-30fps']
        moon_list = Popen(['sudo', '-u', 'pi', 'moonlight', 'list'], stdout=PIPE)
        moon_list_sorted = Popen(['sed', '1,4d'], stdin=moon_list.stdout, stdout=PIPE)
        moon_list.stdout.close()
        while moon_list_sorted.poll() is None:
            time.sleep(2)
        output, error = moon_list_sorted.communicate()

        # moonlight returns a numbered list of games, we want to parse that
        pattern = '(?<=\d\.\s).*$'
        steam_games = []
        if error is None:
            for game in output.splitlines():
                for match in re.findall(pattern, game):
                    steam_games.append(match)
            return steam_games
        else:
            raise IOError(error)

    return Response(moonlight_games(), mimetype='text/html')

#TODO: create dynamic routes based on game list
# allowing games to be started directly
@app.route('/list/<game>')
def start_game():

if __name__ == '__main__':
    manager.run()
