import os
import pytest
from flaskr import create_app
from .database import db
from .models import Tags


app = create_app(config_mode='development')
app.app_context().push()

tag_names = ["Python", "Flask", "Web Development", "Tutorial", "SQLAlchemy", "Backend"]
for name in tag_names:
    if not Tags.query.filter_by(name=name).first():
        tag = Tags(name=name)
        db.session.add(tag)

db.session.commit()
print("Tags added to the database.")

