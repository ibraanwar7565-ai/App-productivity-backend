#!/usr/bin/env python3
"""Seed the productivity app with example users and notes."""

from faker import Faker

from config import app, db
from models import User, Note

fake = Faker()

with app.app_context():
    print("Clearing old data...")
    Note.query.delete()
    User.query.delete()
    db.session.commit()

    print("Creating users...")
    alice = User(username="alice")
    alice.password_hash = "password123"
    bob = User(username="bob")
    bob.password_hash = "password123"
    db.session.add_all([alice, bob])
    db.session.commit()

    print("Creating notes...")
    categories = ["work", "personal", "ideas", "errands"]
    for owner in (alice, bob):
        for _ in range(12):
            db.session.add(Note(
                title=fake.sentence(nb_words=4),
                content=fake.paragraph(nb_sentences=3),
                category=fake.random_element(categories),
                user=owner,
            ))
    db.session.commit()
    print("Done seeding!")
