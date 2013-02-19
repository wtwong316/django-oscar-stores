import os


__version__ = (0, 3, 3)


# Keep a setting for the path to the templates in case a project subclasses the
# models and still needs to use the templates
TEMPLATE_DIR = os.path.join(
    os.path.dirname(__file__),
    'templates')
