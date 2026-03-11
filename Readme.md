# 🍲 Cooking Recipe Database

A web app where users can browse, search, and manage recipes. Built with Python and PostgreSQL.

---

## 💡 What This Project Does

- Users can **sign up and log in** securely
- App **scrapes 50 real recipes** from TheMealDB website automatically
- Users can **search and filter** recipes by cuisine and diet
- Users can **like, save, and review** recipes
- Users can **add their own recipes** manually
- Users can **edit or delete** recipes

---

## 🛠️ Technologies Used

- **Python** — main programming language
- **Streamlit** — for building the web interface
- **PostgreSQL** — database to store all data
- **psycopg2** — connects Python to PostgreSQL
- **bcrypt** — for secure password hashing
- **requests** — for web scraping
- **python-dotenv** — for managing secret credentials

---

## 📁 Project Files
```
project/
├── app.py           → main web app (all pages and UI)
├── auth.py          → handles login and signup
├── scraper.py       → scrapes recipes from TheMealDB
├── db.py            → manages database connection
├── .env             → stores database password (not on GitHub)
└── requirements.txt
```

---

## ⚙️ How to Run This Project

### 1. Clone the project
```bash
git clone https://github.com/yourusername/cooking-recipe-database.git
cd cooking-recipe-database
```

### 2. Create virtual environment
```bash
# Mac
python3 -m venv venv
source venv/bin/activate

# Windows
python -m venv venv
venv\Scripts\activate
```

### 3. Install required libraries
```bash
pip install streamlit psycopg2-binary python-dotenv bcrypt requests beautifulsoup4
```

### 4. Create a `.env` file
```
DB_HOST=localhost
DB_NAME=recipedb
DB_USER=postgres
DB_PASSWORD=yourpassword
DB_PORT=5432
APP_TITLE=Cooking Recipe Database
```

### 5. Run the app
```bash
streamlit run app.py
```

Open `http://localhost:8501` in your browser.

---

## 🚀 How to Use

1. Go to **Signup** → create an account
2. Go to **Login** → log in
3. Go to **Seed Database** → click Start Scraping to load 50 real recipes
4. Go to **Browse Recipes** → search, like, save, and review recipes
5. Go to **Add Recipe** → add your own recipe
6. Go to **Manage Recipes** → edit or delete recipes

---

## 🗄️ Database Tables

| Table | What it stores |
|---|---|
| users | username and hashed password |
| recipes | name, cuisine, diet, nutrition info |
| ingredients | ingredients list per recipe |
| steps | cooking steps per recipe |
| reviews | star ratings and comments |
| likes | which user liked which recipe |
| saved_recipes | which user saved which recipe |

---

## 🔒 Security

- Passwords are **never stored as plain text** — bcrypt hashing is used
- SQL queries use **parameterized placeholders** to prevent SQL injection
- Database credentials are stored in `.env` file — never in the code

---

## 👩‍💻 Author

**Khushi Kumari**
Internship Project — Cooking Recipe Database
Data Source: [TheMealDB](https://www.themealdb.com)