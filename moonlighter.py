#!venv/bin/python

from flask import Flask, render_template, Response, url_for
from flask.ext.script import Manager, Server, Command, Option
from flask_ask import Ask, statement, question, session
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
        app.app_uri = 'moonlighter:app'
        return app.run()


app = Flask(__name__)
ask = Ask(app, '/')

manager = Manager(app)
manager.add_command("runserver", Server(host='0.0.0.0'))
manager.add_command("gunicorn", GunicornServer())


@app.route('/')
def index():
    return render_template('index.html')


def moonlight_games():
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


@app.route('/games')
def games():
    """Render the games list html template"""
    return render_template('games.html', game_list=moonlight_games())


@app.route('/launch/<game_title>')
def launch_game(game_title):
    """Start streaming a game from the list returned by :func:`games`"""
    def _moonlight_stream(game_title):
        launch_game = Popen(['sudo', '-u', 'pi', 'moonlight', 'stream', '-app',
            game_title, '-mapping', '/home/pi/xbox.conf', '-1080', '-60fps'], stdout=PIPE, stderr=STDOUT)

        if launch_game.returncode < 0:
            return "Launched {}".format(game_title)
        else:
            return launch_game.returncode

    env = Environment(loader=FileSystemLoader('templates'))
    template = env.get_template('launched_game.html')
    return Response(template.generate(output=_moonlight_stream(game_title)))


@ask.launch
def alexa_welcome():
    """Welcome message when launching the Alexa Skill"""
    card_title = render_template('card_title')
    welcome_msg = render_template('welcome')
    welcome_reprompt = render_template('welcome_reprompt')
    return question(welcome_msg).reprompt(welcome_reprompt).simple_card(card_title, welcome_msg)


@ask.intent('AskGameIntent')
def alexa_ask_game():
    """Return the five three games in the list"""
    card_title = render_template('card_title')
    game_list = moonlight_games()
    game_list_msg = render_template('game_list', games=game_list[:5])
    session.attributes['games'] = game_list[:5]
    return question(game_list_msg).simple_card(card_title, game_list_msg)


@ask.intent('AnswerGameIntent', mapping={'game_title': 'Game'})
def alexa_launch_game(game_title):
    """Launch the desired GameStream App"""
    card_title = render_template('card_title')
    if game_title is not None:
      statement_msg = render_template('known_game', game=game_title.title())
      launch_game(game_title.title())
      return statement(statement_msg).simple_card(card_title, statement_msg)
    else:
      question_msg = render_template('unknown_game')
      return question(question_msg).simple_card(card_title, question_msg)


@ask.session_ended
def session_ended():
  return "", 200


if __name__ == '__main__':
    manager.run()
