import importlib
import os
import sys
from flask import Flask
from flask_cors import CORS
# Get the absolute path to the Blueprints folder.
blueprints_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'Blueprints')
sys.path.insert(0, blueprints_folder)

app = Flask(__name__)
CORS(app)
## Load all controllers in the blueprints folder.
def register_blueprints(app, blueprints_folder):
    for filename in os.listdir(blueprints_folder):
        if filename.endswith('.py') and filename != '__init__.py':
            module_name = filename[:-3]
            try:
                module = importlib.import_module(module_name)
                blueprint = getattr(module, module_name)
                app.register_blueprint(blueprint)
                print(f"Registered blueprint: {module_name}")
            except (ImportError, AttributeError) as e:
                print(f"Error importing {module_name}: {e}")

# Register blueprints
register_blueprints(app, blueprints_folder)

# Print the route list
routes = [str(rule) for rule in app.url_map.iter_rules()]
print(routes)

if __name__ == "__main__":
    app.run(debug=True)