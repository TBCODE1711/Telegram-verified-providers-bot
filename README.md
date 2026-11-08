# 🛡️ VouchBot — Verified Service Providers Management Bot

[![Python](https://img.shields.io/badge/Python-3.14-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![aiogram](https://img.shields.io/badge/aiogram-3.28-2CA5E0?style=for-the-badge&logo=telegram&logoColor=white)](https://docs.aiogram.dev/)
[![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0_(Async)-D71F00?style=for-the-badge&logo=sqlalchemy&logoColor=white)](https://www.sqlalchemy.org/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-asyncpg-4169E1?style=for-the-badge&logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?style=for-the-badge&logo=docker&logoColor=white)](https://www.docker.com/)

> **A generic, customizable Telegram bot designed for community owners to manage vetted service providers, moderate user reviews, and facilitate safe client-to-professional communication.**

---

## 📖 Overview & Problem Statement

Telegram communities have become major hubs for digital commerce and freelance services—spanning software development, digital marketing, graphic design, financial exchange, and consulting. However, finding reliable professionals within fast-moving group chats remains a significant challenge. Users often struggle to verify a provider's legitimacy, track authentic client feedback, or avoid impersonators.

**VouchBot** solves this trust gap by providing community administrators with a centralized, tamper-resistant directory of verified professionals. Built to real-world client specifications with a focus on modularity, any community can deploy and customize the bot—defining its own service categories, branding, and moderation team exclusively through environment variables without modifying a single line of code.

---

## 🎥 Live Demo & Walkthrough

🔗 **Live Test Bot:** [Try the Bot on Telegram]https://t.me/verefied_providers_test_bot

### Video Demonstration

<div align="center">
  <a href="https://drive.google.com/file/d/11wVj1cx0Jy5GMMyEnLNrVIuc_2wh0vN0/view?usp=sharing">
    <img src="PASTE_GITHUB_IMAGE_URL_HERE" alt="Watch VouchBot Video Demonstration" width="700"/>
  </a>
  <p><i>▶️ Click the image above to watch the full video walkthrough (User Directory, Reviews & Admin Moderation).</i></p>
</div>

---

## ✨ Key Features

### 👤 End-User Experience
* **Dynamic Category Directory:** Browse verified professionals neatly organized by customizable service categories.
* **Direct & Safe Communication:** Initiate a direct Telegram chat (`tg://user?id=...`) with a service provider using their permanent Telegram User ID—preventing username-spoofing scams.
* **Verified Peer Reviews:** Read authentic, admin-approved reviews from previous clients before hiring a provider.
* **Interactive Review Submission:** Submit feedback on any listed professional through a guided Finite State Machine (`FSM`) conversation flow.

### 🛠️ Admin & Moderation Panel (`/admin`)
* **Role-Based Access Control:** Strictly restricted via custom router filters matching authorized Telegram User IDs (`ADMIN_IDS`).
* **Provider Onboarding Flow:** Multi-step interactive wizard to register new providers (User ID validation, optional username, display name, category selection, and pre-commit summary confirmation).
* **Search & Live Editing:** Look up providers by either **Telegram ID** or **Username** to update their display name or reassign their category in real time.
* **Soft-Delete Lifecycle Management:** Activate or deactivate (`is_active`) providers on demand, hiding suspended providers from public view while preserving their historical data and reviews in the database.
* **FIFO Review Moderation Queue:** Process pending user reviews in strict chronological order (*First-In, First-Out*) with one-click **Approve** or **Reject** actions.
* **Media Utility:** Automatically extracts and logs the Telegram `file_id` of photos sent by admins for easy welcome-banner configuration.

### ⚙️ UX & System Engineering
* **Automated Chat Hygiene:** Tracks transient bot prompts and user inputs inside the `FSMContext` and bulk-deletes intermediate messages upon flow completion or cancellation—keeping the chat interface clean.
* **Zero-Code Customization:** Categories, admin permissions, welcome media, and networking parameters are injected dynamically at runtime via environment variables.

---

## 🏗️ Architecture & Tech Stack

The project follows a clean **Layer-Based Architecture** enforcing separation of concerns across presentation, state management, business logic, and data persistence.

| Component | Technology | Purpose |
| :--- | :--- | :--- |
| **Language** | Python 3.14 | Core runtime with modern async/await and type hinting |
| **Bot Framework** | `aiogram 3.28` | Asynchronous Telegram Bot API framework (Routers, Filters, FSM) |
| **Webhook Server** | `aiohttp 3.13` | Event-driven HTTP server handling incoming Telegram webhook updates |
| **ORM & Database** | `SQLAlchemy 2.0` + `asyncpg` | Fully asynchronous PostgreSQL ORM and connection pooling |
| **Configuration** | `python-dotenv` | Environment variable loading and validation |
| **Containerization** | Docker | Lightweight `python:3.14-slim` production container |

### 📂 Project Structure

```text
Telegram_users_bot/
│
├── core/                          # Infrastructure, configuration & utilities
│   ├── __init__.py
│   ├── config.py                  # Environment variables loading & validation
│   ├── telegram_bot_webhook.py    # aiohttp webhook server lifecycle setup
│   └── utils.py                   # FSM message tracking & bulk cleanup helpers
│
├── database/                      # Data persistence layer
│   ├── __init__.py
│   ├── models.py                  # Declarative SQLAlchemy ORM models
│   ├── connection.py              # Async engine, session factory & table initialization
│   └── crud.py                    # Asynchronous database queries & CRUD operations
│
├── handlers/                      # Event routers & business logic
│   ├── __init__.py
│   ├── admin_handlers.py          # Admin panel, provider CRUD & review moderation flows
│   └── user_handlers.py           # Public directory browsing & review submission flows
│
├── keyboards/                     # Inline keyboard builders
│   ├── __init__.py
│   ├── admin_keyboards.py         # Admin dashboard & moderation buttons
│   ├── user_keyboards.py          # Category, provider list & action menus
│   └── shared_keyboards.py        # Reusable confirmation & cancel keyboards
│
├── states/                        # Finite State Machine (FSM) definitions
│   ├── __init__.py
│   ├── admin_states.py            # States for adding, searching & editing providers
│   └── user_states.py             # State for submitting a provider review
│
├── strings/                       # UI text constants & templates
│   ├── __init__.py
│   ├── strings.py                 # Admin interface prompts & notifications
│   └── user_strings.py            # User-facing messages & HTML templates
│
├── main.py                        # Application entry point & dispatcher wiring
├── Dockerfile                     # Production container definition
├── .dockerignore
├── .gitignore
└── requirements.txt
```

---

## 🗄️ Database Schema

The persistence layer uses two relational PostgreSQL tables managed via SQLAlchemy's asynchronous `DeclarativeBase`:

1. **`service_providers`**
   * `user_id` (`BigInteger`, Primary Key) — The provider's permanent Telegram ID.
   * `username` (`String`, Nullable) — Optional Telegram `@username`.
   * `display_name` (`String`, Not Null) — Public name displayed in the directory.
   * `category` (`String`, Not Null) — Assigned service category.
   * `is_active` (`Boolean`, Default `True`) — Controls visibility in the public directory (Soft Delete).
   * `created_at` (`DateTime(timezone=True)`) — Server-side creation timestamp.

2. **`reviews`**
   * `review_id` (`Integer`, Primary Key, Auto-increment) — Unique review identifier.
   * `provider_id` (`BigInteger`, Foreign Key $\rightarrow$ `service_providers.user_id`) — Target provider.
   * `sender_id` (`BigInteger`, Not Null) — Reviewer's Telegram ID.
   * `sender_username` (`String`, Nullable) — Reviewer's Telegram username.
   * `review_text` (`String`, Not Null) — Content of the review.
   * `status` (`String`, Default `"PENDING"`) — Moderation state (`PENDING`, `APPROVED`, `REJECTED`).
   * `created_at` (`DateTime(timezone=True)`) — Timestamp used for FIFO moderation ordering.

---

## ⚙️ Environment Variables

Create a `.env` file in the root directory before running the application. All sensitive credentials and community customizations are configured here:

| Variable | Required | Default | Description |
| :--- | :---: | :---: | :--- |
| `BOT_TOKEN` | **Yes** | — | Telegram Bot token obtained from [@BotFather](https://t.me/BotFather). |
| `DATABASE_URL` | **Yes** | — | Async PostgreSQL connection string (`postgresql+asyncpg://user:pass@host:port/dbname`). |
| `DB_POOL_SIZE` | No | `2` | Number of persistent connections kept open in the SQLAlchemy connection pool. |
| `DB_MAX_OVERFLOW` | No | `3` | Maximum number of additional overflow connections allowed beyond `DB_POOL_SIZE`. |
| `DB_ECHO` | No | `False` | Enables SQLAlchemy SQL query logging when set to `true`. |
| `WEBHOOK_HOST` | **Yes** | — | Public HTTPS base URL where Telegram sends webhook updates (e.g., `https://your-domain.com`). |
| `WEBHOOK_SECRET` | **Yes** | — | Secret token used to verify incoming webhook requests via `X-Telegram-Bot-Api-Secret-Token`. |
| `PORT` | No | `8080` | Local port the `aiohttp` server listens on (`0.0.0.0:PORT`). |
| `LOG_LEVEL` | No | `"INFO"` | Application logging verbosity (`DEBUG`, `INFO`, `WARNING`, `ERROR`). |
| `ADMIN_IDS` | **Yes** | `""` | Comma-separated list of Telegram User IDs granted access to `/admin`. |
| `CATEGORIES` | No | `"Programmers,Exchangers,Marketers,Graphic Designers"` | Comma-separated list of service categories displayed to users and admins. |
| `MAIN_PIC_ID` | No | `""` | Optional Telegram `file_id` for the welcome banner photo on `/start`. |
| `REVIEWS_PER_PAGE` | No | `5` | Number of approved reviews displayed per page before pagination controls appear. |

### Example `.env` file:
```env
BOT_TOKEN=1234567890:AAH_your_telegram_bot_token_here
DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/vouchbot_db
DB_POOL_SIZE=2
DB_MAX_OVERFLOW=3
DB_ECHO=False
WEBHOOK_HOST=https://your-public-webhook-url.com
WEBHOOK_SECRET=your_random_webhook_secret_token_here
PORT=8080
LOG_LEVEL=INFO
ADMIN_IDS=111111111,222222222
CATEGORIES=Programmers,Exchangers,Marketers,Graphic Designers
MAIN_PIC_ID=
REVIEWS_PER_PAGE=5
```

---

## 🚀 Getting Started

The application is completely infrastructure-agnostic. You can run it locally in a Python virtual environment, deploy it as a standalone Docker container on any VPS, or host it on serverless container platforms (such as Google Cloud Run, AWS App Runner, Render, or Railway) paired with any self-hosted or managed PostgreSQL database.

### Option 1: Local Development Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/TBCODE1711/Telegram_users_bot.git
   cd Telegram_users_bot
   ```

2. **Create and activate a virtual environment:**
   ```bash
   # Windows (PowerShell)
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1

   # Linux / macOS
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Expose local port for Telegram Webhooks (Development):**
   Because the bot operates via Webhooks rather than polling, expose your local port (`8080`) using a reverse-proxy tunnel such as `ngrok` or Cloudflare Tunnel:
   ```bash
   ngrok http 8080
   ```
   Copy the generated `https://...` forwarding URL into `WEBHOOK_HOST` in your `.env` file.

5. **Run the bot:**
   ```bash
   python main.py
   ```

---

### Option 2: Docker Deployment (Production)

1. **Build the Docker image:**
   ```bash
   docker build -t vouchbot:latest .
   ```

2. **Run the container:**
   ```bash
   docker run -d \
     --name vouchbot \
     -p 8080:8080 \
     --env-file .env \
     vouchbot:latest
   ```

> **Note on Serverless & Managed Databases:** The asynchronous SQLAlchemy engine in `database/connection.py` is pre-configured with a lightweight connection pool (`pool_size=2`, `max_overflow=3`), making it safe out-of-the-box for both traditional servers and auto-scaling serverless environments connected to managed PostgreSQL providers.

---

## 📄 License

This project was developed as an academic software engineering project built to real-world client specifications. Available under the [MIT License](https://opensource.org/licenses/MIT).

