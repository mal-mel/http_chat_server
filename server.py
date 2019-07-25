from flask import Flask, request, jsonify, abort
from datetime import datetime

from db import cursor, connection


app = Flask(__name__)


@app.route('/users/add', methods=['POST'])
def add_user():
    if not request.json or 'username' not in request.json:
        abort(400)
    cursor.execute(f"insert into user (username, created_at) values('{request.json['username']}', '{datetime.now()}')")
    connection.commit()
    user_id = cursor.execute(f"select id from user where username='{request.json['username']}'").fetchall()[0][0]
    return jsonify({'user_id': user_id})


@app.route('/chats/add', methods=['POST'])
def add_chat():
    if not request.json or 'name' not in request.json or 'users' not in request.json:
        abort(400)
    last_chat_id = (cursor.execute("select max(id) from chat").fetchall()[0][0] + 1) \
        if cursor.execute("select max(id) from chat").fetchall()[0][0] \
        else 1
    cursor.execute(f"insert into chat (name, users, created_at) values ("
                   f"'{request.json['name']}', "
                   f"'{last_chat_id}', "
                   f"'{datetime.now()}')")
    connection.commit()
    for user_id in request.json['users']:
        cursor.execute(f"insert into user_chat values({last_chat_id}, {user_id})")
    connection.commit()
    return jsonify({'chat_id': last_chat_id})


@app.route('/messages/add', methods=['POST'])
def send_message():
    if not request.json or 'chat' not in request.json or 'author' not in request.json or 'text' not in request.json:
        abort(400)
    date = datetime.now()
    if (int(request.json['author']),) in \
            cursor.execute(f"select user_id from user_chat where chat_id={request.json['chat']}").fetchall():
        cursor.execute(f"insert into message (chat, author, text, created_at) values("
                       f"{request.json['chat']}, "
                       f"{request.json['author']}, "
                       f"'{request.json['text']}', "
                       f"'{date}');")
        connection.commit()
        message_id = cursor.execute(f"select id from message where created_at='{date}'").fetchall()[0][0]
        return jsonify({'message_id': message_id})
    abort(403)


@app.route('/chats/get', methods=['POST'])
def get_chats_list():
    if not request.json or 'user' not in request.json or not request.json['user'].isdigit():
        abort(400)
    chats_id = cursor.execute(f"select chat_id from user_chat where user_id={request.json['user']}").fetchall()
    last_messages = []
    for chat_id in chats_id:
        if cursor.execute(f"select created_at from message where chat={chat_id[0]}").fetchall():
            last_messages.append([chat_id[0],
                                  sorted([i[0] for i in cursor.execute(f"select created_at from message where chat={chat_id[0]}")
                                         .fetchall()])[-1]
                                  ])
    result = sorted([cursor.execute(f"select * from chat where id={i[0]}").fetchall()[0] for i in last_messages],
                    key=lambda x: x[1], reverse=True)
    return jsonify({'chats': result})


@app.route('/messages/get', methods=['POST'])
def get_messages():
    if not request.json or 'chat' not in request.json or not request.json['chat'].isdigit():
        abort(400)
    result = sorted(cursor.execute(f"select * from message where chat={request.json['chat']}").fetchall(),
                    key=lambda x: x[4])
    return jsonify({'messages': result})


if __name__ == '__main__':
    app.run('localhost', 9000, debug=True)
