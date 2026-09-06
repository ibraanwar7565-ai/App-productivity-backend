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


# ---------------- Notes (protected, user-owned) ----------------

@app.route("/notes", methods=["GET"])
def list_notes():
    user = current_user()
    if not user:
        return jsonify({"error": "Unauthorized"}), 401

    page = request.args.get("page", 1, type=int) or 1
    per_page = request.args.get("per_page", 5, type=int) or 5

    query = Note.query.filter(Note.user_id == user.id).order_by(Note.id)
    total = query.count()
    total_pages = math.ceil(total / per_page) if per_page else 0
    items = query.offset((page - 1) * per_page).limit(per_page).all()

    return jsonify({
        "page": page,
        "per_page": per_page,
        "total": total,
        "total_pages": total_pages,
        "items": notes_schema.dump(items),
    }), 200


@app.route("/notes/<int:id>", methods=["GET"])
def get_note(id):
    user = current_user()
    if not user:
        return jsonify({"error": "Unauthorized"}), 401
    note = db.session.get(Note, id)
    if note is None or note.user_id != user.id:
        return jsonify({"error": "Note not found"}), 404
    return jsonify(note_schema.dump(note)), 200


@app.route("/notes", methods=["POST"])
def create_note():
    user = current_user()
    if not user:
        return jsonify({"error": "Unauthorized"}), 401

    try:
        data = note_schema.load(request.get_json() or {})
    except ValidationError as err:
        return jsonify({"errors": err.messages}), 422

    try:
        note = Note(
            title=data["title"],
            content=data.get("content"),
            category=data.get("category"),
            user_id=user.id,
        )
        db.session.add(note)
        db.session.commit()
    except (IntegrityError, ValueError):
        db.session.rollback()
        return jsonify({"error": "Could not create note."}), 422

    return jsonify(note_schema.dump(note)), 201


@app.route("/notes/<int:id>", methods=["PATCH"])
def update_note(id):
    user = current_user()
    if not user:
        return jsonify({"error": "Unauthorized"}), 401
    note = db.session.get(Note, id)
    if note is None or note.user_id != user.id:
        return jsonify({"error": "Note not found"}), 404

    data = request.get_json() or {}
    for field in ("title", "content", "category"):
        if field in data:
            setattr(note, field, data[field])
    try:
        db.session.commit()
    except (IntegrityError, ValueError):
        db.session.rollback()
        return jsonify({"error": "Could not update note."}), 422
    return jsonify(note_schema.dump(note)), 200


@app.route("/notes/<int:id>", methods=["DELETE"])
def delete_note(id):
    user = current_user()
    if not user:
        return jsonify({"error": "Unauthorized"}), 401
    note = db.session.get(Note, id)
    if note is None or note.user_id != user.id:
        return jsonify({"error": "Note not found"}), 404
    db.session.delete(note)
    db.session.commit()
    return jsonify({"message": f"Note {id} deleted"}), 200


if __name__ == "__main__":
    app.run(port=5555, debug=True)
