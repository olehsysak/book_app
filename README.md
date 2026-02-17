# 📚 Library Hub

Library Hub is a REST API for managing a library, books, reviews, and personal book collections.

---

## ℹ️ About

Library Hub is an **asynchronous REST API** for managing books and users.  
It integrates with the external **Open Library API** to fetch book data and stores additional information in a PostgreSQL database.

---

## 🛠 Tech Stack

- FastAPI (async REST API framework)
  
- PostgreSQL (relational database)
  
- SQLAlchemy + Alembic (ORM + migrations)
  
- Docker & Docker Compose (containerization)
  
- JWT Authentication (secure user login)
  
- Open Library API Integration (fetch external book data)

---

## ✨ Features

- **Users and Authentication** – registration, login, and account management  
- **Book Management** – searching, viewing, and adding reviews  
- **Favorite Books and Reading Lists** – organizing personal lists  
- **User Book Collections** – creating and managing personal bookshelves  

---

## 🐳 Run with Docker

---

### 1️⃣ Clone the repository

```bash
git clone https://github.com/olehsysak/LibraryHub.git

cd LibraryHub
```

### 2️⃣ Create the .env file

Copy the example file to create your own .env:

```bash
cp .env.example .env
```

You can optionally edit this file to set your own:

- SECRET_KEY — secret key for FastAPI

- POSTGRES_USER — database username

- POSTGRES_PASSWORD — database password

- POSTGRES_DB — database name

Docker and Alembic will use these values automatically.

### 3️⃣ Start the Docker containers

```bash
docker compose up -d --build
```

This command will:

- Start the PostgreSQL database

- Apply Alembic migrations

- Launch the FastAPI server

### 4️⃣ Create Admin User

After the containers are running, create an admin user:

```bash
docker compose exec web python scripts/create_admin.py
```

This will create an admin account with the following credentials:

- Email: admin@example.com

- Password: admin007 (or whatever you set in the script)

### ✅ Access the API

- Main URL: http://localhost:8000

- Swagger documentation: http://localhost:8000/docs

---

## 💻 Run Locally Without Docker

### 1️⃣ Clone the repository

```bash
git clone https://github.com/olehsysak/LibraryHub.git

cd LibraryHub
```

### 2️⃣ Create virtual environment

```bash
python -m venv venv

venv\Scripts\activate  # Windows

# source venv/bin/activate  # Linux/macOS
```

### 3️⃣ Install dependencies

```bash
pip install --upgrade pip

pip install -r requirements.txt
```

### 4️⃣ Configuration

1. Copy the example file:

```bash
cp .env.example .env
```

2. Open .env and update the values:

```bash
SECRET_KEY=your_secret_key

POSTGRES_USER=your_user

POSTGRES_PASSWORD=your_password

POSTGRES_DB=your_database

DATABASE_URL=postgresql+asyncpg://your_user:your_password@localhost:5432/your_database
```

Make sure DATABASE_URL matches your local PostgreSQL credentials and database name.

Use localhost since you are running the server without Docker.

### 5️⃣ Run migrations

```bash
alembic upgrade head
```

### 6️⃣ Start server

```bash
uvicorn app.main:app --reload
```

### 7️⃣ Create Admin User

After starting the server, create an admin account:

```bash
python scripts/create_admin.py
```

Default credentials:

- Email: admin@example.com

- Password: admin007 (or whatever you set in the script)

### ✅ Access the API

- Main URL: http://localhost:8000

- Swagger documentation: http://localhost:8000/docs
