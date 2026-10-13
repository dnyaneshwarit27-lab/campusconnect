# CampusConnect — College Events & Hackathon Hub

> **Discover events · Connect with coordinators · Register instantly · Scan QR to attend**
> **Real Data Only · Zero Dummy Records · 100% Dynamic · MongoDB Atlas Cloud Ready**

---

## 🎯 Overview
**CampusConnect** is a College Events & Hackathon Hub built with **Python, Django 6.1, and MongoDB Atlas**. It eliminates WhatsApp group chaos, scattered social media flyers, and cluttered college bulletin boards by providing a centralized platform where students discover verified events, coordinators manage registrations, and physical attendance is marked in real time using in-browser camera QR scanners.

---

## 🛠️ Final Tech Stack

| Layer | Technology | Details |
|---|---|---|
| **Backend** | **Python + Django 6.1** | Business logic, authentication, QR generation, Q&A, and coordinator workflows |
| **Database** | **MongoDB Atlas** | Cloud collections for actual users, events, registrations, teams, attendance, queries, and feedback |
| **Frontend** | **Django Templates + HTML5 + CSS3 + Bootstrap 5 + JS** | Responsive layout, glassmorphic dark theme, dynamic counters, and empty states |
| **QR System** | **Python `qrcode` + JS `html5-qrcode`** | Event poster QR codes, unique student UUID entry passes, and camera scanner |
| **Version Control** | **Git + GitHub** | Clean repository configuration, `.gitignore`, and branch workflows |
| **Deployment** | **Render** | `render.yaml`, `build.sh`, `Procfile`, and environment variable configuration |

---

## 🍃 MongoDB Atlas Cloud Collections

All data in CampusConnect is dynamic and mapped across 8 core collections:

| Collection | Stored Real Data |
|---|---|
| `users` | Registered students, coordinators, and administrators |
| `events` | Actual campus events, hackathons, and workshops published by coordinators |
| `registrations` | Confirmed student registrations with unpredictable UUID pass tokens |
| `teams` | Hackathon teams, project ideas, and student member rosters |
| `event_questions` | Student questions and coordinator verified answers |
| `attendance` | Real-time QR camera scan verified entrance check-ins |
| `announcements` | Urgent notifications, venue changes, and reporting updates |
| `feedback` | Post-event attendee ratings and suggestions |

---

## 🚫 Zero Dummy Data Architecture

In accordance with strict production requirements:
- **No hardcoded fake events or mock cards:** When the database is fresh, the system presents clean, purposeful empty states inviting coordinators to publish the first event.
- **No fake attendees or synthetic numbers:** All counters (*Live Events*, *Passes Issued*, *QR Verified*) are calculated live from real records in the database.
- **Real User Creation:** Users sign up through the registration portal as **Students** (to register and get passes) or **Event Coordinators** (to host events and scan tickets).

---

## ⚡ Connecting Your MongoDB Atlas Cluster

### Step 1: Obtain Connection String from MongoDB Atlas
1. Log in to [MongoDB Atlas](https://cloud.mongodb.com/).
2. Click **Connect** on your Database Cluster -> Choose **Drivers** (Python).
3. Copy your connection string:
   ```
   mongodb+srv://<username>:<password>@cluster0.xxxxx.mongodb.net/campusconnect?retryWrites=true&w=majority
   ```

### Step 2: Configure Local `.env`
In the project root, open `.env` and set your URI:
```env
SECRET_KEY=django-insecure-g%pw$323u_(of9l3bd#735-^g=an0a2e+uazvk0j2silw(a9*x
DEBUG=True

MONGODB_URI=mongodb+srv://<username>:<password>@cluster0.xxxxx.mongodb.net/campusconnect?retryWrites=true&w=majority
MONGODB_DB_NAME=campusconnect
```

### Step 3: Check Live Diagnostic Endpoint
Visit:
```
http://127.0.0.1:8000/mongodb-status/
```
This returns live JSON diagnostics verifying your cluster connection and current document counts for all 8 collections.

---

## 🚀 Running the Project Locally

```powershell
# 1. Install dependencies
pip install -r requirements.txt

# 2. Run database migrations
python manage.py migrate

# 3. Setup standard categories
python manage.py setup_categories

# 4. Start Django server
python manage.py runserver 0.0.0.0:8000
```
Open **[http://127.0.0.1:8000/](http://127.0.0.1:8000/)** in your browser.

---

## 🌐 Deploying to Render

This repository is ready for 1-click deployment to **Render**:

1. Push your project to **GitHub**.
2. In the [Render Dashboard](https://dashboard.render.com/):
   - Click **New** -> **Web Service**.
   - Connect your GitHub repository.
3. Render will automatically detect `render.yaml` or you can manually configure:
   - **Environment:** `Python`
   - **Build Command:** `./build.sh`
   - **Start Command:** `gunicorn campusconnect.wsgi:application`
4. Add your Environment Variables in Render:
   - `SECRET_KEY`: (generate a secure key)
   - `MONGODB_URI`: (your MongoDB Atlas connection string)
   - `MONGODB_DB_NAME`: `campusconnect`
   - `DEBUG`: `False`
5. Click **Deploy Web Service**!
