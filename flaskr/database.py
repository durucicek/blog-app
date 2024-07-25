from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from flask_migrate import Migrate # type: ignore

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)
migrate = Migrate()

def init_app(app):
    db.init_app(app)
    # with app.app_context():
    #     db.create_all()
    migrate.init_app(app, db)
    