# Football Club Manager

A single-player football management game developed for the BIL372 Database Systems course. The project models accounts, careers, clubs, players, matches, fixtures, and transfers in a relational database, then makes those systems playable through a web interface.

The app runs locally or as a hosted web service. The browser interface is served by FastAPI, which handles the game rules and match simulation. The demo can store data in memory; PostgreSQL can be configured for persistent storage.

## Live Demo

[Play FootballManagerGame](https://footballmanagergame.onrender.com/)

The demo is hosted on Render. The free service may go to sleep after inactivity, so the first request after a quiet period can take up to a minute to load.

## Developers

- Ömer Kara
- Kubilay Filiz
- Mohammad El Ledib

## How to Play

1. Create an account and sign in. Choose a name for your club when prompted.
2. Your club starts with a budget of 2,000,000 and a squad of 12 players. The league has four clubs in total, including yours.
3. In **Squad & Tactics**, choose a 4-3-3 or 4-4-2 formation and assign players to positions. Review your team's defense, midfield, and attack ratings. A player cannot fill more than one starting position.
4. From **Overview**, play the next week. The server simulates both matches scheduled that week and records scores, goals, assists, player performances, and league standings.
5. Open **Fixtures & Matches** to review match reports, starting lineups, formations, and match events.
6. In the **Transfer Market**, filter players from rival clubs and make offers. Evaluate an offer to see whether it is accepted; accepted transfers update your squad and budget. The **Finance** page shows transfer income and expenses.
7. A season ends after six weeks. Review player and formation performance in **Statistics**, start a new season, and revisit completed seasons in **Season Archive**.

The league uses a home-and-away format: each club plays every other club once at home and once away. A season lasts six weeks and contains 12 matches. A win earns three points and a draw earns one. Element combinations among your starting players can add team-strength bonuses.

## Features

- Account registration, sign-in, and sign-out
- A separate league and career for each account
- Club names, player squads, and market values
- 4-3-3 and 4-4-2 formations, starting-lineup selection, and position compatibility
- Team-strength and element-bonus calculations
- Weekly fixtures, match simulation, goals, assists, and player statistics
- League standings, player rankings, and formation performance
- Transfer market, offer evaluation, transfer history, and club finances
- End-of-season player development, new seasons, and season archives
- In-memory demo mode and optional persistent storage with PostgreSQL

## Run Locally

Requirements: Python 3.10 or newer and PowerShell.

From the project directory, create a virtual environment and install the dependencies:

~~~powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
~~~

Start the demo server:

~~~powershell
.\run_demo.ps1
~~~

Open the web app at http://127.0.0.1:8765. The API documentation is available at http://127.0.0.1:8765/docs.

The script starts the server in memory mode. To start it manually:

~~~powershell
$env:BIL372_USER_STORE = "memory"
.\.venv\Scripts\python.exe -m uvicorn backend.main:app --host 127.0.0.1 --port 8765
~~~

In memory mode, accounts, matches, and career progress exist only while the server process is running. They reset when the server restarts.

### PostgreSQL Mode

For persistent storage, follow the database, role, ODBC driver, and .env setup instructions in [the PostgreSQL Development Guide](02_PostgreSQL_Gelistirme_Rehberi.md). Then start the server with:

~~~powershell
$env:BIL372_USER_STORE = "postgres"
.\.venv\Scripts\python.exe -m uvicorn backend.main:app --host 127.0.0.1 --port 8765
~~~

The run_demo.ps1 script selects memory mode, so use the command above for PostgreSQL. The .env file is ignored by Git; do not commit local database passwords.

## Project Structure

~~~text
backend/       FastAPI endpoints, game rules, match engine, and PostgreSQL layer
web/           Browser interface (HTML, CSS, JavaScript)
docs/          SQL examples and OpenAPI specification
render.yaml    Render configuration for the hosted web service
test_*.py      Tests for backend game logic and data access
requirements.txt
run_demo.ps1
00_*.md        Game and project overview
01_*.md        Frontend development guide
02_*.md        PostgreSQL and course-deliverables guide
~~~

The interface sends JSON requests to the same FastAPI server and uses Bearer tokens for account-specific endpoints. In memory mode, the backend stores careers in process memory. In PostgreSQL mode, career, club, player, season, fixture, match, and transfer data are stored in relational tables.

## Course Scope

This repository includes the playable web demo, backend, and database-design guides. The guides also describe separate course deliverables such as loading a large synthetic dataset, measuring five analytical SQL queries on PostgreSQL, and comparing query plans before and after indexing.
