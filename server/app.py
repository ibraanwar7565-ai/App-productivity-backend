#!/usr/bin/env python3
"""Session-based auth API for a productivity (Notes) app.

Auth endpoints: /signup, /login, /logout, /check_session
Resource endpoints (protected, user-owned): /notes CRUD with pagination.
"""

import math

from flask import request, session, jsonify
from marshmallow import ValidationError
from sqlalchemy.exc import IntegrityError

from config import app, db
from models import User, Note, user_schema, note_schema, notes_schema


def current_user():
    user_id = session.get("user_id")
    if not user_id:
        return None
    return db.session.get(User, user_id)


# ---------------- Auth ----------------

@app.route("/signup", methods=["POST"])
def signup():
    data = request.get_json() or {}
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({"error": "Username and password are required."}), 422

    try:
        user = User(username=username)
        user.password_hash = password
        db.session.add(user)
        db.session.commit()
    except (IntegrityError, ValueError):
        db.session.rollback()
        return jsonify({"error": "Username is taken or invalid."}), 422

    session["user_id"] = user.id
    return jsonify(user_schema.dump(user)), 201


@app.route("/login", methods=["POST"])
def login():
    data = request.get_json() or {}
    user = User.query.filter(User.username == data.get("username")).first()
    if user and user.authenticate(data.get("password", "")):
        session["user_id"] = user.id
        return jsonify(user_schema.dump(user)), 200
    return jsonify({"error": "Invalid username or password."}), 401


@app.route("/logout", methods=["DELETE"])
def logout():
    if not session.get("user_id"):
        return jsonify({"error": "Unauthorized"}), 401
    session["user_id"] = None
    return jsonify({}), 204


@app.route("/check_session", methods=["GET"])
def check_session():
    user = current_user()
    if not user:
        return jsonify({"error": "Unauthorized"}), 401
    return jsonify(user_schema.dump(user)), 200


if __name__ == "__main__":
    app.run(port=5555, debug=True)
