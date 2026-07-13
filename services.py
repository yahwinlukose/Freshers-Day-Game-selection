import csv
import requests
import io
import random
from models import db, Participant, Game, GameMember

def import_participants_from_csv(file_stream):
    try:
        # file_stream is a Werkzeug FileStorage object
        content = file_stream.read().decode('utf-8')
        imported, skipped = _process_csv(content)
        return True, f"Successfully imported {imported} participants. Skipped {skipped} duplicates."
    except Exception as e:
        return False, str(e)

def import_participants_from_url(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        imported, skipped = _process_csv(response.text)
        return True, f"Successfully imported {imported} participants. Skipped {skipped} duplicates."
    except Exception as e:
        return False, str(e)

def _process_csv(csv_content):
    reader = csv.DictReader(io.StringIO(csv_content))
    if not reader.fieldnames:
        raise ValueError("CSV is empty or invalid.")
        
    # Map column names to lowercase to be more lenient
    col_map = {c.strip().lower(): c for c in reader.fieldnames if c}
    
    name_col = col_map.get('name')
    gender_col = col_map.get('gender')
    dept_col = col_map.get('department')
    batch_col = col_map.get('batch')
    
    photo_col = col_map.get('upload your photo') or col_map.get('photo') or col_map.get('photo url') or col_map.get('photo_url')
    timestamp_col = col_map.get('timestamp')
    
    if not (name_col and gender_col and (dept_col or batch_col)):
        raise ValueError("CSV must contain 'Name', 'Gender', and either 'Department' or 'Batch' columns.")
        
    imported_count = 0
    skipped_count = 0
    seen = set()
        
    for row in reader:
        # Ignore completely empty rows
        if not any(row.values()):
            continue
            
        name = row[name_col].strip() if name_col and row.get(name_col) else ""
        gender = row[gender_col].strip() if gender_col and row.get(gender_col) else ""
        
        dept = ""
        if dept_col and row.get(dept_col):
            dept = row[dept_col].strip()
        elif batch_col and row.get(batch_col):
            dept = row[batch_col].strip()
            
        timestamp = row[timestamp_col].strip() if timestamp_col and row.get(timestamp_col) else ""
        
        identifier = (name, dept, timestamp)
        if identifier in seen:
            skipped_count += 1
            continue
            
        seen.add(identifier)
            
        photo_path = None
        if photo_col and row.get(photo_col):
            val = row[photo_col].strip()
            if val:
                photo_path = val
                
        participant = Participant(
            name=name,
            department=dept,
            gender=gender,
            photo_path=photo_path,
            status='Available'
        )
        db.session.add(participant)
        imported_count += 1
        
    db.session.commit()
    return imported_count, skipped_count


def generate_teams(game_id, type_, team_size, number_of_teams, gender_rule):
    game = Game.query.get(game_id)
    if not game:
        return False, "Game not found."
    
    total_needed = team_size * number_of_teams if type_ == 'Team' else team_size
    
    query = Participant.query.filter_by(status='Available')
    
    if gender_rule == 'Male Only':
        query = query.filter(Participant.gender.ilike('male'))
    elif gender_rule == 'Female Only':
        query = query.filter(Participant.gender.ilike('female'))
        
    available_participants = query.all()
    
    if len(available_participants) < total_needed:
        return False, f"Insufficient participants. Need {total_needed}, but only {len(available_participants)} available."
        
    selected = []
    
    if gender_rule == 'Mixed' and type_ == 'Team':
        males = [p for p in available_participants if p.gender.lower() == 'male']
        females = [p for p in available_participants if p.gender.lower() == 'female']
        
        random.shuffle(males)
        random.shuffle(females)
        
        teams = {i: [] for i in range(1, number_of_teams + 1)}
        
        for team_idx in range(1, number_of_teams + 1):
            # Try to add at least 1 male and 1 female per team if possible
            if males: teams[team_idx].append(males.pop())
            if females: teams[team_idx].append(females.pop())
            
        remaining_needed = (team_size * number_of_teams) - sum(len(t) for t in teams.values())
        pool = males + females
        random.shuffle(pool)
        
        # Fill the rest
        pool_idx = 0
        for team_idx in range(1, number_of_teams + 1):
            while len(teams[team_idx]) < team_size:
                teams[team_idx].append(pool[pool_idx])
                pool_idx += 1
                
        # Flatten teams to selected list, keeping track of team numbers
        for t_idx, members in teams.items():
            for m in members:
                selected.append((m, t_idx))
    else:
        random.shuffle(available_participants)
        pool = available_participants[:total_needed]
        if type_ == 'Team':
            for i, p in enumerate(pool):
                team_idx = (i // team_size) + 1
                selected.append((p, team_idx))
        else:
            for p in pool:
                selected.append((p, 1))
                
    # Update DB
    for p, t_idx in selected:
        p.status = 'Assigned'
        p.assigned_game_id = game.id
        gm = GameMember(game_id=game.id, participant_id=p.id, team_number=t_idx)
        db.session.add(gm)
        
    db.session.commit()
    return True, "Teams generated successfully."

def release_game_participants(game):
    for gm in game.members:
        participant = gm.participant
        participant.status = 'Available'
        participant.assigned_game_id = None
    # Members will be cascade deleted if Game is deleted, but let's just clear for now
    # If this is called during reset/delete, it handles the state update.
    db.session.commit()
