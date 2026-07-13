import os
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, session, jsonify
import secrets
from werkzeug.utils import secure_filename
from models import db, Participant, Game, GameMember
import services

main = Blueprint('main', __name__)

@main.app_context_processor
def inject_csrf_token():
    def generate_csrf_token():
        if '_csrf_token' not in session:
            session['_csrf_token'] = secrets.token_hex(16)
        return session['_csrf_token']
    return dict(csrf_token=generate_csrf_token)

@main.route('/')
def index():
    total = Participant.query.count()
    available = Participant.query.filter_by(status='Available').count()
    assigned = Participant.query.filter_by(status='Assigned').count()
    games = Game.query.order_by(Game.created_at.desc()).limit(5).all()
    return render_template('index.html', total=total, available=available, assigned=assigned, games=games)

@main.route('/participants', methods=['GET', 'POST'])
def participants():
    query = Participant.query
    
    # Filters
    search = request.args.get('search', '')
    dept = request.args.get('department', '')
    gender = request.args.get('gender', '')
    status = request.args.get('status', '')
    
    if search:
        query = query.filter(Participant.name.ilike(f'%{search}%'))
    if dept:
        query = query.filter(Participant.department == dept)
    if gender:
        query = query.filter(Participant.gender == gender)
    if status:
        query = query.filter(Participant.status == status)
        
    participants_list = query.all()
    
    # For filter dropdowns
    departments = db.session.query(Participant.department).distinct().all()
    departments = [d[0] for d in departments]
    
    return render_template('participants.html', participants=participants_list, 
                           departments=departments, search=search, 
                           sel_dept=dept, sel_gender=gender, sel_status=status)

@main.route('/import', methods=['POST'])
def import_participants():
    source_type = request.form.get('source_type')
    
    if source_type == 'csv':
        if 'csv_file' not in request.files:
            flash('No file part', 'danger')
            return redirect(url_for('main.index'))
        file = request.files['csv_file']
        if file.filename == '':
            flash('No selected file', 'danger')
            return redirect(url_for('main.index'))
        if file:
            success, msg = services.import_participants_from_csv(file)
            flash(msg, 'success' if success else 'danger')
            if success:
                return redirect(url_for('main.participants'))
            
    elif source_type == 'url':
        url = request.form.get('google_sheet_url')
        if not url:
            flash('URL is required', 'danger')
            return redirect(url_for('main.index'))
        success, msg = services.import_participants_from_url(url)
        flash(msg, 'success' if success else 'danger')
        if success:
            return redirect(url_for('main.participants'))
        
    return redirect(url_for('main.index'))

@main.route('/upload_photo/<int:participant_id>', methods=['POST'])
def upload_photo(participant_id):
    participant = Participant.query.get_or_404(participant_id)
    if 'photo' not in request.files:
        flash('No file part', 'danger')
        return redirect(url_for('main.participants'))
        
    file = request.files['photo']
    if file.filename == '':
        flash('No selected file', 'danger')
        return redirect(url_for('main.participants'))
        
    if file:
        filename = secure_filename(f"p_{participant.id}_{file.filename}")
        os.makedirs(current_app.config['UPLOAD_FOLDER'], exist_ok=True)
        filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        participant.photo_path = url_for('static', filename=f"uploads/{filename}")
        db.session.commit()
        flash('Photo uploaded successfully', 'success')
        
    return redirect(url_for('main.participants'))

@main.route('/create_game', methods=['GET', 'POST'])
def create_game():
    if request.method == 'POST':
        name = request.form.get('name')
        type_ = request.form.get('type')
        team_size = int(request.form.get('team_size') or 1)
        num_teams = int(request.form.get('number_of_teams') or 1)
        gender_rule = request.form.get('gender_rule', 'Random')
        
        game = Game(
            name=name,
            type=type_,
            team_size=team_size,
            number_of_teams=num_teams if type_ == 'Team' else 1,
            gender_rule=gender_rule
        )
        db.session.add(game)
        db.session.commit()
        
        success, msg = services.generate_teams(game.id, type_, team_size, num_teams, gender_rule)
        
        if success:
            flash('Game created and teams generated!', 'success')
            return redirect(url_for('main.game_result', game_id=game.id))
        else:
            db.session.delete(game)
            db.session.commit()
            flash(msg, 'danger')
            return redirect(url_for('main.create_game'))
            
    return render_template('create_game.html')

@main.route('/game/<int:game_id>')
def game_result(game_id):
    game = Game.query.get_or_404(game_id)
    # Group members by team number
    teams = {}
    for member in game.members:
        teams.setdefault(member.team_number, []).append(member.participant)
        
    return render_template('game_result.html', game=game, teams=teams)

@main.route('/game/<int:game_id>/reshuffle', methods=['POST'])
def reshuffle_game(game_id):
    game = Game.query.get_or_404(game_id)
    services.release_game_participants(game)
    GameMember.query.filter_by(game_id=game.id).delete()
    db.session.commit()
    
    success, msg = services.generate_teams(game.id, game.type, game.team_size, game.number_of_teams, game.gender_rule)
    if success:
        flash('Teams reshuffled successfully.', 'success')
    else:
        flash(f'Failed to reshuffle: {msg}', 'danger')
    return redirect(url_for('main.game_result', game_id=game.id))

@main.route('/games')
def games():
    all_games = Game.query.order_by(Game.created_at.desc()).all()
    return render_template('games.html', games=all_games)

@main.route('/game/<int:game_id>/delete', methods=['POST', 'DELETE'])
def delete_game(game_id):
    # CSRF check
    token = session.get('_csrf_token', None)
    client_token = request.form.get('csrf_token') or request.headers.get('X-CSRFToken')
    if not token or token != client_token:
        return jsonify({'success': False, 'error': 'Invalid CSRF token.'}), 403

    game = Game.query.get_or_404(game_id)
    try:
        # Release participants
        services.release_game_participants(game)
        # Delete related GameMembers explicitly
        GameMember.query.filter_by(game_id=game.id).delete()
        # Delete Game
        db.session.delete(game)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': f'Failed to delete game: {str(e)}'}), 500
        
    return jsonify({
        "success": True,
        "message": "Game deleted successfully."
    }), 200

@main.route('/reset', methods=['POST'])
def reset_all():
    token = session.get('_csrf_token', None)
    if not token or token != request.form.get('csrf_token'):
        flash('Invalid CSRF token.', 'danger')
        return redirect(url_for('main.index'))
        
    try:
        Participant.query.update({Participant.status: 'Available', Participant.assigned_game_id: None})
        GameMember.query.delete()
        db.session.commit()
        flash('All participant assignments have been reset successfully.', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'An error occurred: {str(e)}', 'danger')
        
    return redirect(url_for('main.index'))
