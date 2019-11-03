import os
import click
from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask.views import MethodView


basedir = os.path.abspath(os.path.dirname(__file__))

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////' + os.path.join(basedir, 'data.sqlite')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
CORS(app)

from src.models import Message


@app.cli.command()
@click.option('--drop', is_flag=True, help='Create after drop.')
def initdb(drop):
    if drop:
        click.confirm('This operation will delete the database, do you want to continue?', abort=True)
        db.drop_all()
        click.echo('Drop database.')
    db.create_all()
    click.echo('Initialized database.')


@app.cli.command()
@click.option('--count', default=20, help='Quantity of messages, default is 20.')
def forge(count):
    from faker import Faker

    db.drop_all()
    db.create_all()

    fake = Faker()
    click.echo('Working...')

    for i in range(count):
        message = Message(
            name=fake.name(),
            body=fake.sentence(),
            timestamp=fake.date_time_this_year()
        )
        db.session.add(message)

    db.session.commit()
    click.echo('Created %d fake messages.' % count)


def message_schema(message):
    return {
        'id': message.id,
        'name': message.name,
        'body': message.body,
        'timestamp': message.timestamp
    }


class MessageAPI(MethodView):
    def get(self):
        messages = Message.query.order_by(Message.timestamp.desc()).all()
        return jsonify(
            messages=[message_schema(message) for message in messages]
        )

    def post(self):
        data = request.get_json()
        message = Message(
            name=data['name'],
            body=data['body']
        )
        db.session.add(message)
        db.session.commit()
        response = jsonify(message_schema(message))
        response.status_code = 201
        return response


app.add_url_rule('/api/v1/message', view_func=MessageAPI.as_view('message'), methods=['GET', 'POST'])
