from flask import Flask, request, jsonify
from ariadne import ObjectType, QueryType, MutationType, make_executable_schema, graphql_sync, gql
import sqlite3
# from faker import Faker

with open("schema.graphql") as f:
    type_defs = gql(f.read())

app = Flask(__name__)

query = QueryType()
mutation = MutationType()
# fake = Faker()


@app.route("/")
def hello_world():
    return "<p>Hello, World!</p>"

def get_db_connection():
    conn = sqlite3.connect("sport.db")
    conn.row_factory = sqlite3.Row
    return conn

@query.field("getTeams")
def resolve_get_teams(*_):
    conn = get_db_connection()
    teams = conn.execute("SELECT * FROM team").fetchall()
    conn.close()
    
    return [
        {
            "id": row["id"],
            "teamName": row["team_name"],
            "establishedDate": row["established_date"],
            "sportTypeId": row["sport_type_id"]
        }
        for row in teams
    ]

@query.field("getPlayers")
def resolve_get_players(*_):
    conn = get_db_connection()
    players = conn.execute("SELECT * FROM player").fetchall()
    conn.close()
    
    return [
        {
            "id": row["id"],
            "playerName": row["player_name"],
            "number": row["number"],
            "gender": row["gender"],
            "dateOfBirth": row["date_of_birth"],
            "teamId": row["team_id"]
        }
        for row in players
    ]

@query.field("getDbInfo")
def resolve_get_db_info(*_):
    conn = get_db_connection()
    cursor = conn.cursor()
    counts = {
        "sportTypeCount": cursor.execute("SELECT COUNT(*) FROM sport_type").fetchone()[0],
        "teamCount": cursor.execute("SELECT COUNT(*) FROM team").fetchone()[0],
        "playerCount": cursor.execute("SELECT COUNT(*) FROM player").fetchone()[0],
    }
    conn.close()
    return counts

@query.field("getSportTypes")
def resolve_get_sport_types(*_):
    conn = get_db_connection()

    sport_types = conn.execute("SELECT * FROM sport_type").fetchall()

    teams = conn.execute("SELECT * FROM team").fetchall()
    teams_by_sport_type = {}
    for team in teams:
        sport_type_id = team["sport_type_id"]
        if sport_type_id not in teams_by_sport_type:
            teams_by_sport_type[sport_type_id] = []
        teams_by_sport_type[sport_type_id].append({
            "id": team["id"],
            "teamName": team["team_name"],
            "establishedDate": team["established_date"],
            "sportTypeId": team["sport_type_id"],
            "players": []  
        })

    players = conn.execute("SELECT * FROM player").fetchall()
    players_by_team = {}
    for player in players:
        team_id = player["team_id"]
        if team_id not in players_by_team:
            players_by_team[team_id] = []
        players_by_team[team_id].append({
            "id": player["id"],
            "playerName": player["player_name"],
            "number": player["number"],
            "gender": player["gender"],
            "dateOfBirth": player["date_of_birth"]
        })

    for sport_type_id, team_list in teams_by_sport_type.items():
        for team in team_list:
            team["players"] = players_by_team.get(team["id"], [])

    sport_types_with_teams = []
    for row in sport_types:
        sport_types_with_teams.append({
            "id": row["id"],
            "sportType": row["sport_type"],
            "teams": teams_by_sport_type.get(row["id"], [])
        })

    conn.close()
    return sport_types_with_teams




# Mutation Resolvers

@mutation.field("addTeam")
def resolve_add_team(_, info, teamName, establishedDate, sportTypeId):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO team (team_name, established_date, sport_type_id) VALUES (?, ?, ?)",
        (teamName, establishedDate, sportTypeId),
    )
    conn.commit()
    new_id = cursor.lastrowid
    conn.close()
    return {"id": new_id, "teamName": teamName, "establishedDate": establishedDate, "sportTypeId": sportTypeId}

@mutation.field("addPlayer")
def resolve_add_player(_, info, playerName, number, gender, dateOfBirth, teamId):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO player (player_name, number, gender, date_of_birth, team_id) VALUES (?, ?, ?, ?, ?)",
        (playerName, number, gender, dateOfBirth, teamId),
    )
    conn.commit()
    new_id = cursor.lastrowid
    conn.close()
    return {"id": new_id, "playerName": playerName, "number": number, "gender": gender, "dateOfBirth": dateOfBirth, "teamId": teamId}

@mutation.field("editTeam")
def resolve_edit_team(_, info, id, teamName, establishedDate, sportTypeId):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE team SET team_name = ?, established_date = ?, sport_type_id = ? WHERE id = ?",
        (teamName, establishedDate, sportTypeId, id),
    )
    conn.commit()
    conn.close()
    return {"id": id, "teamName": teamName, "establishedDate": establishedDate, "sportTypeId": sportTypeId}

@mutation.field("editPlayer")
def resolve_edit_player(_, info, id, playerName, number, gender, dateOfBirth, teamId):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE player SET player_name = ?, number = ?, gender = ?, date_of_birth = ?, team_id = ? WHERE id = ?",
        (playerName, number, gender, dateOfBirth, teamId, id),
    )
    conn.commit()
    conn.close()
    return {"id": id, "playerName": playerName, "number": number, "gender": gender, "dateOfBirth": dateOfBirth, "teamId": teamId}

@mutation.field("deleteTeam")
def resolve_delete_team(_, info, id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM team WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    return {"deleted": id}

@mutation.field("deletePlayer")
def resolve_delete_player(_, info, id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM player WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    return {"deleted": id}

@mutation.field("addSportType")
def resolve_add_sport_type(_, info, sportType):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO sport_type (sport_type) VALUES (?)",
        (sportType,),
    )
    conn.commit()
    new_id = cursor.lastrowid
    conn.close()
    return {"id": new_id, "sportType": sportType}

@mutation.field("editSportType")
def resolve_edit_sport_type(_, info, id, sportType):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE sport_type SET sport_type = ? WHERE id = ?",
        (sportType, id),
    )
    conn.commit()
    conn.close()
    return {"id": id, "sportType": sportType}

@mutation.field("deleteSportType")
def resolve_delete_sport_type(_, info, id):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM sport_type WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    return {"deleted": id}


@app.route("/graphql", methods=["POST"])
def graphql_server():
    data = request.get_json()
    return schema.execute(data)


def init_db():
    conn = get_db_connection()
    with conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS sport_type (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sport_type TEXT NOT NULL
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS team (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                team_name TEXT NOT NULL,
                established_date TEXT NOT NULL,
                sport_type_id INTEGER,
                FOREIGN KEY (sport_type_id) REFERENCES sport_type (id)
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS player (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                player_name TEXT NOT NULL,
                number INTEGER NOT NULL,
                gender TEXT NOT NULL,
                date_of_birth TEXT NOT NULL,
                team_id INTEGER,
                FOREIGN KEY (team_id) REFERENCES team (id)
            )
        """)


# def populate_database():
#     conn = get_db_connection()
#     cursor = conn.cursor()

#     sport_type_ids = []
#     for _ in range(10):
#         sport_type = fake.word().capitalize()
#         cursor.execute("INSERT INTO sport_type (sport_type) VALUES (?)", (sport_type,))
#         sport_type_ids.append(cursor.lastrowid)

#     team_ids = []
#     for _ in range(200):
#         team_name = fake.company()
#         established_date = fake.date()
#         sport_type_id = fake.random.choice(sport_type_ids)
#         cursor.execute("INSERT INTO team (team_name, established_date, sport_type_id) VALUES (?, ?, ?)",
#                        (team_name, established_date, sport_type_id))
#         team_ids.append(cursor.lastrowid)

#     total_players = 4790
#     players_per_team = total_players // 200  # Base number of players per team
#     extra_players = total_players % 200  # Extra players to distribute

#     for team_id in team_ids:
#         num_players = players_per_team + (1 if extra_players > 0 else 0)
#         extra_players -= 1

#         for _ in range(num_players):
#             player_name = fake.name()
#             number = fake.random_int(min=1, max=99)
#             gender = fake.random_element(elements=("Male", "Female"))
#             date_of_birth = fake.date_of_birth(minimum_age=18, maximum_age=40)
#             cursor.execute(
#                 "INSERT INTO player (player_name, number, gender, date_of_birth, team_id) VALUES (?, ?, ?, ?, ?)",
#                 (player_name, number, gender, date_of_birth, team_id)
#             )

#     conn.commit()
#     conn.close()


if __name__ == "__main__":
    init_db()
    # populate_database()
    schema = make_executable_schema(type_defs, query, mutation)
    app.run(debug=True)
