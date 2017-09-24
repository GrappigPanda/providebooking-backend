from flask_migrate import MigrateCommand, Migrate
from flask_script import Manager
from almanac.almanac import create_app

app = create_app(None)

from almanac.models import db
migrate = Migrate(app, db)

manager = Manager(app)
manager.add_command('db', MigrateCommand)

manager.run()