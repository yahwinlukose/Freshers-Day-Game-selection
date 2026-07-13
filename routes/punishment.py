from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from models import db
from models.punishment import Punishment, SpinHistory

punishment_bp = Blueprint('punishment', __name__, url_prefix='/punishment')

from flask import session

@punishment_bp.before_request
def csrf_protect():
    if request.method == "POST":
        token = session.get('_csrf_token', None)
        if not token or token != request.form.get('csrf_token'):
            flash('Invalid CSRF token.', 'danger')
            return redirect(url_for('punishment.wheel'))

def get_wheel_state(sort_by='newest', filter_by='all', search=''):
    query = Punishment.query
    if search:
        query = query.filter(Punishment.text.ilike(f'%{search}%'))
    if filter_by == 'active':
        query = query.filter(Punishment.is_active == True)
    elif filter_by == 'used':
        query = query.filter(Punishment.is_active == False)
        
    if sort_by == 'name':
        query = query.order_by(Punishment.text.asc())
    elif sort_by == 'status':
        query = query.order_by(Punishment.is_active.desc(), Punishment.text.asc())
    elif sort_by == 'oldest':
        query = query.order_by(Punishment.created_at.asc())
    else:
        query = query.order_by(Punishment.created_at.desc())
        
    punishments = query.all()
    active_punishments = Punishment.query.filter_by(is_active=True).all()
    
    total_count = Punishment.query.count()
    active_count = len(active_punishments)
    used_count = total_count - active_count
    
    history = SpinHistory.query.order_by(SpinHistory.spun_at.desc()).limit(10).all()
    
    return {
        'punishments': [{'id': p.id, 'text': p.text, 'is_active': p.is_active, 'created_at': p.created_at.strftime('%Y-%m-%d')} for p in punishments],
        'active_punishments': [{'id': p.id, 'text': p.text} for p in active_punishments],
        'stats': {'total': total_count, 'active': active_count, 'used': used_count},
        'history': [{'text': h.punishment.text if h.punishment else "[Deleted Punishment]", 'spun_at': h.spun_at.strftime('%Y-%m-%d %H:%M:%S')} for h in history]
    }

def wants_json():
    return request.headers.get('Accept', '').find('application/json') > -1

@punishment_bp.route('/')
def wheel():
    sort_by = request.args.get('sort', 'newest')
    filter_by = request.args.get('filter', 'all')
    search = request.args.get('search', '').strip()
    
    state = get_wheel_state(sort_by, filter_by, search)
    if wants_json():
        return jsonify(state)
        
    return render_template('punishment/wheel.html',
                           punishments=Punishment.query.all(), # Passed for initial render, actual values taken from state below
                           active_punishments=state['active_punishments'],
                           total_count=state['stats']['total'],
                           active_count=state['stats']['active'],
                           used_count=state['stats']['used'],
                           history=[], # will be hydrated by JS
                           search=search,
                           sort=sort_by,
                           filter=filter_by)

@punishment_bp.route('/add', methods=['POST'])
def add():
    text = request.form.get('text', '').strip()
    if not text:
        if wants_json(): return jsonify({'error': 'Punishment cannot be empty.'}), 400
        flash('Punishment cannot be empty.', 'danger')
        return redirect(url_for('punishment.wheel'))
        
    exists = Punishment.query.filter(Punishment.text.ilike(text)).first()
    if exists:
        if wants_json(): return jsonify({'error': 'This punishment already exists.'}), 400
        flash('This punishment already exists.', 'warning')
        return redirect(url_for('punishment.wheel'))
        
    new_punishment = Punishment(text=text, is_active=True)
    db.session.add(new_punishment)
    db.session.commit()
    
    if wants_json(): return jsonify(get_wheel_state())
    flash('Punishment added successfully.', 'success')
    return redirect(url_for('punishment.wheel'))

@punishment_bp.route('/edit/<int:id>', methods=['POST'])
def edit(id):
    punishment = Punishment.query.get_or_404(id)
    text = request.form.get('text', '').strip()
    
    if not text:
        if wants_json(): return jsonify({'error': 'Punishment cannot be empty.'}), 400
        flash('Punishment cannot be empty.', 'danger')
        return redirect(url_for('punishment.wheel'))
        
    exists = Punishment.query.filter(Punishment.text.ilike(text), Punishment.id != id).first()
    if exists:
        if wants_json(): return jsonify({'error': 'This punishment already exists.'}), 400
        flash('This punishment already exists.', 'warning')
        return redirect(url_for('punishment.wheel'))
        
    punishment.text = text
    db.session.commit()
    
    if wants_json(): return jsonify(get_wheel_state())
    flash('Punishment updated successfully.', 'success')
    return redirect(url_for('punishment.wheel'))

@punishment_bp.route('/delete/<int:id>', methods=['POST'])
def delete(id):
    punishment = Punishment.query.get_or_404(id)
    try:
        db.session.delete(punishment)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        if wants_json(): return jsonify({'error': 'Failed to delete punishment.'}), 500
        flash('Failed to delete punishment.', 'danger')
        return redirect(url_for('punishment.wheel'))
        
    if wants_json(): return jsonify(get_wheel_state())
    flash('Punishment deleted permanently.', 'success')
    return redirect(url_for('punishment.wheel'))

@punishment_bp.route('/spin', methods=['POST'])
def spin():
    punishment_id = request.form.get('punishment_id')
    punishment = Punishment.query.get(punishment_id)
    
    if not punishment or not punishment.is_active:
        return jsonify({'success': False, 'error': 'Invalid or inactive punishment.'}), 400
        
    punishment.is_active = False
    
    spin_history = SpinHistory(punishment_id=punishment.id)
    db.session.add(spin_history)
    db.session.commit()
    
    state = get_wheel_state()
    state['success'] = True
    state['spun_text'] = punishment.text
    return jsonify(state)

@punishment_bp.route('/reset', methods=['POST'])
def reset():
    try:
        SpinHistory.query.delete()
        Punishment.query.delete()
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        if wants_json(): return jsonify({'error': 'Failed to reset wheel. Transaction rolled back.'}), 500
        flash('Failed to reset wheel.', 'danger')
        return redirect(url_for('punishment.wheel'))
        
    if wants_json(): return jsonify(get_wheel_state())
    flash('Wheel reset successfully! All punishments deleted.', 'success')
    return redirect(url_for('punishment.wheel'))
