import os
from flask import Flask, url_for
from config import Config
from models import db
from routes import main
from routes.punishment import punishment_bp

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    db.init_app(app)
    
    app.register_blueprint(main)
    app.register_blueprint(punishment_bp)
    
    @app.context_processor
    def utility_processor():
        def get_participant_image_url(participant):
            """Return a normalized image URL for a participant.
            Handles paths stored as '/static/...' or 'static/...' or full URLs."""
            if not participant or not participant.photo_path:
                return url_for('static', filename='images/default-avatar.png')
            path = participant.photo_path.strip()
            if path.startswith(('http://', 'https://')):
                return path
            # Ensure leading slash for browser resolution
            if not path.startswith('/'):
                path = '/' + path
            return path
        return dict(get_participant_image_url=get_participant_image_url)
    
    with app.app_context():
        # Create database tables if they don't exist
        db.create_all()
        
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, port=5000)
