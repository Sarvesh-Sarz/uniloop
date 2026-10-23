# Uniloop — Campus Resource Sharing & Peer-to-Peer Rental Hub

> **Tagline:** *Share More. Spend Less.*  
> A hyperlocal marketplace and peer-to-peer rental web platform for university students to safely rent, borrow, and lend textbooks, lab equipment, electronics, calculators, and tools.

---

## 1. Project Overview

Students often buy expensive items (such as scientific calculators, specialized lab coats, engineering drawing kits, or ₹2,000+ textbooks) for a single semester and then never use them again. Meanwhile, incoming students need the exact same items. 

**Uniloop** solves this problem by providing a verified, campus-focused resource hub where students from the same university can list unused resources for daily/weekly paid rental or free borrowing, backed by:
- **University Email Verification** (e.g. `@university.edu`)
- **Authoritative Backend Pricing & Quote Calculator**
- **Refundable Security Deposits**
- **Automatic Overdue Detection & Late Fee Accrual**
- **Transparent, Algorithmic Campus Trust Scoring (0–100)**
- **In-App Messaging & Notifications**
- **Moderator & Dispute Resolution Dashboard**

---

## 2. Technology Stack

This application was intentionally built with a clean, beginner-to-intermediate architecture designed to be understood and confidently explained in technical interviews:

| Layer | Technology | Purpose |
|---|---|---|
| **Backend** | Python 3.10+ & **FastAPI** | High-performance asynchronous REST API framework with automatic Swagger docs |
| **Database** | **PostgreSQL** & **SQLAlchemy ORM** | Relational database with SQL schema normalization and relationship mapping |
| **Local Dev** | **SQLite** (Auto-fallback) | Instant zero-configuration local database so code runs out-of-the-box |
| **Frontend** | **HTML5, Modern CSS3, Vanilla JS** | Pure, lightweight frontend using browser-native **Fetch API** (No React/Node complexity) |
| **Auth** | **JWT (JSON Web Tokens) & bcrypt** | Industry-standard password hashing and stateless token-based authorization |
| **Validation**| **Pydantic v2** | Strict schema validation, type safety, and automatic HTTP error formatting |

### Technologies Deliberately Excluded
To keep the project clean, understandable, and interview-ready, we avoided over-engineering:
- **No React / Next.js / Node.js** (All frontend is plain HTML/CSS/JS with Fetch API)
- **No Redis / Celery / RabbitMQ / Kafka** (State checks and overdue calculations run synchronously on endpoint access)
- **No WebSockets** (Clean REST polling for in-app messages and notifications)
- **No complicated payment gateways** (Demo Payment calculation clearly labeled and ready for Stripe/Razorpay)

---

## 3. Core Architecture

```text
Browser Client (HTML5 / Modern CSS3 / Vanilla JS)
       │
       ▼ (HTTP Requests with JWT Bearer Token)
Fetch API Wrapper (`frontend/js/api.js`)
       │
       ▼ (JSON REST Endpoints: GET, POST, PUT, DELETE)
FastAPI Application (`app/main.py`)
       │
       ├─► Pydantic Schemas (`app/schemas/`) ──> Input Validation & Sanitization
       ├─► JWT & bcrypt Auth (`app/auth.py`) ──> Token decoding & Role Guard
       ├─► Business Logic Services (`app/services/`)
       │       ├─ rental_service.py (Quotes, Late fees, Overdue sync)
       │       ├─ trust_service.py  (Trust score engine 0-100)
       │       └─ notification_service.py
       │
       ▼ (Object-Relational Mapping Queries & Transactions)
SQLAlchemy ORM (`app/database.py` & `app/models/`)
       │
       ▼
PostgreSQL / SQLite Database (`users`, `listings`, `rentals`, `ratings`, `reports`, etc.)
```

---

## 4. Key Features

1. **Student Registration & University Domain Validation**:
   - Only emails matching the configured university domain (e.g. `@university.edu`) can register.
   - All students start with a baseline trust score of `50/100`.
2. **Marketplace & Resource Discovery**:
   - Multi-attribute filtering: Category, Item Condition, Paid vs Free Borrow, Campus Pickup Location, Department, and Price Range.
   - Real-time search across title, description, and tags.
   - Sorting: Newest, Price (Low to High), Price (High to Low), Highest Owner Rating.
3. **Item Listing & Local File Uploads**:
   - Students list resources with daily price, weekly discount rate, security deposit, max duration, and campus meetup spot.
   - Images are uploaded locally to `/uploads/` (swappable with AWS S3 without altering API contracts).
4. **Authoritative Rental System & Lifecycle**:
   - **State Machine:** `REQUESTED` ➔ `APPROVED` ➔ `ACTIVE` ➔ `RETURN_REQUESTED` ➔ `COMPLETED` (also `REJECTED`, `OVERDUE`, `DISPUTED`).
   - Prices and quotes are calculated strictly on the backend via `POST /api/rentals/quote`—the frontend never dictates the price.
5. **Security Deposit Management**:
   - Tracks deposit status through `HELD`, `REFUNDABLE`, `REFUNDED`, `PARTIALLY_DEDUCTED`, or `DEDUCTED`.
6. **Automatic Overdue Detection & Late Fee Accrual**:
   - Automatically synchronizes rentals whose end date has passed (`late_days * daily_late_fee`) when endpoints are hit, eliminating background queue complexity.
   - Live visual countdown tags (`4 days remaining`, `Due tomorrow`, `Due today`, `Overdue by 2 days`).
7. **Transparent Campus Trust Score Engine (0 to 100)**:
   - `+5 pts`: On-time completed rental
   - `+3 pts`: Positive review (4 or 5 stars)
   - `+2 pts`: Clean return
   - `-5 pts`: Late return
   - `-3 pts`: Cancelled approved rental
   - `-10 pts`: Confirmed damage or dispute
   - Tiers: *Highly Reliable (80-100)*, *Reliable (60-79)*, *Building Trust (40-59)*, *Low Trust (0-39)*.
8. **Peer Reviews & Ratings**:
   - 1–5 stars and text feedback after rental completion.
   - Prevents duplicate reviews for the same rental.
9. **In-App Messaging & Notifications**:
   - Lightweight peer-to-peer message threads with listing context.
   - Bell notification dropdown with live unread counter badge.
10. **Semester Mode**:
    - Curated "Popular This Semester" items featured on the homepage.
11. **Admin Moderation Dashboard**:
    - Platform KPIs, student account suspension toggle, listing removal, and dispute resolution.

---

## 5. Project Directory Structure

```text
Uniloop/
│
├── app/
│   ├── main.py                  # FastAPI app entry point, route mounts & static files
│   ├── database.py              # SQLAlchemy engine, SessionLocal, Base, get_db dependency
│   ├── auth.py                  # JWT encode/decode, bcrypt hash/verify, get_current_user
│   ├── utils.py                 # University email validator, upload handler
│   │
│   ├── models/                  # SQLAlchemy ORM database models
│   │   ├── user.py              # User table (roles, trust score, average rating)
│   │   ├── listing.py           # Listings & ListingImage tables
│   │   ├── rental.py            # RentalRequest & Rental tables
│   │   ├── rating.py            # Ratings & Reviews table (with unique constraints)
│   │   ├── message.py           # Peer-to-peer message table
│   │   ├── notification.py      # In-app notifications table
│   │   ├── wishlist.py          # Bookmarked items table
│   │   └── report.py            # Dispute & moderation reports table
│   │
│   ├── schemas/                 # Pydantic request/response schemas
│   │   ├── user.py
│   │   ├── listing.py
│   │   ├── rental.py
│   │   ├── rating.py
│   │   ├── message.py
│   │   ├── notification.py
│   │   ├── wishlist.py
│   │   └── report.py
│   │
│   ├── routes/                  # Modular REST API endpoints
│   │   ├── auth.py              # /api/auth (register, login, me)
│   │   ├── users.py             # /api/users (profile & reputation)
│   │   ├── listings.py          # /api/listings (CRUD, search, filters)
│   │   ├── rentals.py           # /api/rentals & /api/rental-requests
│   │   ├── ratings.py           # /api/ratings
│   │   ├── messages.py          # /api/messages
│   │   ├── notifications.py     # /api/notifications
│   │   ├── wishlist.py          # /api/wishlist
│   │   ├── reports.py           # /api/reports
│   │   └── admin.py             # /api/admin (stats, user moderation, reports)
│   │
│   └── services/                # Encapsulated business logic
│       ├── rental_service.py    # Authoritative quotes, late fees, countdowns, overdue sync
│       ├── trust_service.py     # Rule-based trust score calculator (0-100)
│       └── notification_service.py # In-app notification dispatcher
│
├── frontend/                    # Vanilla HTML5, CSS3, JavaScript frontend
│   ├── index.html               # Landing page (Hero, Categories, How it works, Semester items)
│   ├── login.html               # Login page with 1-click Demo credentials
│   ├── register.html            # University registration form
│   ├── marketplace.html         # Browse & filter listings with search
│   ├── listing.html             # Item details, image gallery, quote estimator modal
│   ├── create-listing.html      # Create / edit item form with upload
│   ├── dashboard.html           # Student dashboard with countdown badges
│   ├── rentals.html             # My Rentals tabs (Borrowed, Lent, Completed, Overdue)
│   ├── messages.html            # In-app peer messaging
│   ├── wishlist.html            # Saved resources grid
│   ├── profile.html             # Public / Private profile with trust score dial
│   ├── admin.html               # Admin Dashboard (Platform stats, moderation)
│   │
│   ├── css/
│   │   └── styles.css           # Modern startup SaaS UI styling
│   └── js/
│       ├── api.js               # Fetch API wrapper with JWT & toast notifications
│       └── navbar.js            # Universal navigation bar & unread notification poller
│
├── uploads/                     # Uploaded resource images & generated SVGs
├── seed.py                      # Demo data generator (12 students, 1 admin, 24 items, active rentals)
├── test_api.py                  # 14-step automated test suite verifying all routes & business logic
├── requirements.txt             # Clean Python dependencies
├── .env.example                 # Environment configuration template
└── README.md                    # Complete documentation & interview preparation guide
```

---

## 6. Installation & Setup

### Prerequisites
- Python 3.10+ (Tested on Python 3.13)
- Git (Optional)
- PostgreSQL (Optional; local SQLite fallback works immediately out-of-the-box!)

### Step 1: Clone or Navigate to the Project
```bash
cd "c:\Users\Vinay\OneDrive\Desktop\DREAM\vinaysingh projects"
```

### Step 2: Create and Activate Virtual Environment
On Windows (PowerShell):
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

On Linux / macOS:
```bash
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install Dependencies
```bash
pip install -r requirements.txt
```

---

## 7. Database Configuration

Uniloop supports both **PostgreSQL** (Production / Standard) and **SQLite** (Local Zero-Config).

### Option A: Instant Local SQLite (Default)
No setup required! The `.env` file already contains:
```env
DATABASE_URL=sqlite:///./campusshare.db
```
When you run the seed script or start the server, `campusshare.db` is created automatically with all 10 tables.

### Option B: Setting up PostgreSQL
If you want to run PostgreSQL:
1. Open PostgreSQL CLI or pgAdmin:
   ```sql
   CREATE DATABASE campusshare_db;
   ```
2. Update your `.env` file:
   ```env
   DATABASE_URL=postgresql://postgres:yourpassword@localhost:5432/campusshare_db
   ```
3. Run `python seed.py` to initialize tables and load demo records.

---

## 8. Seeding Demo Data

To load 12 students, 1 administrator, 24 realistic listings, active rentals with countdowns, overdue rentals with late fees, ratings, notifications, and sample messages:

```bash
python seed.py
```

---

## 9. Running the Application

Start the FastAPI server using Uvicorn:

```bash
uvicorn app.main:app --reload --port 8000
```

Open your browser and visit:
- **Application Web UI:** [http://localhost:8000](http://localhost:8000)
- **FastAPI Interactive API Docs (Swagger):** [http://localhost:8000/docs](http://localhost:8000/docs)
- **Alternative API Docs (ReDoc):** [http://localhost:8000/redoc](http://localhost:8000/redoc)

---

## 10. Demo Credentials (For Interviews & Presentations)

On `http://localhost:8000/login.html`, click any of the instant demo buttons to auto-fill credentials:

| Account | Email | Password | Role & Highlights |
|---|---|---|---|
| **Student A (Sarah Chen)** | `sarah@university.edu` | `Password123!` | Electronics, 3rd Year • Trust: **94/100** • Owner of CLRS textbook, Arduino kit |
| **Student B (Alex Rivera)** | `alex@university.edu` | `Password123!` | Mechanical, 2nd Year • Trust: **88/100** • Active borrower |
| **Student C (Priya Sharma)** | `priya@university.edu` | `Password123!` | Electronics, 4th Year • Trust: **92/100** • Owner of Oscilloscope |
| **Administrator** | `admin@university.edu` | `AdminPassword123!` | Staff Moderator • Full admin dashboard access |

---

## 11. Complete Demo Flow (Step-by-Step Interview Walkthrough)

To give an impressive live demo to recruiters or professors:

1. **Sign In as Student A (Sarah Chen):**
   - Click the 1-click login button for Sarah on `/login.html`.
   - View Sarah's student dashboard (`/dashboard.html`): observe her 94/100 Trust Score badge, active items, and active rental countdowns.
2. **List a New Resource:**
   - Click **+ List an Item** (`/create-listing.html`).
   - Enter title (e.g., "Engineering Drawing Kit"), choose category, condition, pickup location (Main Library), and daily price (₹30).
   - Publish the listing. Observe instant redirection to the live detail view.
3. **Log Out & Sign In as Student B (Alex Rivera):**
   - Sign out via profile menu, then log in as Alex.
4. **Discover Resource & Interactive Pricing Quote:**
   - Go to `/marketplace.html`. Filter by category or search "Drawing".
   - Open the item page (`/listing.html`).
   - Change rental dates in the quote box: observe how the duration, rental fee, security deposit, and total update in real-time via the backend quote API (`POST /api/rentals/quote`).
5. **Submit Rental Request:**
   - Click **Request to Rent**, enter an optional pickup note, and submit.
6. **Approve Request as Student A:**
   - Log back in as Sarah.
   - Open `/rentals.html` ➔ switch to **Items Lent** tab.
   - See the incoming request from Alex with dates and message. Click **Approve Request**.
   - Notice the item transitions to `ACTIVE`, deposit transitions to `HELD`, and the listing is marked rented in the marketplace.
7. **Initiate Return as Student B:**
   - Log in as Alex. Visit `/rentals.html` ➔ **Items Borrowed** tab.
   - See the live countdown badge.
   - Click **↩ Return Item**. Choose "Returned in good condition" and submit.
   - Notice deposit status changes to `REFUNDABLE`.
8. **Finalize Return & Rate Peer:**
   - Log back in as Sarah. Click **✓ Confirm & Release Deposit**.
   - The rental moves to `COMPLETED` and deposit status becomes `REFUNDED`.
   - Click **⭐ Leave Review**, pick 5 stars, write a comment, and submit.
9. **Verify Trust Score Boost:**
   - Open `/profile.html`: observe updated average rating and increased trust score!
10. **Explore Admin Dashboard:**
    - Log in as `admin@university.edu` and visit `/admin.html`.
    - Review platform KPIs (total students, listings, value shared).
    - Inspect students table, toggle suspension, and review open dispute reports.

---

## 12. Automated Verification

Run the comprehensive 14-step automated test suite:

```bash
python test_api.py
```

Expected output:
```text
[PASS] Health Check Passed
[PASS] University Domain Restriction Verified
[PASS] Student Registration & Baseline Trust Score (50) Verified
[PASS] Login & JWT Issuance Verified
[PASS] /api/auth/me Protected Endpoint Verified
[PASS] Listings Search Verified
[PASS] Listings Filter by Category Verified
[PASS] Listing Created Successfully (ID: ...)
[PASS] Backend Authoritative Rental Quote Calculation Verified
[PASS] Rental Request Submitted by Borrower
[PASS] Rental Approved & Active State Initiated
[PASS] Item Return Requested by Borrower (Deposit Marked REFUNDABLE)
[PASS] Rental Marked COMPLETED & Deposit Fully Released
[PASS] Peer Review Submitted & Processed
[PASS] Duplicate Review Prevention Verified
[PASS] In-App Notification Feed Verified
[PASS] Wishlist Bookmark & Removal Verified
[PASS] Admin Platform KPIs Verified
[PASS] Admin User Account Suspension Verified

==========================================
 ALL 14 AUTOMATED TESTS PASSED CLEANLY! 
==========================================
```

---

## 13. Important Business Logic (Interview Ready)

These are the core algorithms you should be ready to discuss during technical interviews:

### A. Rental Price Calculation (`app/services/rental_service.py`)
```python
def calculate_rental_quote(price_per_day, price_per_week, security_deposit, rental_type, start_date, end_date):
    days = max(1, (end_date - start_date).days)
    if rental_type == "free":
        rental_cost = 0.0
        deposit = 0.0
    else:
        # If duration >= 7 days and weekly rate is provided, give student the best rate
        if price_per_week > 0 and days >= 7:
            weeks = days // 7
            rem_days = days % 7
            bundled_cost = (weeks * price_per_week) + (rem_days * price_per_day)
            daily_cost = days * price_per_day
            rental_cost = round(min(bundled_cost, daily_cost), 2)
        else:
            rental_cost = round(days * price_per_day, 2)
        deposit = round(security_deposit, 2)

    total_amount = round(rental_cost + deposit, 2)
    return { "days": days, "rental_cost": rental_cost, "security_deposit": deposit, "total_amount": total_amount }
```
*Why this matters in interviews:* Explain that pricing is **authoritative on the backend**. A malicious user could edit HTML/JS in browser DevTools, but FastAPI re-calculates all sums before storing in the database.

### B. Late Fee Calculation (`app/services/rental_service.py`)
```python
def calculate_late_fee(end_date, return_date=None, daily_late_fee=25.0):
    compare_date = return_date if return_date else date.today()
    if compare_date > end_date:
        late_days = (compare_date - end_date).days
        late_fee = round(late_days * daily_late_fee, 2)
        return late_days, late_fee
    return 0, 0.0
```
*Why this matters in interviews:* Explain how **overdue checking runs dynamically** whenever rental endpoints are queried (`sync_overdue_rentals(db)`). This prevents needing heavy background worker infrastructure like Celery or Redis for a student project while remaining 100% accurate.

### C. Campus Trust Score Algorithm (`app/services/trust_service.py`)
- Starting baseline: **50 / 100**
- Bounded strictly: `0 <= trust_score <= 100`
- Adjustments:
  - `+5` for on-time completed rental
  - `+3` for receiving 4 or 5-star rating
  - `+2` for clean return submission
  - `-5` for late return
  - `-3` for cancelled approved rental
  - `-10` for confirmed damage report or dispute

---

## 14. What I Should Understand Before Explaining This Project in an Interview

Be prepared to explain these foundational concepts:

### 1. SQL & PostgreSQL Basics
- **Tables & Records:** How data is stored in rectangular rows and columns.
- **Primary Key (PK):** A unique identifier for every record (e.g., `users.id`, `listings.id`).
- **Foreign Key (FK):** A column in one table referencing the Primary Key in another table (e.g., `listings.owner_id -> users.id`, `rentals.listing_id -> listings.id`). Enforces referential integrity.
- **SQL JOINs:** Combining records from two or more tables. For example, querying a listing and joining the `users` table on `listings.owner_id == users.id` to show the owner's department and rating without duplicating data.
- **Database Normalization:** Why we do NOT store `owner_name` directly in `listings` (3rd Normal Form). If the user updates their name, it automatically reflects everywhere.

### 2. SQLAlchemy ORM (Object-Relational Mapping)
- **Why ORM?** Allows writing Python classes and objects (`User`, `Listing`) instead of raw SQL strings, providing type safety, SQL injection protection, and database portability (switching between PostgreSQL and SQLite without changing code).
- **Session Lifecycle:** `SessionLocal()` creates a unit of work. `db.commit()` commits the SQL transaction; `db.rollback()` cancels if an exception occurs; `db.close()` releases the connection back to the pool.
- **FastAPI `Depends(get_db)`:** A generator that yields a database session for each incoming HTTP request and guarantees it closes when the request ends.

### 3. REST API Design & HTTP
- **Statelessness:** The server does not store user session state in server memory; every request contains everything necessary (the JWT token in the `Authorization: Bearer <token>` header).
- **HTTP Methods:**
  - `GET`: Retrieve resources (e.g., `GET /api/listings`, `GET /api/rentals`)
  - `POST`: Create a new resource (e.g., `POST /api/rental-requests`, `POST /api/ratings`)
  - `PUT`: Update/replace a resource or state (e.g., `PUT /api/rentals/{id}/return`)
  - `DELETE`: Remove a resource (e.g., `DELETE /api/listings/{id}`)
- **HTTP Status Codes:**
  - `200 OK`: Request succeeded
  - `201 Created`: Resource successfully created
  - `400 Bad Request`: Validation failure (e.g., end date before start date)
  - `401 Unauthorized`: Missing or invalid JWT token
  - `403 Forbidden`: Authenticated user lacks permission (e.g., trying to edit someone else's listing)
  - `404 Not Found`: Resource ID does not exist

### 4. Authentication & Security
- **Password Hashing:** Passwords should NEVER be stored in plain text. `bcrypt` generates a unique random salt and runs repeated one-way hashing rounds. Even if two users have the same password, their hashes are completely different.
- **JWT (JSON Web Token):**
  - Composed of 3 parts: `Header.Payload.Signature`
  - Signed using a secret key with HMAC-SHA256 (`HS256`).
  - Contains claims: `sub` (user ID), `email`, `role`, and `exp` (expiration timestamp).
  - The client stores the token in `localStorage` and includes it in `Authorization: Bearer <token>`.

### 5. Frontend & Fetch API
- **Vanilla JavaScript Fetch API:** Modern standard for asynchronous HTTP requests returning Promises (`async/await`).
- **DOM Manipulation:** Dynamically updating UI cards, modal dialogs, and countdown tags without full-page reloads.
- **Toast Notifications & Modals:** Provides feedback on every user action.

---

## 15. License & Credits

Built as an interview-ready full-stack portfolio project for university students.  
Created with Python, FastAPI, PostgreSQL, SQLAlchemy, HTML5, CSS3, and JavaScript.
