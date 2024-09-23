from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
import sqlite3

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Replace this with a secure key

# Setup Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

DATABASE = 'database.db'

def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row  # To access columns by name
    return conn

# User class for Flask-Login
class User(UserMixin):
    def __init__(self, id):
        self.id = id

@login_manager.user_loader
def load_user(user_id):
    return User(user_id)

# Home page: Display the league table with total points for each team
@app.route('/')
def index():
    conn = get_db_connection()
    teams = conn.execute('''
        SELECT teams.id, teams.name, 
            IFNULL(ROUND(SUM(
                CASE 
                    WHEN players.position = 'Quarterback' THEN 
                        (0.1 * stats.passing_yards + 4 * stats.passing_touchdowns + stats.extra_points - 2 * stats.interceptions_qb)
                    ELSE 
                        (1 * stats.receptions + 0.1 * stats.yards + 6 * stats.touchdowns + 2 * stats.interceptions)
                END
            ), 2), 0) as total_points
        FROM teams
        LEFT JOIN players ON teams.id = players.team_id
        LEFT JOIN stats ON players.id = stats.player_id
        GROUP BY teams.id
        ORDER BY total_points DESC
    ''').fetchall()
    conn.close()
    return render_template('index.html', teams=teams)


# Players page: List all players with their total points
@app.route('/players')
def players():
    conn = get_db_connection()

    # Fetch quarterbacks sorted by total points (highest to lowest)
    quarterbacks = conn.execute('''
        SELECT players.id, players.name, teams.name as team,
               players.passing_yards, players.passing_touchdowns, players.extra_points, players.interceptions_qb,
               ROUND(0.1 * players.passing_yards + 4 * players.passing_touchdowns + 1 * players.extra_points - 2 * players.interceptions_qb, 2) as total_points
        FROM players
        JOIN teams ON players.team_id = teams.id
        WHERE players.position = 'Quarterback'
        ORDER BY total_points DESC
    ''').fetchall()

    # Fetch wide receivers sorted by total points (highest to lowest)
    wide_receivers = conn.execute('''
        SELECT players.id, players.name, teams.name as team,
               players.receptions, players.yards, players.touchdowns, players.interceptions,
               ROUND(1 * players.receptions + 0.1 * players.yards + 6 * players.touchdowns + 2 * players.interceptions, 2) as total_points
        FROM players
        JOIN teams ON players.team_id = teams.id
        WHERE players.position = 'Wide Receiver'
        ORDER BY total_points DESC
    ''').fetchall()

    conn.close()
    return render_template('players.html', quarterbacks=quarterbacks, wide_receivers=wide_receivers)



# Player detail page: Show a player's stats and weekly breakdown
@app.route('/player/<int:player_id>')
def player_detail(player_id):
    conn = get_db_connection()

    # Get player information
    player = conn.execute('''
        SELECT players.id, players.name, teams.name as team, players.position, 
               (CASE WHEN players.position = 'Quarterback' THEN 
                    ROUND(0.1 * players.passing_yards + 4 * players.passing_touchdowns + players.extra_points - 2 * players.interceptions_qb, 2)
                ELSE 
                    ROUND(1 * players.receptions + 0.1 * players.yards + 6 * players.touchdowns + 2 * players.interceptions, 2)
                END) as total_points
        FROM players
        JOIN teams ON players.team_id = teams.id
        WHERE players.id = ?
    ''', (player_id,)).fetchone()

    # Get stats for the player by week
    if player['position'] == 'Quarterback':
        stats = conn.execute('''
            SELECT week, passing_yards, passing_touchdowns, extra_points, interceptions_qb,
                   ROUND(0.1 * passing_yards + 4 * passing_touchdowns + extra_points - 2 * interceptions_qb, 2) as total_points
            FROM stats
            WHERE player_id = ?
            ORDER BY week ASC
        ''', (player_id,)).fetchall()
    else: 
        stats = conn.execute('''
            SELECT week, receptions, yards, touchdowns, interceptions,
                   ROUND(1 * receptions + 0.1 * yards + 6 * touchdowns + 2 * interceptions, 2) as total_points
            FROM stats
            WHERE player_id = ?
            ORDER BY week ASC
        ''', (player_id,)).fetchall()

    conn.close()
    return render_template('player.html', player=player, stats=stats)


# Edit stats page: Form for editing or adding weekly stats for a player
@app.route('/edit-stats/<int:player_id>/<int:week>', methods=('GET', 'POST'))
@login_required
def edit_stats(player_id, week):
    conn = get_db_connection()

    # Get the player and their position
    player = conn.execute('SELECT * FROM players WHERE id = ?', (player_id,)).fetchone()

    # Get existing stats for the player and week, if available
    stat = conn.execute('SELECT * FROM stats WHERE player_id = ? AND week = ?', (player_id, week)).fetchone()

    if request.method == 'POST':
        if player['position'] == 'Quarterback':
            passing_yards = request.form['passing_yards']
            passing_touchdowns = request.form['passing_touchdowns']
            extra_points = request.form['extra_points']
            interceptions_qb = request.form['interceptions_qb']

            if stat:
                # Update existing stats for quarterbacks
                conn.execute('''
                    UPDATE stats 
                    SET passing_yards = ?, passing_touchdowns = ?, extra_points = ?, interceptions_qb = ?
                    WHERE id = ?
                ''', (passing_yards, passing_touchdowns, extra_points, interceptions_qb, stat['id']))
            else:
                # Insert new stats for quarterbacks
                conn.execute('''
                    INSERT INTO stats (player_id, week, passing_yards, passing_touchdowns, extra_points, interceptions_qb)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (player_id, week, passing_yards, passing_touchdowns, extra_points, interceptions_qb))

            # Update the quarterback's total stats
            conn.execute('''
                UPDATE players 
                SET passing_yards = (SELECT SUM(passing_yards) FROM stats WHERE player_id = ?),
                    passing_touchdowns = (SELECT SUM(passing_touchdowns) FROM stats WHERE player_id = ?),
                    extra_points = (SELECT SUM(extra_points) FROM stats WHERE player_id = ?),
                    interceptions_qb = (SELECT SUM(interceptions_qb) FROM stats WHERE player_id = ?)
                WHERE id = ?
            ''', (player_id, player_id, player_id, player_id, player_id))

        else:
            # Handle stats for Wide Receivers
            receptions = request.form['receptions']
            yards = request.form['yards']
            touchdowns = request.form['touchdowns']
            interceptions = request.form['interceptions']

            if stat:
                # Update existing stats for wide receivers
                conn.execute('''
                    UPDATE stats 
                    SET receptions = ?, yards = ?, touchdowns = ?, interceptions = ?
                    WHERE id = ?
                ''', (receptions, yards, touchdowns, interceptions, stat['id']))
            else:
                # Insert new stats for wide receivers
                conn.execute('''
                    INSERT INTO stats (player_id, week, receptions, yards, touchdowns, interceptions)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (player_id, week, receptions, yards, touchdowns, interceptions))

            # Update the wide receiver's total stats
            conn.execute('''
                UPDATE players 
                SET receptions = (SELECT SUM(receptions) FROM stats WHERE player_id = ?),
                    yards = (SELECT SUM(yards) FROM stats WHERE player_id = ?),
                    touchdowns = (SELECT SUM(touchdowns) FROM stats WHERE player_id = ?),
                    interceptions = (SELECT SUM(interceptions) FROM stats WHERE player_id = ?)
                WHERE id = ?
            ''', (player_id, player_id, player_id, player_id, player_id))

        conn.commit()
        conn.close()
        return redirect(url_for('player_detail', player_id=player_id))

    conn.close()
    return render_template('edit_stats.html', stat=stat, player=player, week=week)


# Login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # For simplicity, we are using hardcoded credentials
        if username == 'UFA' and password == 'Winter24Szn':
            user = User(id=1)  # Mock user ID
            login_user(user)
            return redirect(url_for('index'))
        else:
            flash('Invalid credentials')

    return render_template('login.html')

# Shows players on that team
@app.route('/team/<int:team_id>')
def team_detail(team_id):
    conn = get_db_connection()
    
    # Fetch the team name
    team = conn.execute('SELECT name FROM teams WHERE id = ?', (team_id,)).fetchone()

    # Fetch the players and their stats for the selected team
    players = conn.execute('''
        SELECT players.id, players.name, players.position, 
               players.receptions, players.yards, players.touchdowns, players.interceptions, 
               players.passing_yards, players.passing_touchdowns, players.extra_points, players.interceptions_qb,
               ROUND((1 * players.receptions + 0.1 * players.yards + 6 * players.touchdowns + 2 * players.interceptions +
                0.1 * players.passing_yards + 4 * players.passing_touchdowns + players.extra_points - 2 * players.interceptions_qb), 1) AS total_points
        FROM players
        WHERE players.team_id = ?
        ORDER BY players.position, players.name
    ''', (team_id,)).fetchall()
    
    conn.close()
    
    return render_template('team_detail.html', team=team, players=players)



# Logout route
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
