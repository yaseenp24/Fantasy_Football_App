import sqlite3

# Connect to SQLite database (it will create the file if it doesn't exist)
conn = sqlite3.connect('database.db')
c = conn.cursor()

# Create Teams Table
c.execute('''
    CREATE TABLE IF NOT EXISTS teams (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL
    )
''')

# Create Players Table with added position-specific stats for Quarterbacks and Wide Receivers
c.execute('''
    CREATE TABLE IF NOT EXISTS players (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        team_id INTEGER,
        position TEXT NOT NULL,
        receptions INTEGER DEFAULT 0,
        yards INTEGER DEFAULT 0,
        touchdowns INTEGER DEFAULT 0,
        passing_yards INTEGER DEFAULT 0,
        passing_touchdowns INTEGER DEFAULT 0,
        extra_points INTEGER DEFAULT 0,
        interceptions INTEGER DEFAULT 0,
        interceptions_qb INTEGER DEFAULT 0,  -- Interceptions for Quarterbacks
        FOREIGN KEY(team_id) REFERENCES teams(id)
    )
''')

# Create Stats Table for both Wide Receivers and Quarterbacks
c.execute('''
    CREATE TABLE IF NOT EXISTS stats (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        player_id INTEGER,
        week INTEGER,
        receptions INTEGER DEFAULT 0,
        yards INTEGER DEFAULT 0,
        touchdowns INTEGER DEFAULT 0,
        passing_yards INTEGER DEFAULT 0,
        passing_touchdowns INTEGER DEFAULT 0,
        extra_points INTEGER DEFAULT 0,
        interceptions INTEGER DEFAULT 0,
        interceptions_qb INTEGER DEFAULT 0,  -- Interceptions for Quarterbacks
        FOREIGN KEY(player_id) REFERENCES players(id)
    )
''')

# Seed Teams based on the screenshot
teams = ['Gridiron Gang', 'The Poodles', 'Dirty Birdz', 'The Eastern Farmers', 'Bomberos']
team_map = {team: i + 1 for i, team in enumerate(teams)}  # Map team names to IDs

for team in teams:
    c.execute('INSERT INTO teams (name) VALUES (?)', (team,))

# Player list with the correct teams and correct quarterbacks based on the screenshots
player_team_assignments = [
    ('Mali', 'Gridiron Gang'),
    ('Ali', 'Gridiron Gang'),  # Quarterback
    ('Fahad', 'Gridiron Gang'),
    ('Hayder', 'Gridiron Gang'),
    ('Scott', 'Gridiron Gang'),
    ('Muhammad S', 'Gridiron Gang'),
    ('Maher', 'Gridiron Gang'),
    ('Omar Patel', 'Gridiron Gang'),
    ('Mujahid S', 'The Poodles'),
    ('Nathaniel', 'The Poodles'),
    ('Ismaeel Harsolia', 'The Poodles'),
    ('Mujahid Zaman', 'The Poodles'),
    ('Ahmad Kazi', 'The Poodles'),
    ('Maaz', 'The Poodles'),  # Quarterback
    ('CJ', 'The Poodles'),
    ('Arnold', 'The Poodles'),
    ('Ibrahim Khan', 'The Eastern Farmers'),
    ('Amjad', 'The Eastern Farmers'),  # Quarterback
    ('Samir', 'The Eastern Farmers'),
    ('Kareem', 'The Eastern Farmers'),
    ('Omar Ibrahim', 'The Eastern Farmers'),
    ('Mohammad H', 'The Eastern Farmers'),
    ('Abu Moe', 'The Eastern Farmers'),
    ('Subhi', 'The Eastern Farmers'),
    ('Sufyan', 'Dirty Birdz'),
    ('Zuhair', 'Dirty Birdz'),  # Quarterback
    ('Jamal', 'Dirty Birdz'),
    ('Bilal', 'Dirty Birdz'),
    ('Laayouni', 'Dirty Birdz'),
    ('Umair', 'Dirty Birdz'),
    ('Hadi O', 'Dirty Birdz'),
    ('Yaseen', 'Dirty Birdz'),
    ('Eesa', 'Bomberos'),
    ('Christian', 'Bomberos'),
    ('Ryan', 'Bomberos'),
    ('Yazen', 'Bomberos'),  # Quarterback
    ('Hadi', 'Bomberos'),
    ('Bashar', 'Bomberos'),
    ('Ibrahim', 'Bomberos'),
    ('Bo', 'Bomberos'),  # Quarterback
]

# Insert each player into the correct team based on the list above
for player_name, team_name in player_team_assignments:
    position = 'Quarterback' if player_name in ['Ali', 'Maaz', 'Amjad', 'Zuhair', 'Bo'] else 'Wide Receiver'
    team_id = team_map[team_name]
    c.execute('INSERT INTO players (name, team_id, position) VALUES (?, ?, ?)', (player_name, team_id, position))

conn.commit()
conn.close()
print("Database setup complete with updated player team and quarterback assignments.")

