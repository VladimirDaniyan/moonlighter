#!venv/bin/python
from flask import Flask, render_template, Response, url_for
from flask.ext.script import Manager, Server, Command, Option
from subprocess import Popen, PIPE, STDOUT
from jinja2 import Environment, FileSystemLoader
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

@app.route('/games')
def games():
    def _moonlight_games():
        """Returns the list of game titles from the moonlight list action

        The game list is auto-detected by Nvidia's GeForce Experience app
        Games can manually be added from Preferences -> SHIELD -> Games
        """
        moon_list = Popen(['sudo', '-u', 'pi', 'moonlight', 'list'], stdout=PIPE)
        # remove the non-game titles from the output
        moon_list_sorted = Popen(['sed', '1,4d'], stdin=moon_list.stdout, stdout=PIPE)
        moon_list.stdout.close()
        while moon_list_sorted.poll() is None:
            time.sleep(2)
        output, error = moon_list_sorted.communicate()

        if error is None:
            # moonlight returns a numbered list of game titles
            # parse that to create python list
            pattern = '(?<=\d\.\s).*$'
            steam_games = []
            for game in output.splitlines():
                for match in re.findall(pattern, game):
                    steam_games.append(match)
            return steam_games
        else:
            return Response(error, mimetype='text/html')

    return render_template('games.html', game_list=_moonlight_games())

@app.route('/launch/<game_title>')
def launch_game(game_title):
    """Start streaming a game from the list returned by :func:`games`"""
    def _moonlight_stream(game_title):
        launch_game = Popen(['sudo', '-u', 'pi', 'moonlight', 'stream', '-app',
            game_title, '-mapping', '/home/pi/xbox.conf', '-1080', '-60fps'], stdout=PIPE, stderr=STDOUT)

        for line in iter(launch_game.stdout.readline, b''):
            yield line.rstrip() + '<br/>\n'

    env = Environment(loader=FileSystemLoader('templates'))
    template = env.get_template('launched_game.html')
    return Response(template.generate(output=_moonlight_stream(game_title)))


if __name__ == '__main__':
    manager.run()
