import json

import flask
from flask import jsonify

from data import db_session
from .data.messages import Message

blueprint = flask.Blueprint(
    'messages_api',
    __name__,
    template_folder='templates'
)


@blueprint.route('/api/messages')
def get_messages():
    db_sess = db_session.create_session()
    messages = db_sess.query(Message).all()
    db_sess.commit()
    messages_to_json = {'messages': list()}
    if not messages:
        return jsonify({'error': 'Not found'})
    for message in messages:
        message_to_json = {"message_id": message.id,
                           "id_from": message.user_id_from,
                           "id_to": message.user_id_to,
                           "message_content": message.content,
                           "message_title": message.title,
                           "created_date": str(message.created_date)}
        messages_to_json["messages"].append(message_to_json)
    messages_to_json['messages'].sort(key=lambda msg: msg["message_id"])
    return json.dumps(messages_to_json)


@blueprint.route('/api/messages/<int:message_id>', methods=['GET'])
def get_one_news(message_id):
    db_sess = db_session.create_session()
    message = db_sess.query(Message).filter((Message.id == message_id)).first()
    db_sess.commit()
    if not message:
        return jsonify({'error': 'Not found'})
    return json.dumps(
        {
            'messages': [{"message_id": message.id,
                          "id_from": message.user_id_from,
                          "id_to": message.user_id_to,
                          "message_content": message.content,
                          "message_title": message.title,
                          "created_date": str(message.created_date)}]
        }
    )
