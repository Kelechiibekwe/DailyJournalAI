# app/routes.py
from flask import Flask, jsonify
from app.email_helper import send_journal_email, check_for_reply
from app.models import db, Prompts, Responses, User_Prompt


def init_routes(app):
    @app.route('/')
    def home():
        return "Welcome to my Flask app!"

    @app.route('/send_journal/<int:user_id>', methods=['POST'])
    def send_journal(user_id):
        msg_id = send_journal_email(user_id)
        return jsonify({"message": "Journal email sent", "message_id": msg_id})

    @app.route('/check_reply/<message_id>', methods=['GET'])
    def check_reply(message_id):
        check_for_reply(message_id)
        return jsonify({"message": f"Checked for reply to Message-ID: {message_id}"})
