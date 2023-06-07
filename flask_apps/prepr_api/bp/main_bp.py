from flask import Blueprint


main = Blueprint('main_bp', __name__)


@main.route('/')
def index():
    return "Hello World!"
