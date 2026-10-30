import os
from flask import Flask, render_template_string, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from functools import wraps

# ============================================================
# APP CONFIG
# ============================================================
app = Flask(__name__)

# 1. Load the Secret Key
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'fallback-dev-key')

# 2. Read DATABASE_URL and force psycopg2 driver safely
database_url = os.environ.get('DATABASE_URL', '')

if database_url:
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)
    if database_url.startswith("postgresql://"):
        database_url = database_url.replace("postgresql://", "postgresql+psycopg2://", 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
else:
    import os
from flask import Flask, render_template_string, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from functools import wraps

# ============================================================
# APP CONFIG
# ============================================================
app = Flask(__name__)

# 1. Load the Secret Key
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'fallback-dev-key')

# 2. Read DATABASE_URL and force psycopg2 driver safely
database_url = os.environ.get('DATABASE_URL', '')

if database_url:
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)
    if database_url.startswith("postgresql://"):
        database_url = database_url.replace("postgresql://", "postgresql+psycopg2://", 1)
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///local_dev.db'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize DB
db = SQLAlchemy(app)

# ============================================================
# MODELS
# ============================================================

class Room(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    sharing = db.Column(db.String(80), nullable=False)
    floor = db.Column(db.String(80), nullable=False)
    price = db.Column(db.Integer, nullable=False)
    duration = db.Column(db.String(60))
    beds = db.Column(db.Integer, default=10)
    available_beds = db.Column(db.Integer, default=10)
    description = db.Column(db.Text)
    icon = db.Column(db.String(50), default='fa-bed')
    is_active = db.Column(db.Boolean, default=True)


class Staff(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(80), nullable=False)
    qualification = db.Column(db.String(120))
    experience = db.Column(db.String(50))
    bio = db.Column(db.Text)
    icon = db.Column(db.String(50), default='fa-user-tie')
    is_active = db.Column(db.Boolean, default=True)


class Booking(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    guest_name = db.Column(db.String(100), nullable=False)
    occupation = db.Column(db.String(100))
    email = db.Column(db.String(120), nullable=False)
    phone = db.Column(db.String(20), nullable=False)
    room_id = db.Column(db.Integer, db.ForeignKey('room.id'))
    message = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='pending')
    room = db.relationship('Room', backref='bookings')


class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class Admin(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)


class SiteSetting(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(80), unique=True, nullable=False)
    value = db.Column(db.Text)
    label = db.Column(db.String(200))
    group = db.Column(db.String(60), default='general')


class Feature(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    icon = db.Column(db.String(50), default='fa-star')
    title = db.Column(db.String(120), nullable=False)
    description = db.Column(db.Text)
    sort_order = db.Column(db.Integer, default=0)


class Testimonial(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(120))
    avatar = db.Column(db.String(4))
    stars = db.Column(db.Integer, default=5)
    content = db.Column(db.Text, nullable=False)
    sort_order = db.Column(db.Integer, default=0)


# ============================================================
# HELPERS
# ============================================================
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'admin_id' not in session:
            flash('Please login as admin first.', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated


def all_settings():
    return {s.key: s.value for s in SiteSetting.query.all()}


# ============================================================
# BASE TEMPLATE
# ============================================================
BASE_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{% block title %}{{ site.site_name or 'Kant PG' }}{% endblock %}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=Merriweather:wght@700;900&display=swap" rel="stylesheet">
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css">
<style>
:root{
  --blue-900:#0a2540;--blue-800:#0d2f52;--blue-700:#10406f;--blue-600:#1a5fa8;
  --blue-500:#2874c4;--blue-400:#5b9de0;--blue-100:#e8f1fa;--blue-50:#f4f9ff;
  --white:#fff;--gray-50:#f7fafd;--gray-100:#eef2f7;--gray-200:#dfe6ee;
  --gray-500:#6b7c93;--gray-700:#3d4d63;--accent:#ffb703;
  --shadow-sm:0 2px 8px rgba(10,37,64,.06);--shadow-md:0 8px 24px rgba(10,37,64,.08);
  --shadow-lg:0 16px 40px rgba(10,37,64,.12);--radius:14px;--radius-lg:20px;
}
*{margin:0;padding:0;box-sizing:border-box}
html{scroll-behavior:smooth}
body{font-family:'Plus Jakarta Sans',-apple-system,sans-serif;background:var(--white);color:var(--gray-700);line-height:1.6;-webkit-font-smoothing:antialiased}
h1,h2,h3,h4{font-family:'Merriweather',serif;color:var(--blue-900);letter-spacing:-.3px;line-height:1.25}
a{color:inherit;text-decoration:none}
.container{max-width:1200px;margin:0 auto;padding:0 28px}

.topbar{background:var(--blue-900);color:#c9d9eb;font-size:.85rem;padding:9px 0}
.topbar-inner{display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px}
.topbar a{color:#c9d9eb;margin-left:20px;transition:.2s}
.topbar a:hover{color:var(--white)}
.topbar i{color:var(--blue-400);margin-right:6px}

.navbar{background:var(--white);border-bottom:1px solid var(--gray-100);position:sticky;top:0;z-index:100;box-shadow:var(--shadow-sm)}
.nav-inner{display:flex;justify-content:space-between;align-items:center;padding:16px 0;flex-wrap:wrap;gap:16px}
.brand{display:flex;align-items:center;gap:12px;text-decoration:none}
.brand-mark{width:44px;height:44px;border-radius:12px;background:linear-gradient(135deg,var(--blue-600),var(--blue-800));display:flex;align-items:center;justify-content:center;color:var(--white);font-weight:800;font-size:1.3rem;box-shadow:var(--shadow-sm)}
.brand-text{display:flex;flex-direction:column;line-height:1.15}
.brand-text b{font-family:'Merriweather',serif;font-size:1.25rem;color:var(--blue-900);font-weight:900}
.brand-text span{font-size:.72rem;color:var(--gray-500);letter-spacing:1.5px;text-transform:uppercase;font-weight:600}
.nav-links{display:flex;gap:2rem;list-style:none;align-items:center;flex-wrap:wrap}
.nav-links a{font-weight:600;color:var(--gray-700);font-size:.95rem;transition:.2s;position:relative}
.nav-links a:hover{color:var(--blue-600)}
.nav-links a.active{color:var(--blue-600)}
.nav-links a.active::after{content:'';position:absolute;left:0;right:0;bottom:-22px;height:3px;background:var(--blue-600);border-radius:3px 3px 0 0}

.btn{display:inline-flex;align-items:center;gap:8px;background:var(--blue-600);color:var(--white);padding:13px 28px;border-radius:10px;font-weight:600;border:none;cursor:pointer;font-size:.95rem;transition:.25s;font-family:inherit;box-shadow:0 4px 14px rgba(40,116,196,.28)}
.btn:hover{background:var(--blue-700);transform:translateY(-2px);box-shadow:0 6px 18px rgba(40,116,196,.35)}
.btn-outline{background:transparent;border:2px solid var(--blue-600);color:var(--blue-600);box-shadow:none}
.btn-outline:hover{background:var(--blue-600);color:var(--white);box-shadow:0 4px 14px rgba(40,116,196,.28)}
.btn-lg{padding:16px 36px;font-size:1.05rem}
.btn-sm{padding:9px 20px;font-size:.85rem}
.btn-white{background:var(--white);color:var(--blue-700)}
.btn-white:hover{background:var(--blue-50);color:var(--blue-800)}
.btn-danger{background:#c0392b}
.btn-danger:hover{background:#a93226}

.hero{background:linear-gradient(135deg,var(--blue-50) 0%,var(--white) 100%);padding:72px 0 88px;position:relative;overflow:hidden}
.hero::before{content:'';position:absolute;top:-120px;right:-120px;width:460px;height:460px;background:radial-gradient(circle,rgba(40,116,196,.09),transparent 70%);border-radius:50%}
.hero::after{content:'';position:absolute;bottom:-160px;left:-100px;width:380px;height:380px;background:radial-gradient(circle,rgba(40,116,196,.06),transparent 70%);border-radius:50%}
.hero-grid{display:grid;grid-template-columns:1.1fr .9fr;gap:56px;align-items:center;position:relative;z-index:2}
@media(max-width:900px){.hero-grid{grid-template-columns:1fr;gap:40px}}
.hero-eyebrow{display:inline-flex;align-items:center;gap:8px;background:var(--blue-100);color:var(--blue-700);padding:8px 18px;border-radius:40px;font-size:.82rem;font-weight:700;letter-spacing:.5px;text-transform:uppercase;margin-bottom:24px}
.hero-eyebrow i{font-size:.8rem}
.hero h1{font-size:3.3rem;font-weight:900;margin-bottom:22px;color:var(--blue-900)}
.hero h1 .accent{color:var(--blue-600);position:relative}
.hero h1 .accent::after{content:'';position:absolute;left:0;right:0;bottom:6px;height:12px;background:rgba(255,183,3,.28);z-index:-1;border-radius:4px}
.hero p{font-size:1.13rem;color:var(--gray-500);margin-bottom:34px;max-width:520px;line-height:1.7}
.hero-actions{display:flex;gap:14px;flex-wrap:wrap}
.hero-trust{display:flex;gap:32px;margin-top:44px;padding-top:32px;border-top:1px solid var(--gray-200);flex-wrap:wrap}
.trust-item{display:flex;flex-direction:column}
.trust-item b{font-family:'Merriweather',serif;font-size:1.8rem;color:var(--blue-700);font-weight:900;line-height:1}
.trust-item span{font-size:.82rem;color:var(--gray-500);text-transform:uppercase;letter-spacing:.8px;margin-top:6px;font-weight:600}

.hero-visual{position:relative;background:var(--white);border-radius:var(--radius-lg);padding:32px;box-shadow:var(--shadow-lg);border:1px solid var(--gray-100)}
.hero-visual::before{content:'';position:absolute;inset:-14px -14px auto auto;width:120px;height:120px;background:linear-gradient(135deg,var(--blue-600),var(--blue-400));border-radius:20px;z-index:-1;opacity:.15}
.hv-header{display:flex;justify-content:space-between;align-items:center;margin-bottom:24px}
.hv-header span{font-size:.78rem;text-transform:uppercase;letter-spacing:1.2px;color:var(--gray-500);font-weight:700}
.hv-badge{background:#e6f7ec;color:#1e7a3f;padding:5px 12px;border-radius:20px;font-size:.72rem;font-weight:700}
.hv-course{display:flex;gap:16px;padding:16px 0;border-bottom:1px solid var(--gray-100);align-items:center}
.hv-course:last-of-type{border-bottom:none}
.hv-icon{width:52px;height:52px;border-radius:14px;flex-shrink:0;background:var(--blue-50);color:var(--blue-600);display:flex;align-items:center;justify-content:center;font-size:1.3rem}
.hv-course b{display:block;color:var(--blue-900);font-family:'Plus Jakarta Sans',sans-serif;font-size:.95rem;font-weight:700}
.hv-course small{color:var(--gray-500);font-size:.82rem}
.hv-footer{margin-top:20px;padding-top:20px;border-top:1px solid var(--gray-100);text-align:center}
.hv-footer .btn{width:100%;justify-content:center}

.section{padding:88px 0}
.section-alt{background:var(--gray-50)}
.section-head{text-align:center;max-width:640px;margin:0 auto 56px}
.section-eyebrow{display:inline-block;color:var(--blue-600);font-weight:700;font-size:.82rem;letter-spacing:2px;text-transform:uppercase;margin-bottom:14px}
.section-head h2{font-size:2.4rem;margin-bottom:14px}
.section-head p{color:var(--gray-500);font-size:1.05rem}

.courses-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:26px}
.course-card{background:var(--white);border-radius:var(--radius-lg);padding:30px 26px;border:1px solid var(--gray-100);transition:.3s;position:relative;overflow:hidden}
.course-card::before{content:'';position:absolute;top:0;left:0;right:0;height:4px;background:linear-gradient(90deg,var(--blue-600),var(--blue-400));transform:scaleX(0);transform-origin:left;transition:.3s}
.course-card:hover{transform:translateY(-6px);box-shadow:var(--shadow-lg);border-color:var(--blue-100)}
.course-card:hover::before{transform:scaleX(1)}
.course-icon{width:58px;height:58px;border-radius:16px;background:linear-gradient(135deg,var(--blue-50),var(--blue-100));color:var(--blue-600);display:flex;align-items:center;justify-content:center;font-size:1.5rem;margin-bottom:22px}
.course-tag{position:absolute;top:22px;right:22px;background:var(--blue-100);color:var(--blue-700);padding:4px 12px;border-radius:20px;font-size:.72rem;font-weight:700;text-transform:uppercase;letter-spacing:.5px}
.course-card h3{font-size:1.35rem;margin-bottom:8px}
.course-meta{color:var(--gray-500);font-size:.88rem;margin-bottom:16px}
.course-card p{color:var(--gray-500);font-size:.92rem;margin-bottom:20px;min-height:52px}
.course-footer{display:flex;justify-content:space-between;align-items:center;padding-top:20px;border-top:1px solid var(--gray-100)}
.course-price{font-family:'Merriweather',serif;font-size:1.5rem;color:var(--blue-900);font-weight:900}
.course-price small{font-family:'Plus Jakarta Sans',sans-serif;font-size:.78rem;color:var(--gray-500);font-weight:500}
.seats{font-size:.82rem;color:var(--gray-500);margin-top:4px}
.seats b{color:#1e7a3f}

.features-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:24px}
.feature-card{background:var(--white);border-radius:var(--radius);padding:32px 26px;border:1px solid var(--gray-100);transition:.25s}
.feature-card:hover{border-color:var(--blue-400);box-shadow:var(--shadow-md)}
.feature-icon{width:54px;height:54px;border-radius:14px;background:var(--blue-50);color:var(--blue-600);display:flex;align-items:center;justify-content:center;font-size:1.35rem;margin-bottom:20px}
.feature-card h4{font-size:1.12rem;margin-bottom:10px}
.feature-card p{color:var(--gray-500);font-size:.92rem}

.faculty-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(260px,1fr));gap:26px}
.faculty-card{background:var(--white);border-radius:var(--radius-lg);padding:32px 26px;text-align:center;border:1px solid var(--gray-100);transition:.25s}
.faculty-card:hover{box-shadow:var(--shadow-lg);border-color:var(--blue-100)}
.faculty-avatar{width:88px;height:88px;border-radius:50%;margin:0 auto 20px;background:linear-gradient(135deg,var(--blue-500),var(--blue-700));color:var(--white);display:flex;align-items:center;justify-content:center;font-size:2rem;box-shadow:0 8px 20px rgba(40,116,196,.25)}
.faculty-card h4{font-size:1.15rem;margin-bottom:6px}
.faculty-card .subject{color:var(--blue-600);font-weight:700;font-size:.85rem;text-transform:uppercase;letter-spacing:1px;margin-bottom:14px}
.faculty-card p{color:var(--gray-500);font-size:.9rem;margin-bottom:14px}
.faculty-meta{display:flex;justify-content:center;gap:20px;padding-top:16px;border-top:1px solid var(--gray-100);font-size:.82rem;color:var(--gray-500)}
.faculty-meta i{color:var(--blue-600);margin-right:4px}

.testi-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:24px}
.testi-card{background:var(--white);border-radius:var(--radius-lg);padding:32px 28px;border:1px solid var(--gray-100);position:relative}
.testi-quote{font-size:2.5rem;color:var(--blue-100);font-family:Georgia,serif;line-height:1;position:absolute;top:16px;right:24px}
.testi-stars{color:var(--accent);margin-bottom:16px;font-size:.9rem}
.testi-card p{color:var(--gray-700);font-size:.95rem;line-height:1.7;margin-bottom:22px;font-style:italic}
.testi-author{display:flex;align-items:center;gap:14px}
.testi-avatar{width:44px;height:44px;border-radius:50%;background:var(--blue-100);color:var(--blue-700);display:flex;align-items:center;justify-content:center;font-weight:700}
.testi-author b{display:block;color:var(--blue-900);font-size:.95rem}
.testi-author small{color:var(--gray-500);font-size:.8rem}

.cta-banner{background:linear-gradient(135deg,var(--blue-800),var(--blue-600));border-radius:var(--radius-lg);padding:56px 48px;display:flex;justify-content:space-between;align-items:center;gap:32px;flex-wrap:wrap;color:var(--white);box-shadow:var(--shadow-lg)}
.cta-banner h2{color:var(--white);font-size:2rem;margin-bottom:10px}
.cta-banner p{color:#c9d9eb;font-size:1.05rem}

.form{display:flex;flex-direction:column;gap:16px}
.form input,.form textarea,.form select{padding:14px 16px;border-radius:10px;border:1.5px solid var(--gray-200);font-family:inherit;font-size:.95rem;background:var(--white);color:var(--gray-700);transition:.2s}
.form input:focus,.form textarea:focus,.form select:focus{outline:none;border-color:var(--blue-600);box-shadow:0 0 0 3px rgba(40,116,196,.1)}
.form label{font-size:.85rem;font-weight:700;color:var(--blue-900);margin-bottom:-8px}
.form-row{display:grid;grid-template-columns:1fr 1fr;gap:16px}
@media(max-width:600px){.form-row{grid-template-columns:1fr}}

.flash{padding:14px 20px;border-radius:10px;margin:20px 0;font-weight:600;font-size:.92rem;display:flex;align-items:center;gap:10px}
.flash.success{background:#e6f7ec;color:#1e7a3f;border-left:4px solid #1e7a3f}
.flash.error{background:#fde8e8;color:#a32424;border-left:4px solid #a32424}

.detail-card{display:grid;grid-template-columns:1fr 1.4fr;gap:40px;background:var(--white);border-radius:var(--radius-lg);padding:40px;border:1px solid var(--gray-100);margin:30px 0 60px;box-shadow:var(--shadow-md)}
@media(max-width:800px){.detail-card{grid-template-columns:1fr;padding:28px}}
.detail-left{background:linear-gradient(135deg,var(--blue-50),var(--blue-100));border-radius:var(--radius);display:flex;flex-direction:column;align-items:center;justify-content:center;padding:48px 24px;text-align:center}
.detail-left .big-icon{font-size:5rem;color:var(--blue-600);margin-bottom:20px}
.detail-left b{font-family:'Merriweather',serif;font-size:1.2rem;color:var(--blue-900)}

.auth-wrap{max-width:440px;margin:60px auto}
.auth-wrap h2{margin-bottom:8px}
.auth-wrap .sub{color:var(--gray-500);margin-bottom:24px;font-size:.95rem}
.card{background:var(--white);padding:32px;border-radius:var(--radius-lg);border:1px solid var(--gray-100);box-shadow:var(--shadow-sm)}

.stats-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:16px;margin-bottom:40px}
.stat-card{background:var(--white);border-radius:var(--radius);padding:24px;border:1px solid var(--gray-100);text-align:center;font-weight:600;color:var(--gray-500);font-size:.88rem;text-transform:uppercase;letter-spacing:.5px}
.stat-card span{display:block;font-family:'Merriweather',serif;font-size:2.4rem;font-weight:900;color:var(--blue-700);margin-bottom:4px;letter-spacing:-1px}

.table-wrap{overflow-x:auto;background:var(--white);border-radius:var(--radius);margin-bottom:40px;border:1px solid var(--gray-100);box-shadow:var(--shadow-sm)}
table{width:100%;border-collapse:collapse;font-size:.9rem}
th,td{padding:14px 18px;text-align:left;border-bottom:1px solid var(--gray-100);vertical-align:middle}
th{background:var(--blue-50);font-weight:700;color:var(--blue-900);font-size:.8rem;text-transform:uppercase;letter-spacing:.5px}
tr:last-child td{border-bottom:none}
tr:hover td{background:var(--gray-50)}
.tag{padding:5px 12px;border-radius:20px;font-size:.75rem;font-weight:700;text-transform:capitalize;display:inline-block}
.tag.pending{background:#fff3cd;color:#8a6d1c}
.tag.confirmed{background:#d4edda;color:#155724}
.tag.rejected{background:#f8d7da;color:#721c24}

.footer{background:var(--blue-900);color:#a8bdd6;padding:64px 0 0;margin-top:40px}
.footer-grid{display:grid;grid-template-columns:1.6fr 1fr 1fr 1.2fr;gap:48px;padding-bottom:48px}
@media(max-width:800px){.footer-grid{grid-template-columns:1fr 1fr;gap:32px}}
@media(max-width:480px){.footer-grid{grid-template-columns:1fr}}
.footer h5{color:var(--white);font-family:'Plus Jakarta Sans',sans-serif;font-size:.9rem;text-transform:uppercase;letter-spacing:1.5px;margin-bottom:20px;font-weight:700}
.footer p{font-size:.9rem;line-height:1.7;margin-bottom:10px}
.footer a{color:#a8bdd6;font-size:.9rem;display:block;margin-bottom:10px;transition:.2s}
.footer a:hover{color:var(--white);padding-left:4px}
.footer .brand-text b{color:var(--white)}
.footer .brand-text span{color:#a8bdd6}
.footer-bottom{border-top:1px solid rgba(255,255,255,.1);padding:24px 0;text-align:center;font-size:.85rem;color:#7a94b3}
.footer-social{display:flex;gap:12px;margin-top:18px}
.footer-social a{width:38px;height:38px;border-radius:10px;background:rgba(255,255,255,.08);display:flex;align-items:center;justify-content:center;margin:0}
.footer-social a:hover{background:var(--blue-600);padding-left:0}

.muted{color:var(--gray-500)}
.text-center{text-align:center}
.mt-3{margin-top:24px}
.mb-3{margin-bottom:24px}

.tabs{display:flex;gap:4px;border-bottom:2px solid var(--gray-100);margin-bottom:28px;overflow-x:auto;flex-wrap:wrap}
.tabs a{padding:12px 22px;font-weight:600;font-size:.9rem;color:var(--gray-500);border-bottom:3px solid transparent;margin-bottom:-2px;transition:.2s;white-space:nowrap}
.tabs a:hover{color:var(--blue-600)}
.tabs a.active{color:var(--blue-600);border-bottom-color:var(--blue-600)}
.admin-section{margin-bottom:48px}
.admin-section h3{font-size:1.25rem;margin-bottom:16px}
.icon-btn{background:none;border:none;cursor:pointer;color:var(--blue-600);font-size:1rem;padding:4px;text-decoration:none}
.icon-btn:hover{color:var(--blue-800)}
.delete-btn{color:#c0392b}
</style>
</head>
<body>

<div class="topbar">
  <div class="container topbar-inner">
    <div><i class="fas fa-phone"></i>{{ site.phone or '+91 98765 43210' }} &nbsp;·&nbsp; <i class="fas fa-envelope"></i>{{ site.email or 'stay@kantpg.com' }}</div>
    <div>
      <i class="fas fa-clock"></i>{{ site.office_hours or 'Office: 8:00 AM – 9:00 PM' }}
      <a href="{{ url_for('login') }}"><i class="fas fa-user-shield"></i>Admin</a>
    </div>
  </div>
</div>

<nav class="navbar">
  <div class="container nav-inner">
    <a href="{{ url_for('index') }}" class="brand">
      <div class="brand-mark">{{ (site.site_name or 'Kant PG')[0] }}</div>
      <div class="brand-text">
        <b>{{ site.site_name or 'Kant PG' }}</b>
        <span>{{ site.tagline or 'Comfort Since 2018' }}</span>
      </div>
    </a>
    <ul class="nav-links">
      <li><a href="{{ url_for('index') }}" class="{{ 'active' if request.endpoint == 'index' else '' }}">{{ site.nav_home or 'Home' }}</a></li>
      <li><a href="{{ url_for('rooms') }}" class="{{ 'active' if request.endpoint == 'rooms' else '' }}">{{ site.nav_rooms or 'Rooms' }}</a></li>
      <li><a href="{{ url_for('staff') }}" class="{{ 'active' if request.endpoint == 'staff' else '' }}">{{ site.nav_staff or 'Our Team' }}</a></li>
      <li><a href="{{ url_for('about') }}" class="{{ 'active' if request.endpoint == 'about' else '' }}">{{ site.nav_about or 'About' }}</a></li>
      <li><a href="{{ url_for('contact') }}" class="{{ 'active' if request.endpoint == 'contact' else '' }}">{{ site.nav_contact or 'Contact' }}</a></li>
      {% if session.get('admin_id') %}
        <li><a href="{{ url_for('admin_dashboard') }}">Dashboard</a></li>
        <li><a href="{{ url_for('logout') }}">Logout</a></li>
      {% endif %}
      <li><a href="{{ url_for('contact') }}" class="btn btn-sm" style="color:#fff">{{ site.nav_cta or 'Book a Room' }}</a></li>
    </ul>
  </div>
</nav>

{% with msgs = get_flashed_messages(with_categories=true) %}
  {% if msgs %}
    <div class="container">
      {% for cat, msg in msgs %}
        <div class="flash {{ cat }}"><i class="fas {{ 'fa-check-circle' if cat == 'success' else 'fa-exclamation-circle' }}"></i>{{ msg }}</div>
      {% endfor %}
    </div>
  {% endif %}
{% endwith %}

{% block content %}{% endblock %}

<footer class="footer">
  <div class="container">
    <div class="footer-grid">
      <div>
        <div class="brand" style="margin-bottom:18px">
          <div class="brand-mark" style="background:linear-gradient(135deg,var(--blue-500),var(--blue-700))">{{ (site.site_name or 'Kant PG')[0] }}</div>
          <div class="brand-text">
            <b style="color:#fff">{{ site.site_name or 'Kant PG' }}</b>
            <span>{{ site.tagline or 'Comfort Since 2018' }}</span>
          </div>
        </div>
        <p>{{ site.footer_about or 'A premium paying-guest residence for students and working professionals.' }}</p>
        <div class="footer-social">
          <a href="{{ site.whatsapp or '#' }}"><i class="fab fa-whatsapp"></i></a>
        </div>
      </div>
      <div>
        <h5>{{ site.footer_links_title or 'Quick Links' }}</h5>
        <a href="{{ url_for('index') }}">{{ site.nav_home or 'Home' }}</a>
        <a href="{{ url_for('rooms') }}">{{ site.nav_rooms or 'Rooms' }}</a>
        <a href="{{ url_for('staff') }}">{{ site.nav_staff or 'Our Team' }}</a>
        <a href="{{ url_for('about') }}">{{ site.nav_about or 'About Us' }}</a>
        <a href="{{ url_for('contact') }}">{{ site.nav_contact or 'Contact' }}</a>
      </div>
      <div>
        <h5>{{ site.footer_rooms_title or 'Room Types' }}</h5>
        {% for r in footer_rooms[:4] %}
          <a href="{{ url_for('room_detail', room_id=r.id) }}">{{ r.name }}</a>
        {% endfor %}
      </div>
      <div>
        <h5>{{ site.footer_contact_title or 'Get in Touch' }}</h5>
        <p><i class="fas fa-map-marker-alt" style="color:var(--blue-400);margin-right:8px"></i>{{ site.address or '123 Green Park, New Delhi' }}</p>
        <p><i class="fas fa-phone" style="color:var(--blue-400);margin-right:8px"></i>{{ site.phone or '+91 98765 43210' }}</p>
        <p><i class="fas fa-envelope" style="color:var(--blue-400);margin-right:8px"></i>{{ site.email or 'stay@kantpg.com' }}</p>
      </div>
    </div>
    <div class="footer-bottom">
      © {{ current_year }} {{ site.site_name or 'Kant PG' }} · {{ site.footer_copyright or 'All rights reserved · Designed with care.' }}
    </div>
  </div>
</footer>

</body>
</html>
"""


# ============================================================
# INDEX PAGE
# ============================================================
INDEX_HTML = BASE_HTML.replace("{% block content %}{% endblock %}", """
{% block content %}
<section class="hero">
  <div class="container hero-grid">
    <div>
      <div class="hero-eyebrow"><i class="fas fa-award"></i> {{ site.hero_eyebrow or 'Trusted by 1200+ residents' }}</div>
      <h1>{{ site.hero_title|safe if site.hero_title else 'Where <span class="accent">Comfort Meets Convenience</span>' }}</h1>
      <p>{{ site.hero_subtitle or 'A premium paying-guest residence built for students and working professionals.' }}</p>
      <div class="hero-actions">
        <a href="{{ url_for('rooms') }}" class="btn btn-lg">{{ site.hero_cta1 or 'Explore Rooms' }} <i class="fas fa-arrow-right"></i></a>
        <a href="{{ url_for('contact') }}" class="btn btn-outline btn-lg">{{ site.hero_cta2 or 'Book a Visit' }}</a>
      </div>
      <div class="hero-trust">
        <div class="trust-item"><b>{{ site.stat1_num or '7+' }}</b><span>{{ site.stat1_label or 'Years of Trust' }}</span></div>
        <div class="trust-item"><b>{{ site.stat2_num or '1200+' }}</b><span>{{ site.stat2_label or 'Happy Residents' }}</span></div>
        <div class="trust-item"><b>{{ site.stat3_num or '4.8★' }}</b><span>{{ site.stat3_label or 'Average Rating' }}</span></div>
        <div class="trust-item"><b>{{ site.stat4_num or '24/7' }}</b><span>{{ site.stat4_label or 'Security' }}</span></div>
      </div>
    </div>
    <div class="hero-visual">
      <div class="hv-header">
        <span>{{ site.hv_heading or 'Available Rooms' }}</span>
        <div class="hv-badge">● {{ site.hv_badge or 'Live Now' }}</div>
      </div>
      {% for room in rooms %}
      <div class="hv-course">
        <div class="hv-icon"><i class="fas {{ room.icon }}"></i></div>
        <div style="flex:1">
          <b>{{ room.name }}</b>
          <small>{{ room.sharing }} · ₹{{ room.price }}/mo</small>
        </div>
        <i class="fas fa-chevron-right" style="color:var(--gray-200)"></i>
      </div>
      {% endfor %}
      <div class="hv-footer">
        <a href="{{ url_for('rooms') }}" class="btn">{{ site.hv_cta or 'View All Rooms' }}</a>
      </div>
    </div>
  </div>
</section>

<section class="section">
  <div class="container">
    <div class="section-head">
      <div class="section-eyebrow">{{ site.why_eyebrow or 'Why Choose Us' }}</div>
      <h2>{{ site.why_title or 'More Than Just a Room' }}</h2>
      <p>{{ site.why_subtitle or 'Kant PG combines the safety of home with the independence of independent living.' }}</p>
    </div>
    <div class="features-grid">
      {% for f in features %}
      <div class="feature-card">
        <div class="feature-icon"><i class="fas {{ f.icon }}"></i></div>
        <h4>{{ f.title }}</h4>
        <p>{{ f.description }}</p>
      </div>
      {% endfor %}
    </div>
  </div>
</section>

<section class="section section-alt">
  <div class="container">
    <div class="section-head">
      <div class="section-eyebrow">{{ site.rooms_eyebrow or 'Our Rooms' }}</div>
      <h2>{{ site.rooms_title or 'Find Your Perfect Space' }}</h2>
      <p>{{ site.rooms_subtitle or 'From budget-friendly sharing to premium private rooms.' }}</p>
    </div>
    <div class="courses-grid">
      {% for room in rooms %}
      <div class="course-card">
        {% if room.available_beds > 0 %}
          <div class="course-tag">{{ site.rooms_tag_available or 'Available' }}</div>
        {% else %}
          <div class="course-tag" style="background:#f8d7da;color:#721c24">{{ site.rooms_tag_full or 'Full' }}</div>
        {% endif %}
        <div class="course-icon"><i class="fas {{ room.icon }}"></i></div>
        <h3>{{ room.name }}</h3>
        <div class="course-meta">{{ room.sharing }} · {{ room.floor }}</div>
        <p>{{ room.description[:90] }}...</p>
        <div class="course-footer">
          <div>
            <div class="course-price">₹{{ room.price }}<small>{{ site.rooms_price_suffix or '/mo' }}</small></div>
            <div class="seats"><b>{{ room.available_beds }}</b> / {{ room.beds }} {{ site.rooms_beds_label or 'beds left' }}</div>
          </div>
          <a href="{{ url_for('room_detail', room_id=room.id) }}" class="btn btn-sm">{{ site.rooms_btn or 'Details' }}</a>
        </div>
      </div>
      {% endfor %}
    </div>
    <div class="text-center" style="margin-top:48px">
      <a href="{{ url_for('rooms') }}" class="btn btn-outline btn-lg">{{ site.rooms_cta or 'View All Rooms' }}</a>
    </div>
  </div>
</section>

<section class="section">
  <div class="container">
    <div class="section-head">
      <div class="section-eyebrow">{{ site.testi_eyebrow or 'Testimonials' }}</div>
      <h2>{{ site.testi_title or 'What Our Residents Say' }}</h2>
      <p>{{ site.testi_subtitle or 'Real experiences from the people who call Kant PG home.' }}</p>
    </div>
    <div class="testi-grid">
      {% for t in testimonials %}
      <div class="testi-card">
        <div class="testi-quote">"</div>
        <div class="testi-stars">{% for _ in range(t.stars or 5) %}<i class="fas fa-star"></i>{% endfor %}</div>
        <p>{{ t.content }}</p>
        <div class="testi-author">
          <div class="testi-avatar">{{ t.avatar or t.name[:2]|upper }}</div>
          <div><b>{{ t.name }}</b><small>{{ t.role }}</small></div>
        </div>
      </div>
      {% endfor %}
    </div>
  </div>
</section>

<section class="section" style="padding-top:0">
  <div class="container">
    <div class="cta-banner">
      <div>
        <h2>{{ site.cta_title or 'Ready to Move In?' }}</h2>
        <p>{{ site.cta_subtitle or 'Schedule a visit today.' }}</p>
      </div>
      <div style="display:flex;gap:12px;flex-wrap:wrap">
        <a href="{{ url_for('contact') }}" class="btn btn-white btn-lg">{{ site.cta_btn1 or 'Book a Visit' }}</a>
        <a href="tel:{{ site.phone or '+919876543210' }}" class="btn btn-lg" style="background:rgba(255,255,255,.15);color:#fff;box-shadow:none;border:1.5px solid rgba(255,255,255,.3)"><i class="fas fa-phone"></i> {{ site.cta_btn2 or 'Call Us' }}</a>
      </div>
    </div>
  </div>
</section>
{% endblock %}
""")


# ============================================================
# ROOMS PAGE
# ============================================================
ROOMS_HTML = BASE_HTML.replace("{% block content %}{% endblock %}", """
{% block content %}
<section class="section" style="padding-top:56px">
  <div class="container">
    <div class="section-head">
      <div class="section-eyebrow">{{ site.rooms_page_eyebrow or 'All Rooms' }}</div>
      <h2>{{ site.rooms_page_title or 'Our Complete Room Catalogue' }}</h2>
      <p>{{ site.rooms_page_subtitle or 'Choose the room that fits your budget and lifestyle.' }}</p>
    </div>
    <div class="courses-grid">
      {% for room in rooms %}
      <div class="course-card">
        {% if room.available_beds > 0 %}
          <div class="course-tag">{{ site.rooms_tag_available or 'Available' }}</div>
        {% else %}
          <div class="course-tag" style="background:#f8d7da;color:#721c24">{{ site.rooms_tag_full or 'Full' }}</div>
        {% endif %}
        <div class="course-icon"><i class="fas {{ room.icon }}"></i></div>
        <h3>{{ room.name }}</h3>
        <div class="course-meta">{{ room.sharing }} · {{ room.floor }}</div>
        <p>{{ room.description }}</p>
        <div class="course-footer">
          <div>
            <div class="course-price">₹{{ room.price }}<small>{{ site.rooms_price_suffix or '/mo' }}</small></div>
            <div class="seats"><b>{{ room.available_beds }}</b> / {{ room.beds }} {{ site.rooms_beds_label or 'beds left' }}</div>
          </div>
          <a href="{{ url_for('room_detail', room_id=room.id) }}" class="btn btn-sm">{{ site.rooms_page_btn or 'Book' }}</a>
        </div>
      </div>
      {% endfor %}
    </div>
  </div>
</section>
{% endblock %}
""")


# ============================================================
# ROOM DETAIL PAGE
# ============================================================
ROOM_DETAIL_HTML = BASE_HTML.replace("{% block content %}{% endblock %}", """
{% block content %}
<section class="section" style="padding-top:48px">
  <div class="container">
    <a href="{{ url_for('rooms') }}" style="color:var(--blue-600);font-weight:600;font-size:.92rem">
      <i class="fas fa-arrow-left"></i> {{ site.room_detail_back or 'Back to all rooms' }}
    </a>
    <div class="detail-card">
      <div class="detail-left">
        <div class="big-icon"><i class="fas {{ room.icon }}"></i></div>
        <b>{{ room.name }}</b>
        <div style="color:var(--blue-700);font-weight:600;margin-top:8px">{{ room.sharing }}</div>
        <div style="color:var(--gray-500);font-size:.9rem;margin-top:4px">{{ room.floor }}</div>
      </div>
      <div>
        <h2 style="margin-bottom:8px">{{ room.name }}</h2>
        <div class="course-meta" style="margin-bottom:20px">
          <i class="fas fa-layer-group" style="color:var(--blue-600)"></i> {{ room.floor }}
          &nbsp;·&nbsp;
          <i class="fas fa-clock" style="color:var(--blue-600)"></i> {{ room.duration }}
        </div>
        <p style="color:var(--gray-500);margin-bottom:24px">{{ room.description }}</p>

        <div style="background:var(--blue-50);padding:22px;border-radius:var(--radius);margin-bottom:24px;border-left:4px solid var(--blue-600)">
          <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:12px">
            <div>
              <div class="course-price">₹{{ room.price }}<small>/month</small></div>
              <div class="seats" style="margin-top:6px"><b>{{ room.available_beds }}</b> of {{ room.beds }} {{ site.room_detail_beds_label or 'beds available' }}</div>
            </div>
            <div style="font-size:.85rem;color:var(--blue-700);font-weight:600">
              <i class="fas fa-check-circle"></i> {{ site.room_detail_badge or 'No brokerage · Free visit' }}
            </div>
          </div>
        </div>

        {% if room.available_beds > 0 %}
        <h3 style="font-size:1.3rem;margin-bottom:20px">{{ site.room_detail_form_title or 'Reserve Your Bed' }}</h3>
        <form method="POST" action="{{ url_for('book', room_id=room.id) }}" class="form">
          <div class="form-row">
            <div><label>{{ site.booking_label_name or 'Full Name *' }}</label><input type="text" name="guest_name" placeholder="Your name" required style="width:100%"></div>
            <div><label>{{ site.booking_label_occupation or 'Occupation' }}</label><input type="text" name="occupation" placeholder="Student / Professional" style="width:100%"></div>
          </div>
          <div class="form-row">
            <div><label>{{ site.booking_label_email or 'Email *' }}</label><input type="email" name="email" placeholder="you@example.com" required style="width:100%"></div>
            <div><label>{{ site.booking_label_phone or 'Phone *' }}</label><input type="tel" name="phone" placeholder="+91 ..." required style="width:100%"></div>
          </div>
          <label>{{ site.booking_label_message or 'Message' }}</label>
          <textarea name="message" rows="3" placeholder="Move-in date, preferences, questions"></textarea>
          <button type="submit" class="btn btn-lg" style="margin-top:6px"><i class="fas fa-paper-plane"></i> {{ site.booking_form_btn or 'Submit Booking Request' }}</button>
        </form>
        {% else %}
        <div class="flash error"><i class="fas fa-exclamation-circle"></i>{{ site.room_detail_full_msg or 'This room is currently full. Please contact us to join the waitlist.' }}</div>
        {% endif %}
      </div>
    </div>
  </div>
</section>
{% endblock %}
""")


# ============================================================
# STAFF PAGE
# ============================================================
STAFF_HTML = BASE_HTML.replace("{% block content %}{% endblock %}", """
{% block content %}
<section class="section">
  <div class="container">
    <div class="section-head">
      <div class="section-eyebrow">{{ site.staff_eyebrow or 'Our Team' }}</div>
      <h2>{{ site.staff_title or 'Meet the People Behind Kant PG' }}</h2>
      <p>{{ site.staff_subtitle or 'Wardens, managers, and support staff who make your stay safe and comfortable.' }}</p>
    </div>
    <div class="faculty-grid">
      {% for member in members %}
      <div class="faculty-card">
        <div class="faculty-avatar"><i class="fas {{ member.icon }}"></i></div>
        <h4>{{ member.name }}</h4>
        <div class="subject">{{ member.role }}</div>
        <p>{{ member.bio }}</p>
        <div class="faculty-meta">
          <div><i class="fas fa-graduation-cap"></i>{{ member.qualification }}</div>
          <div><i class="fas fa-briefcase"></i>{{ member.experience }}</div>
        </div>
      </div>
      {% endfor %}
    </div>
  </div>
</section>
{% endblock %}
""")


# ============================================================
# ABOUT PAGE
# ============================================================
ABOUT_HTML = BASE_HTML.replace("{% block content %}{% endblock %}", """
{% block content %}
<section class="section" style="padding-top:56px">
  <div class="container">
    <div class="section-head">
      <div class="section-eyebrow">{{ site.about_eyebrow or 'About Us' }}</div>
      <h2>{{ site.about_title or 'Seven Years of Welcoming Residents' }}</h2>
      <p>{{ site.about_subtitle or 'Since 2018, Kant PG has been a trusted home.' }}</p>
    </div>

    <div style="display:grid;grid-template-columns:1fr 1fr;gap:48px;align-items:center;margin-bottom:60px" class="about-grid">
      <div>
        <h3 style="font-size:1.8rem;margin-bottom:18px">{{ site.about_story_heading or 'Our Story' }}</h3>
        <p style="color:var(--gray-500);margin-bottom:18px;white-space:pre-line">{{ site.about_p1 or 'Kant PG started with a single building and a simple belief: everyone deserves a safe place to call home.' }}</p>
        <p style="color:var(--gray-500);margin-bottom:18px;white-space:pre-line">{{ site.about_p2 or 'Today we accommodate 120+ residents across multiple floors.' }}</p>
        <p style="color:var(--gray-500);white-space:pre-line">{{ site.about_p3 or 'From students to working professionals, thousands have passed through our doors.' }}</p>
      </div>
      <div style="background:var(--blue-50);padding:48px;border-radius:var(--radius-lg);text-align:center">
        <i class="fas fa-building" style="font-size:5rem;color:var(--blue-600);margin-bottom:20px"></i>
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:24px;margin-top:20px">
          <div><b style="font-family:'Merriweather',serif;font-size:2rem;color:var(--blue-900);display:block">{{ site.about_stat1_num or '7+' }}</b><span style="font-size:.85rem;color:var(--gray-500)">{{ site.about_stat1_label or 'Years of Trust' }}</span></div>
          <div><b style="font-family:'Merriweather',serif;font-size:2rem;color:var(--blue-900);display:block">{{ site.about_stat2_num or '1200+' }}</b><span style="font-size:.85rem;color:var(--gray-500)">{{ site.about_stat2_label or 'Happy Residents' }}</span></div>
          <div><b style="font-family:'Merriweather',serif;font-size:2rem;color:var(--blue-900);display:block">{{ site.about_stat3_num or '4.8★' }}</b><span style="font-size:.85rem;color:var(--gray-500)">{{ site.about_stat3_label or 'Average Rating' }}</span></div>
          <div><b style="font-family:'Merriweather',serif;font-size:2rem;color:var(--blue-900);display:block">{{ site.about_stat4_num or '24/7' }}</b><span style="font-size:.85rem;color:var(--gray-500)">{{ site.about_stat4_label or 'Security' }}</span></div>
        </div>
      </div>
    </div>

    <h3 style="font-size:1.8rem;margin-bottom:28px;text-align:center">{{ site.about_values_heading or 'Our Values' }}</h3>
    <div class="features-grid">
      {% for f in features %}
      <div class="feature-card">
        <div class="feature-icon"><i class="fas {{ f.icon }}"></i></div>
        <h4>{{ f.title }}</h4>
        <p>{{ f.description }}</p>
      </div>
      {% endfor %}
    </div>
  </div>
</section>
<style>@media(max-width:800px){.about-grid{grid-template-columns:1fr!important}}</style>
{% endblock %}
""")


# ============================================================
# CONTACT PAGE — fully editable
# ============================================================
CONTACT_HTML = BASE_HTML.replace("{% block content %}{% endblock %}", """
{% block content %}
<section class="section">
  <div class="container">
    <div class="section-head">
      <div class="section-eyebrow">{{ site.contact_eyebrow or 'Get in Touch' }}</div>
      <h2>{{ site.contact_title or "We'd Love to Hear From You" }}</h2>
      <p>{{ site.contact_subtitle or 'Book a visit, ask about availability, or just say hello.' }}</p>
    </div>
    <div style="display:grid;grid-template-columns:1fr 1.2fr;gap:48px" class="contact-grid">
      <div>
        <h3 style="font-size:1.5rem;margin-bottom:24px">{{ site.contact_info_heading or 'Contact Information' }}</h3>
        <div style="display:flex;flex-direction:column;gap:24px">

          <div style="display:flex;gap:16px;align-items:flex-start">
            <div style="width:48px;height:48px;border-radius:12px;background:var(--blue-50);color:var(--blue-600);display:flex;align-items:center;justify-content:center;font-size:1.15rem;flex-shrink:0"><i class="fas fa-map-marker-alt"></i></div>
            <div>
              <b style="display:block;color:var(--blue-900);margin-bottom:4px">{{ site.contact_label_address or 'Visit Our PG' }}</b>
              <span style="color:var(--gray-500);font-size:.92rem;white-space:pre-line">{{ site.address or '123 Green Park, New Delhi' }}</span>
            </div>
          </div>

          <div style="display:flex;gap:16px;align-items:flex-start">
            <div style="width:48px;height:48px;border-radius:12px;background:var(--blue-50);color:var(--blue-600);display:flex;align-items:center;justify-content:center;font-size:1.15rem;flex-shrink:0"><i class="fas fa-phone-alt"></i></div>
            <div>
              <b style="display:block;color:var(--blue-900);margin-bottom:4px">{{ site.contact_label_phone or 'Call Us' }}</b>
              <span style="color:var(--gray-500);font-size:.92rem;white-space:pre-line">{{ site.phone or '+91 98765 43210' }}{% if site.phone_secondary %}<br>{{ site.phone_secondary }}{% endif %}</span>
            </div>
          </div>

          <div style="display:flex;gap:16px;align-items:flex-start">
            <div style="width:48px;height:48px;border-radius:12px;background:var(--blue-50);color:var(--blue-600);display:flex;align-items:center;justify-content:center;font-size:1.15rem;flex-shrink:0"><i class="fas fa-envelope"></i></div>
            <div>
              <b style="display:block;color:var(--blue-900);margin-bottom:4px">{{ site.contact_label_email or 'Email Us' }}</b>
              <span style="color:var(--gray-500);font-size:.92rem;white-space:pre-line">{{ site.email or 'stay@kantpg.com' }}{% if site.email_secondary %}<br>{{ site.email_secondary }}{% endif %}</span>
            </div>
          </div>

          <div style="display:flex;gap:16px;align-items:flex-start">
            <div style="width:48px;height:48px;border-radius:12px;background:var(--blue-50);color:var(--blue-600);display:flex;align-items:center;justify-content:center;font-size:1.15rem;flex-shrink:0"><i class="fas fa-clock"></i></div>
            <div>
              <b style="display:block;color:var(--blue-900);margin-bottom:4px">{{ site.contact_label_hours or 'Office Hours' }}</b>
              <span style="color:var(--gray-500);font-size:.92rem;white-space:pre-line">{{ site.office_hours_detailed or 'Mon–Sat: 8:00 AM – 9:00 PM' }}</span>
            </div>
          </div>
        </div>
      </div>

      <div class="card">
        <h3 style="font-size:1.4rem;margin-bottom:22px">{{ site.contact_form_title or 'Send Us a Message' }}</h3>
        <form method="POST" class="form">
          <div class="form-row">
            <div><label>{{ site.contact_form_name_label or 'Your Name *' }}</label><input type="text" name="name" placeholder="Full name" required style="width:100%"></div>
            <div><label>{{ site.contact_form_email_label or 'Email *' }}</label><input type="email" name="email" placeholder="you@example.com" required style="width:100%"></div>
          </div>
          <label>{{ site.contact_form_message_label or 'Message *' }}</label>
          <textarea name="content" rows="6" placeholder="Tell us how we can help..." required></textarea>
          <button type="submit" class="btn btn-lg"><i class="fas fa-paper-plane"></i> {{ site.contact_form_btn or 'Send Message' }}</button>
        </form>
      </div>
    </div>
  </div>
</section>
<style>@media(max-width:800px){.contact-grid{grid-template-columns:1fr!important}}</style>
{% endblock %}
""")


# ============================================================
# LOGIN PAGE
# ============================================================
LOGIN_HTML = BASE_HTML.replace("{% block content %}{% endblock %}", """
{% block content %}
<div class="auth-wrap">
  <div class="card">
    <h2 style="font-size:1.6rem;margin-bottom:6px">{{ site.login_title or 'Admin Login' }}</h2>
    <p class="sub">{{ site.login_subtitle or 'Access the management dashboard' }}</p>
    <form method="POST" class="form">
      <label>Username</label>
      <input type="text" name="username" placeholder="Enter username" required>
      <label>Password</label>
      <input type="password" name="password" placeholder="Enter password" required>
      <button type="submit" class="btn" style="margin-top:8px"><i class="fas fa-sign-in-alt"></i> Login</button>
    </form>
  </div>
</div>
{% endblock %}
""")


# ============================================================
# ADMIN TEMPLATES
# ============================================================
ADMIN_HTML = BASE_HTML.replace("{% block content %}{% endblock %}", """
{% block content %}
<section class="section" style="padding-top:48px">
  <div class="container">
    <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:16px;margin-bottom:24px">
      <div>
        <h2 style="font-size:1.9rem">Admin Dashboard</h2>
        <p class="muted" style="font-size:.92rem">Manage everything from here</p>
      </div>
      <a href="{{ url_for('logout') }}" class="btn btn-outline btn-sm"><i class="fas fa-sign-out-alt"></i> Logout</a>
    </div>

    <div class="tabs">
      <a href="{{ url_for('admin_dashboard') }}" class="{{ 'active' if tab == 'overview' else '' }}">Overview</a>
      <a href="{{ url_for('admin_bookings') }}" class="{{ 'active' if tab == 'bookings' else '' }}">Bookings ({{ stats.pending }})</a>
      <a href="{{ url_for('admin_rooms') }}" class="{{ 'active' if tab == 'rooms' else '' }}">Rooms</a>
      <a href="{{ url_for('admin_staff') }}" class="{{ 'active' if tab == 'staff' else '' }}">Staff</a>
      <a href="{{ url_for('admin_features') }}" class="{{ 'active' if tab == 'features' else '' }}">Features</a>
      <a href="{{ url_for('admin_testimonials') }}" class="{{ 'active' if tab == 'testimonials' else '' }}">Testimonials</a>
      <a href="{{ url_for('admin_messages') }}" class="{{ 'active' if tab == 'messages' else '' }}">Messages</a>
      <a href="{{ url_for('admin_settings') }}" class="{{ 'active' if tab == 'settings' else '' }}">Site Content</a>
      <a href="{{ url_for('admin_account') }}" class="{{ 'active' if tab == 'account' else '' }}">Account</a>
    </div>

    {% block admin_content %}{% endblock %}
  </div>
</section>
{% endblock %}
""")


ADMIN_OVERVIEW = ADMIN_HTML.replace("{% block admin_content %}{% endblock %}", """
{% block admin_content %}
<div class="stats-grid">
  <div class="stat-card"><span>{{ stats.total_bookings }}</span>Bookings</div>
  <div class="stat-card"><span>{{ stats.pending }}</span>Pending</div>
  <div class="stat-card"><span>{{ stats.confirmed }}</span>Confirmed</div>
  <div class="stat-card"><span>{{ stats.total_rooms }}</span>Rooms</div>
  <div class="stat-card"><span>{{ stats.total_staff }}</span>Staff</div>
  <div class="stat-card"><span>{{ stats.total_messages }}</span>Messages</div>
</div>

<div style="display:grid;grid-template-columns:1fr 1fr;gap:24px" class="ov-grid">
  <div class="card">
    <h3 style="font-size:1.1rem;margin-bottom:16px"><i class="fas fa-clock" style="color:var(--blue-600)"></i> Recent Bookings</h3>
    <div class="table-wrap" style="margin:0">
      <table>
        <tr><th>Guest</th><th>Room</th><th>Status</th></tr>
        {% for b in recent_bookings %}
        <tr>
          <td>{{ b.guest_name }}</td>
          <td>{{ b.room.name if b.room else '—' }}</td>
          <td><span class="tag {{ b.status }}">{{ b.status }}</span></td>
        </tr>
        {% else %}
        <tr><td colspan="3" class="muted">No bookings yet.</td></tr>
        {% endfor %}
      </table>
    </div>
  </div>
  <div class="card">
    <h3 style="font-size:1.1rem;margin-bottom:16px"><i class="fas fa-envelope" style="color:var(--blue-600)"></i> Recent Messages</h3>
    <div class="table-wrap" style="margin:0">
      <table>
        <tr><th>Name</th><th>Message</th></tr>
        {% for m in recent_messages %}
        <tr><td>{{ m.name }}</td><td>{{ m.content[:60] }}...</td></tr>
        {% else %}
        <tr><td colspan="2" class="muted">No messages yet.</td></tr>
        {% endfor %}
      </table>
    </div>
  </div>
</div>
<style>@media(max-width:800px){.ov-grid{grid-template-columns:1fr!important}}</style>
{% endblock %}
""")


ADMIN_BOOKINGS = ADMIN_HTML.replace("{% block admin_content %}{% endblock %}", """
{% block admin_content %}
<h3 style="margin-bottom:16px">All Bookings</h3>
<div class="table-wrap">
  <table>
    <tr><th>#</th><th>Guest</th><th>Contact</th><th>Room</th><th>Date</th><th>Status</th><th>Actions</th></tr>
    {% for b in bookings %}
    <tr>
      <td>{{ b.id }}</td>
      <td>{{ b.guest_name }}<br><small class="muted">{{ b.occupation or '—' }}</small></td>
      <td>{{ b.phone }}<br><small class="muted">{{ b.email }}</small></td>
      <td>{{ b.room.name if b.room else '—' }}</td>
      <td>{{ b.created_at.strftime('%d %b %Y') }}</td>
      <td><span class="tag {{ b.status }}">{{ b.status }}</span></td>
      <td style="white-space:nowrap">
        <a href="{{ url_for('update_booking', booking_id=b.id, status='confirmed') }}" class="icon-btn" title="Confirm">✅</a>
        <a href="{{ url_for('update_booking', booking_id=b.id, status='rejected') }}" class="icon-btn" title="Reject">❌</a>
        <a href="{{ url_for('admin_delete_booking', booking_id=b.id) }}" class="icon-btn delete-btn" onclick="return confirm('Delete?')" title="Delete">🗑️</a>
      </td>
    </tr>
    {% else %}
    <tr><td colspan="7" class="muted text-center">No bookings yet.</td></tr>
    {% endfor %}
  </table>
</div>
{% endblock %}
""")


ADMIN_ROOMS = ADMIN_HTML.replace("{% block admin_content %}{% endblock %}", """
{% block admin_content %}
<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px">
  <h3>Rooms</h3>
  <button class="btn btn-sm" onclick="document.getElementById('addRoomForm').style.display='block'"><i class="fas fa-plus"></i> Add Room</button>
</div>

<div id="addRoomForm" class="card" style="margin-bottom:24px;display:none">
  <h4 style="margin-bottom:16px">Add New Room</h4>
  <form method="POST" action="{{ url_for('admin_add_room') }}" class="form">
    <div class="form-row">
      <div><label>Room Name *</label><input type="text" name="name" required style="width:100%"></div>
      <div><label>Sharing Type *</label><input type="text" name="sharing" placeholder="Single / Double / Triple" required style="width:100%"></div>
    </div>
    <div class="form-row">
      <div><label>Floor / Info *</label><input type="text" name="floor" placeholder="2nd Floor · AC" required style="width:100%"></div>
      <div><label>Min Duration</label><input type="text" name="duration" placeholder="3 months" style="width:100%"></div>
    </div>
    <div class="form-row">
      <div><label>Monthly Rent (₹) *</label><input type="number" name="price" required style="width:100%"></div>
      <div><label>Total Beds *</label><input type="number" name="beds" required style="width:100%"></div>
    </div>
    <label>Description *</label>
    <textarea name="description" rows="3" required></textarea>
    <label>Icon</label>
    <select name="icon">
      <option value="fa-bed">Bed</option><option value="fa-user">Single</option>
      <option value="fa-user-friends">Two</option><option value="fa-users">Group</option>
      <option value="fa-crown">Premium</option><option value="fa-home">Home</option>
    </select>
    <button class="btn" type="submit">Add Room</button>
  </form>
</div>

<div class="table-wrap">
  <table>
    <tr><th>ID</th><th>Name</th><th>Sharing</th><th>Price</th><th>Beds</th><th>Active</th><th>Actions</th></tr>
    {% for r in rooms %}
    <tr>
      <td>{{ r.id }}</td>
      <td>{{ r.name }}</td>
      <td>{{ r.sharing }}</td>
      <td>₹{{ r.price }}</td>
      <td>{{ r.available_beds }} / {{ r.beds }}</td>
      <td>{{ '✅' if r.is_active else '❌' }}</td>
      <td style="white-space:nowrap">
        <a href="{{ url_for('admin_edit_room', room_id=r.id) }}" class="icon-btn">✏️</a>
        <a href="{{ url_for('admin_delete_room', room_id=r.id) }}" class="icon-btn delete-btn" onclick="return confirm('Delete?')">🗑️</a>
      </td>
    </tr>
    {% else %}
    <tr><td colspan="7" class="muted text-center">No rooms yet.</td></tr>
    {% endfor %}
  </table>
</div>
{% endblock %}
""")


ADMIN_EDIT_ROOM = ADMIN_HTML.replace("{% block admin_content %}{% endblock %}", """
{% block admin_content %}
<a href="{{ url_for('admin_rooms') }}" style="color:var(--blue-600);font-weight:600"><i class="fas fa-arrow-left"></i> Back</a>
<div class="card" style="margin-top:20px;max-width:720px">
  <h3 style="margin-bottom:20px">Edit Room: {{ room.name }}</h3>
  <form method="POST" class="form">
    <div class="form-row">
      <div><label>Room Name *</label><input type="text" name="name" value="{{ room.name }}" required style="width:100%"></div>
      <div><label>Sharing Type *</label><input type="text" name="sharing" value="{{ room.sharing }}" required style="width:100%"></div>
    </div>
    <div class="form-row">
      <div><label>Floor / Info *</label><input type="text" name="floor" value="{{ room.floor }}" required style="width:100%"></div>
      <div><label>Min Duration</label><input type="text" name="duration" value="{{ room.duration or '' }}" style="width:100%"></div>
    </div>
    <div class="form-row">
      <div><label>Monthly Rent (₹) *</label><input type="number" name="price" value="{{ room.price }}" required style="width:100%"></div>
      <div><label>Total Beds *</label><input type="number" name="beds" value="{{ room.beds }}" required style="width:100%"></div>
    </div>
    <div class="form-row">
      <div><label>Available Beds *</label><input type="number" name="available_beds" value="{{ room.available_beds }}" required style="width:100%"></div>
      <div><label>Icon</label>
        <select name="icon" style="width:100%">
          {% for ic in ['fa-bed','fa-user','fa-user-friends','fa-users','fa-crown','fa-home'] %}
          <option value="{{ ic }}" {{ 'selected' if room.icon == ic else '' }}>{{ ic }}</option>
          {% endfor %}
        </select>
      </div>
    </div>
    <label>Description *</label>
    <textarea name="description" rows="4" required>{{ room.description }}</textarea>
    <label style="display:flex;align-items:center;gap:8px;flex-direction:row">
      <input type="checkbox" name="is_active" {{ 'checked' if room.is_active else '' }} style="width:auto"> Show on site
    </label>
    <button class="btn" type="submit"><i class="fas fa-save"></i> Save</button>
  </form>
</div>
{% endblock %}
""")


ADMIN_STAFF = ADMIN_HTML.replace("{% block admin_content %}{% endblock %}", """
{% block admin_content %}
<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px">
  <h3>Staff Members</h3>
  <button class="btn btn-sm" onclick="document.getElementById('addStaffForm').style.display='block'"><i class="fas fa-plus"></i> Add Staff</button>
</div>

<div id="addStaffForm" class="card" style="margin-bottom:24px;display:none">
  <h4 style="margin-bottom:16px">Add New Staff</h4>
  <form method="POST" action="{{ url_for('admin_add_staff') }}" class="form">
    <div class="form-row">
      <div><label>Name *</label><input type="text" name="name" required style="width:100%"></div>
      <div><label>Role *</label><input type="text" name="role" required style="width:100%"></div>
    </div>
    <div class="form-row">
      <div><label>Qualification</label><input type="text" name="qualification" style="width:100%"></div>
      <div><label>Experience</label><input type="text" name="experience" style="width:100%"></div>
    </div>
    <label>Bio</label>
    <textarea name="bio" rows="2"></textarea>
    <label>Icon</label>
    <select name="icon">
      <option value="fa-user-tie">Tie</option><option value="fa-user">User</option>
      <option value="fa-user-shield">Shield</option><option value="fa-user-cog">Cog</option>
    </select>
    <button class="btn" type="submit">Add Staff</button>
  </form>
</div>

<div class="table-wrap">
  <table>
    <tr><th>ID</th><th>Name</th><th>Role</th><th>Active</th><th>Actions</th></tr>
    {% for s in staff %}
    <tr>
      <td>{{ s.id }}</td>
      <td>{{ s.name }}</td>
      <td>{{ s.role }}</td>
      <td>{{ '✅' if s.is_active else '❌' }}</td>
      <td>
        <a href="{{ url_for('admin_edit_staff', staff_id=s.id) }}" class="icon-btn">✏️</a>
        <a href="{{ url_for('admin_delete_staff', staff_id=s.id) }}" class="icon-btn delete-btn" onclick="return confirm('Delete?')">🗑️</a>
      </td>
    </tr>
    {% else %}
    <tr><td colspan="5" class="muted text-center">No staff yet.</td></tr>
    {% endfor %}
  </table>
</div>
{% endblock %}
""")


ADMIN_EDIT_STAFF = ADMIN_HTML.replace("{% block admin_content %}{% endblock %}", """
{% block admin_content %}
<a href="{{ url_for('admin_staff') }}" style="color:var(--blue-600);font-weight:600"><i class="fas fa-arrow-left"></i> Back</a>
<div class="card" style="margin-top:20px;max-width:720px">
  <h3 style="margin-bottom:20px">Edit Staff: {{ member.name }}</h3>
  <form method="POST" class="form">
    <div class="form-row">
      <div><label>Name *</label><input type="text" name="name" value="{{ member.name }}" required style="width:100%"></div>
      <div><label>Role *</label><input type="text" name="role" value="{{ member.role }}" required style="width:100%"></div>
    </div>
    <div class="form-row">
      <div><label>Qualification</label><input type="text" name="qualification" value="{{ member.qualification or '' }}" style="width:100%"></div>
      <div><label>Experience</label><input type="text" name="experience" value="{{ member.experience or '' }}" style="width:100%"></div>
    </div>
    <label>Bio</label>
    <textarea name="bio" rows="3">{{ member.bio or '' }}</textarea>
    <label>Icon</label>
    <select name="icon" style="width:100%">
      {% for ic in ['fa-user-tie','fa-user','fa-user-shield','fa-user-cog'] %}
      <option value="{{ ic }}" {{ 'selected' if member.icon == ic else '' }}>{{ ic }}</option>
      {% endfor %}
    </select>
    <label style="display:flex;align-items:center;gap:8px;flex-direction:row">
      <input type="checkbox" name="is_active" {{ 'checked' if member.is_active else '' }} style="width:auto"> Show on site
    </label>
    <button class="btn" type="submit"><i class="fas fa-save"></i> Save</button>
  </form>
</div>
{% endblock %}
""")


ADMIN_FEATURES = ADMIN_HTML.replace("{% block admin_content %}{% endblock %}", """
{% block admin_content %}
<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px">
  <h3>"Why Choose Us" Features</h3>
  <button class="btn btn-sm" onclick="document.getElementById('addFeatureForm').style.display='block'"><i class="fas fa-plus"></i> Add</button>
</div>

<div id="addFeatureForm" class="card" style="margin-bottom:24px;display:none">
  <h4 style="margin-bottom:16px">Add New Feature</h4>
  <form method="POST" action="{{ url_for('admin_add_feature') }}" class="form">
    <div class="form-row">
      <div><label>Title *</label><input type="text" name="title" required style="width:100%"></div>
      <div><label>Icon</label>
        <select name="icon" style="width:100%">
          {% for ic in ['fa-utensils','fa-wifi','fa-shield-alt','fa-broom','fa-tshirt','fa-map-marker-alt','fa-bed','fa-star','fa-heart','fa-award'] %}
          <option value="{{ ic }}">{{ ic }}</option>
          {% endfor %}
        </select>
      </div>
    </div>
    <label>Description</label>
    <textarea name="description" rows="2"></textarea>
    <label>Sort order</label>
    <input type="number" name="sort_order" value="0">
    <button class="btn" type="submit">Add Feature</button>
  </form>
</div>

<div class="table-wrap">
  <table>
    <tr><th>Order</th><th>Icon</th><th>Title</th><th>Description</th><th>Actions</th></tr>
    {% for f in features %}
    <tr>
      <td>{{ f.sort_order }}</td>
      <td><i class="fas {{ f.icon }}"></i></td>
      <td>{{ f.title }}</td>
      <td>{{ f.description[:60] }}...</td>
      <td>
        <a href="{{ url_for('admin_edit_feature', feature_id=f.id) }}" class="icon-btn">✏️</a>
        <a href="{{ url_for('admin_delete_feature', feature_id=f.id) }}" class="icon-btn delete-btn" onclick="return confirm('Delete?')">🗑️</a>
      </td>
    </tr>
    {% else %}
    <tr><td colspan="5" class="muted text-center">No features yet.</td></tr>
    {% endfor %}
  </table>
</div>
{% endblock %}
""")


ADMIN_EDIT_FEATURE = ADMIN_HTML.replace("{% block admin_content %}{% endblock %}", """
{% block admin_content %}
<a href="{{ url_for('admin_features') }}" style="color:var(--blue-600);font-weight:600"><i class="fas fa-arrow-left"></i> Back</a>
<div class="card" style="margin-top:20px;max-width:720px">
  <h3 style="margin-bottom:20px">Edit Feature</h3>
  <form method="POST" class="form">
    <div class="form-row">
      <div><label>Title *</label><input type="text" name="title" value="{{ feature.title }}" required style="width:100%"></div>
      <div><label>Icon</label>
        <select name="icon" style="width:100%">
          {% for ic in ['fa-utensils','fa-wifi','fa-shield-alt','fa-broom','fa-tshirt','fa-map-marker-alt','fa-bed','fa-star','fa-heart','fa-award'] %}
          <option value="{{ ic }}" {{ 'selected' if feature.icon == ic else '' }}>{{ ic }}</option>
          {% endfor %}
        </select>
      </div>
    </div>
    <label>Description</label>
    <textarea name="description" rows="3">{{ feature.description or '' }}</textarea>
    <label>Sort order</label>
    <input type="number" name="sort_order" value="{{ feature.sort_order or 0 }}">
    <button class="btn" type="submit"><i class="fas fa-save"></i> Save</button>
  </form>
</div>
{% endblock %}
""")


ADMIN_TESTIMONIALS = ADMIN_HTML.replace("{% block admin_content %}{% endblock %}", """
{% block admin_content %}
<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px">
  <h3>Testimonials</h3>
  <button class="btn btn-sm" onclick="document.getElementById('addTestiForm').style.display='block'"><i class="fas fa-plus"></i> Add</button>
</div>

<div id="addTestiForm" class="card" style="margin-bottom:24px;display:none">
  <h4 style="margin-bottom:16px">Add New Testimonial</h4>
  <form method="POST" action="{{ url_for('admin_add_testimonial') }}" class="form">
    <div class="form-row">
      <div><label>Name *</label><input type="text" name="name" required style="width:100%"></div>
      <div><label>Role</label><input type="text" name="role" style="width:100%"></div>
    </div>
    <div class="form-row">
      <div><label>Avatar (2 letters)</label><input type="text" name="avatar" maxlength="4" style="width:100%"></div>
      <div><label>Stars (1-5)</label><input type="number" name="stars" value="5" min="1" max="5" style="width:100%"></div>
    </div>
    <label>Content *</label>
    <textarea name="content" rows="3" required></textarea>
    <label>Sort order</label>
    <input type="number" name="sort_order" value="0">
    <button class="btn" type="submit">Add Testimonial</button>
  </form>
</div>

<div class="table-wrap">
  <table>
    <tr><th>Order</th><th>Name</th><th>Stars</th><th>Content</th><th>Actions</th></tr>
    {% for t in testimonials %}
    <tr>
      <td>{{ t.sort_order }}</td>
      <td>{{ t.name }}</td>
      <td>{{ '★' * t.stars }}</td>
      <td>{{ t.content[:60] }}...</td>
      <td>
        <a href="{{ url_for('admin_edit_testimonial', testi_id=t.id) }}" class="icon-btn">✏️</a>
        <a href="{{ url_for('admin_delete_testimonial', testi_id=t.id) }}" class="icon-btn delete-btn" onclick="return confirm('Delete?')">🗑️</a>
      </td>
    </tr>
    {% else %}
    <tr><td colspan="5" class="muted text-center">No testimonials yet.</td></tr>
    {% endfor %}
  </table>
</div>
{% endblock %}
""")


ADMIN_EDIT_TESTI = ADMIN_HTML.replace("{% block admin_content %}{% endblock %}", """
{% block admin_content %}
<a href="{{ url_for('admin_testimonials') }}" style="color:var(--blue-600);font-weight:600"><i class="fas fa-arrow-left"></i> Back</a>
<div class="card" style="margin-top:20px;max-width:720px">
  <h3 style="margin-bottom:20px">Edit Testimonial</h3>
  <form method="POST" class="form">
    <div class="form-row">
      <div><label>Name *</label><input type="text" name="name" value="{{ testi.name }}" required style="width:100%"></div>
      <div><label>Role</label><input type="text" name="role" value="{{ testi.role or '' }}" style="width:100%"></div>
    </div>
    <div class="form-row">
      <div><label>Avatar</label><input type="text" name="avatar" maxlength="4" value="{{ testi.avatar or '' }}" style="width:100%"></div>
      <div><label>Stars</label><input type="number" name="stars" value="{{ testi.stars }}" min="1" max="5" style="width:100%"></div>
    </div>
    <label>Content *</label>
    <textarea name="content" rows="3" required>{{ testi.content }}</textarea>
    <label>Sort order</label>
    <input type="number" name="sort_order" value="{{ testi.sort_order or 0 }}">
    <button class="btn" type="submit"><i class="fas fa-save"></i> Save</button>
  </form>
</div>
{% endblock %}
""")


ADMIN_MESSAGES = ADMIN_HTML.replace("{% block admin_content %}{% endblock %}", """
{% block admin_content %}
<h3 style="margin-bottom:16px">Contact Messages</h3>
<div class="table-wrap">
  <table>
    <tr><th>#</th><th>Name</th><th>Email</th><th>Message</th><th>Date</th><th></th></tr>
    {% for m in messages %}
    <tr>
      <td>{{ m.id }}</td>
      <td>{{ m.name }}</td>
      <td>{{ m.email }}</td>
      <td>{{ m.content }}</td>
      <td>{{ m.created_at.strftime('%d %b %Y') }}</td>
      <td><a href="{{ url_for('admin_delete_message', message_id=m.id) }}" class="icon-btn delete-btn" onclick="return confirm('Delete?')">🗑️</a></td>
    </tr>
    {% else %}
    <tr><td colspan="6" class="muted text-center">No messages yet.</td></tr>
    {% endfor %}
  </table>
</div>
{% endblock %}
""")


ADMIN_SETTINGS = ADMIN_HTML.replace("{% block admin_content %}{% endblock %}", """
{% block admin_content %}
<h3 style="margin-bottom:8px">Site Content Editor</h3>
<p class="muted" style="margin-bottom:16px;font-size:.92rem">Edit every text shown on the public site.</p>

<div style="display:flex;gap:8px;flex-wrap:wrap;margin-bottom:24px">
  {% for g in grouped_settings.keys() %}
    <a href="#group-{{ g }}" class="btn btn-outline btn-sm" style="text-transform:capitalize">{{ g|replace('_', ' ') }}</a>
  {% endfor %}
</div>

<form method="POST" action="{{ url_for('admin_update_settings') }}" class="form">
  {% for group, items in grouped_settings.items() %}
    <div class="card" id="group-{{ group }}" style="margin-bottom:20px">
      <h4 style="margin-bottom:16px;text-transform:capitalize;color:var(--blue-700);font-size:1.1rem">
        {{ group|replace('_', ' ')|title }}
      </h4>
      <div style="display:grid;grid-template-columns:1fr 2fr;gap:12px 16px;align-items:center">
        {% for s in items %}
          <label style="font-size:.9rem;font-weight:600;color:var(--blue-900)">
            {{ s.label or s.key }}
            <div style="font-size:.72rem;color:var(--gray-500);font-weight:400;margin-top:2px">key: {{ s.key }}</div>
          </label>
          {% set long_fields = ['subtitle','about','description','footer_about','about_p1','about_p2','about_p3','address','office_hours_detailed','hero_title'] %}
          {% if s.key in long_fields or s.key.endswith('subtitle') or s.key.endswith('description') or s.key.startswith('about_p') %}
            <textarea name="{{ s.key }}" rows="2" style="padding:10px 12px;border-radius:10px;border:1.5px solid var(--gray-200);font-family:inherit;font-size:.9rem">{{ s.value or '' }}</textarea>
          {% else %}
            <input type="text" name="{{ s.key }}" value="{{ s.value or '' }}" style="padding:10px 12px;border-radius:10px;border:1.5px solid var(--gray-200);font-family:inherit;font-size:.9rem">
          {% endif %}
        {% endfor %}
      </div>
    </div>
  {% endfor %}
  <div style="position:sticky;bottom:20px;background:var(--white);padding:16px;border-radius:12px;box-shadow:var(--shadow-lg);border:1px solid var(--blue-100)">
    <button class="btn btn-lg" type="submit" style="width:100%"><i class="fas fa-save"></i> Save All Settings</button>
  </div>
</form>

<style>
  @media(max-width:700px){
    form > .card > div[style*="grid-template-columns"] { grid-template-columns:1fr !important; }
  }
</style>
{% endblock %}
""")


ADMIN_ACCOUNT = ADMIN_HTML.replace("{% block admin_content %}{% endblock %}", """
{% block admin_content %}
<h3 style="margin-bottom:16px">Account Settings</h3>
<div class="card" style="max-width:520px">
  <h4 style="margin-bottom:16px">Change Password</h4>
  <form method="POST" action="{{ url_for('admin_change_password') }}" class="form">
    <label>Current Password</label>
    <input type="password" name="current" required>
    <label>New Password</label>
    <input type="password" name="new" required minlength="6">
    <label>Confirm New Password</label>
    <input type="password" name="confirm" required minlength="6">
    <button class="btn" type="submit"><i class="fas fa-lock"></i> Update Password</button>
  </form>
</div>
{% endblock %}
""")


# ============================================================
# PUBLIC ROUTES
# ============================================================
def render_base(template, **kwargs):
    ctx = {
        'site': all_settings(),
        'footer_rooms': Room.query.filter_by(is_active=True).limit(4).all(),
        'current_year': datetime.utcnow().year,
    }
    ctx.update(kwargs)
    return render_template_string(template, **ctx)


@app.route('/')
def index():
    rooms = Room.query.filter_by(is_active=True).limit(3).all()
    features = Feature.query.order_by(Feature.sort_order).all()
    testimonials = Testimonial.query.order_by(Testimonial.sort_order).all()
    return render_base(INDEX_HTML, rooms=rooms, features=features, testimonials=testimonials)


@app.route('/rooms')
def rooms():
    all_rooms = Room.query.filter_by(is_active=True).all()
    return render_base(ROOMS_HTML, rooms=all_rooms)


@app.route('/room/<int:room_id>')
def room_detail(room_id):
    room = Room.query.get_or_404(room_id)
    return render_base(ROOM_DETAIL_HTML, room=room)


@app.route('/staff')
def staff():
    members = Staff.query.filter_by(is_active=True).all()
    return render_base(STAFF_HTML, members=members)


@app.route('/about')
def about():
    features = Feature.query.order_by(Feature.sort_order).all()
    return render_base(ABOUT_HTML, features=features)


@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        msg = Message(
            name=request.form['name'],
            email=request.form['email'],
            content=request.form['content']
        )
        db.session.add(msg)
        db.session.commit()
        success_msg = all_settings().get('contact_success_msg',
            "Thank you! Your message has been sent. We'll respond within 24 hours.")
        flash(success_msg, 'success')
        return redirect(url_for('contact'))
    return render_base(CONTACT_HTML)


@app.route('/book/<int:room_id>', methods=['POST'])
def book(room_id):
    room = Room.query.get_or_404(room_id)
    if room.available_beds < 1:
        flash('Sorry, this room is fully occupied.', 'error')
        return redirect(url_for('room_detail', room_id=room_id))

    booking = Booking(
        guest_name=request.form['guest_name'],
        occupation=request.form.get('occupation', ''),
        email=request.form['email'],
        phone=request.form['phone'],
        message=request.form.get('message', ''),
        room_id=room_id
    )
    db.session.add(booking)
    db.session.commit()
    success_msg = all_settings().get('booking_success_msg',
        'Booking request received! Our team will contact you within 24 hours.')
    flash(success_msg, 'success')
    return redirect(url_for('index'))


# ============================================================
# ADMIN AUTH
# ============================================================
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        admin = Admin.query.filter_by(username=username).first()
        if admin and check_password_hash(admin.password_hash, password):
            session['admin_id'] = admin.id
            flash('Welcome back! Logged in successfully.', 'success')
            return redirect(url_for('admin_dashboard'))
        flash('Invalid username or password.', 'error')
    return render_base(LOGIN_HTML)


@app.route('/logout')
def logout():
    session.pop('admin_id', None)
    flash('You have been logged out.', 'success')
    return redirect(url_for('index'))


# ============================================================
# ADMIN HELPERS
# ============================================================
def admin_stats():
    return {
        'total_bookings': Booking.query.count(),
        'pending': Booking.query.filter_by(status='pending').count(),
        'confirmed': Booking.query.filter_by(status='confirmed').count(),
        'total_rooms': Room.query.count(),
        'total_staff': Staff.query.count(),
        'total_messages': Message.query.count(),
    }


def render_admin(template, **kwargs):
    ctx = {
        'site': all_settings(),
        'footer_rooms': Room.query.filter_by(is_active=True).limit(4).all(),
        'current_year': datetime.utcnow().year,
        'stats': admin_stats(),
    }
    ctx.update(kwargs)
    return render_template_string(template, **ctx)


# ============================================================
# ADMIN ROUTES
# ============================================================
@app.route('/admin')
@login_required
def admin_dashboard():
    return render_admin(
        ADMIN_OVERVIEW, tab='overview',
        recent_bookings=Booking.query.order_by(Booking.created_at.desc()).limit(5).all(),
        recent_messages=Message.query.order_by(Message.created_at.desc()).limit(5).all()
    )


@app.route('/admin/bookings')
@login_required
def admin_bookings():
    bookings = Booking.query.order_by(Booking.created_at.desc()).all()
    return render_admin(ADMIN_BOOKINGS, tab='bookings', bookings=bookings)


@app.route('/admin/booking/<int:booking_id>/<status>')
@login_required
def update_booking(booking_id, status):
    booking = Booking.query.get_or_404(booking_id)
    if status in ['confirmed', 'rejected', 'pending']:
        old = booking.status
        booking.status = status
        if old != 'confirmed' and status == 'confirmed' and booking.room.available_beds > 0:
            booking.room.available_beds -= 1
        elif old == 'confirmed' and status != 'confirmed' and booking.room.available_beds < booking.room.beds:
            booking.room.available_beds += 1
        db.session.commit()
        flash(f'Booking #{booking.id} marked as {status}.', 'success')
    return redirect(url_for('admin_bookings'))


@app.route('/admin/booking/<int:booking_id>/delete')
@login_required
def admin_delete_booking(booking_id):
    b = Booking.query.get_or_404(booking_id)
    db.session.delete(b)
    db.session.commit()
    flash('Booking deleted.', 'success')
    return redirect(url_for('admin_bookings'))


@app.route('/admin/rooms')
@login_required
def admin_rooms():
    rooms = Room.query.order_by(Room.id).all()
    return render_admin(ADMIN_ROOMS, tab='rooms', rooms=rooms)


@app.route('/admin/room/add', methods=['POST'])
@login_required
def admin_add_room():
    room = Room(
        name=request.form['name'], sharing=request.form['sharing'],
        floor=request.form['floor'], price=int(request.form['price']),
        duration=request.form.get('duration', ''),
        beds=int(request.form['beds']), available_beds=int(request.form['beds']),
        description=request.form['description'],
        icon=request.form.get('icon', 'fa-bed'), is_active=True
    )
    db.session.add(room)
    db.session.commit()
    flash('Room added.', 'success')
    return redirect(url_for('admin_rooms'))


@app.route('/admin/room/<int:room_id>/edit', methods=['GET', 'POST'])
@login_required
def admin_edit_room(room_id):
    room = Room.query.get_or_404(room_id)
    if request.method == 'POST':
        room.name = request.form['name']
        room.sharing = request.form['sharing']
        room.floor = request.form['floor']
        room.price = int(request.form['price'])
        room.duration = request.form.get('duration', '')
        room.beds = int(request.form['beds'])
        room.available_beds = int(request.form['available_beds'])
        room.description = request.form['description']
        room.icon = request.form.get('icon', 'fa-bed')
        room.is_active = 'is_active' in request.form
        db.session.commit()
        flash('Room updated.', 'success')
        return redirect(url_for('admin_rooms'))
    return render_admin(ADMIN_EDIT_ROOM, tab='rooms', room=room)


@app.route('/admin/room/<int:room_id>/delete')
@login_required
def admin_delete_room(room_id):
    room = Room.query.get_or_404(room_id)
    Booking.query.filter_by(room_id=room_id).delete()
    db.session.delete(room)
    db.session.commit()
    flash('Room deleted.', 'success')
    return redirect(url_for('admin_rooms'))


@app.route('/admin/staff')
@login_required
def admin_staff():
    staff = Staff.query.order_by(Staff.id).all()
    return render_admin(ADMIN_STAFF, tab='staff', staff=staff)


@app.route('/admin/staff/add', methods=['POST'])
@login_required
def admin_add_staff():
    s = Staff(
        name=request.form['name'], role=request.form['role'],
        qualification=request.form.get('qualification', ''),
        experience=request.form.get('experience', ''),
        bio=request.form.get('bio', ''),
        icon=request.form.get('icon', 'fa-user-tie'), is_active=True
    )
    db.session.add(s)
    db.session.commit()
    flash('Staff added.', 'success')
    return redirect(url_for('admin_staff'))


@app.route('/admin/staff/<int:staff_id>/edit', methods=['GET', 'POST'])
@login_required
def admin_edit_staff(staff_id):
    member = Staff.query.get_or_404(staff_id)
    if request.method == 'POST':
        member.name = request.form['name']
        member.role = request.form['role']
        member.qualification = request.form.get('qualification', '')
        member.experience = request.form.get('experience', '')
        member.bio = request.form.get('bio', '')
        member.icon = request.form.get('icon', 'fa-user-tie')
        member.is_active = 'is_active' in request.form
        db.session.commit()
        flash('Staff updated.', 'success')
        return redirect(url_for('admin_staff'))
    return render_admin(ADMIN_EDIT_STAFF, tab='staff', member=member)


@app.route('/admin/staff/<int:staff_id>/delete')
@login_required
def admin_delete_staff(staff_id):
    s = Staff.query.get_or_404(staff_id)
    db.session.delete(s)
    db.session.commit()
    flash('Staff deleted.', 'success')
    return redirect(url_for('admin_staff'))


@app.route('/admin/features')
@login_required
def admin_features():
    features = Feature.query.order_by(Feature.sort_order).all()
    return render_admin(ADMIN_FEATURES, tab='features', features=features)


@app.route('/admin/feature/add', methods=['POST'])
@login_required
def admin_add_feature():
    f = Feature(
        title=request.form['title'],
        description=request.form.get('description', ''),
        icon=request.form.get('icon', 'fa-star'),
        sort_order=int(request.form.get('sort_order', 0))
    )
    db.session.add(f)
    db.session.commit()
    flash('Feature added.', 'success')
    return redirect(url_for('admin_features'))


@app.route('/admin/feature/<int:feature_id>/edit', methods=['GET', 'POST'])
@login_required
def admin_edit_feature(feature_id):
    feature = Feature.query.get_or_404(feature_id)
    if request.method == 'POST':
        feature.title = request.form['title']
        feature.description = request.form.get('description', '')
        feature.icon = request.form.get('icon', 'fa-star')
        feature.sort_order = int(request.form.get('sort_order', 0))
        db.session.commit()
        flash('Feature updated.', 'success')
        return redirect(url_for('admin_features'))
    return render_admin(ADMIN_EDIT_FEATURE, tab='features', feature=feature)


@app.route('/admin/feature/<int:feature_id>/delete')
@login_required
def admin_delete_feature(feature_id):
    f = Feature.query.get_or_404(feature_id)
    db.session.delete(f)
    db.session.commit()
    flash('Feature deleted.', 'success')
    return redirect(url_for('admin_features'))


@app.route('/admin/testimonials')
@login_required
def admin_testimonials():
    testis = Testimonial.query.order_by(Testimonial.sort_order).all()
    return render_admin(ADMIN_TESTIMONIALS, tab='testimonials', testimonials=testis)


@app.route('/admin/testimonial/add', methods=['POST'])
@login_required
def admin_add_testimonial():
    t = Testimonial(
        name=request.form['name'],
        role=request.form.get('role', ''),
        avatar=request.form.get('avatar', ''),
        stars=int(request.form.get('stars', 5)),
        content=request.form['content'],
        sort_order=int(request.form.get('sort_order', 0))
    )
    db.session.add(t)
    db.session.commit()
    flash('Testimonial added.', 'success')
    return redirect(url_for('admin_testimonials'))


@app.route('/admin/testimonial/<int:testi_id>/edit', methods=['GET', 'POST'])
@login_required
def admin_edit_testimonial(testi_id):
    testi = Testimonial.query.get_or_404(testi_id)
    if request.method == 'POST':
        testi.name = request.form['name']
        testi.role = request.form.get('role', '')
        testi.avatar = request.form.get('avatar', '')
        testi.stars = int(request.form.get('stars', 5))
        testi.content = request.form['content']
        testi.sort_order = int(request.form.get('sort_order', 0))
        db.session.commit()
        flash('Testimonial updated.', 'success')
        return redirect(url_for('admin_testimonials'))
    return render_admin(ADMIN_EDIT_TESTI, tab='testimonials', testi=testi)


@app.route('/admin/testimonial/<int:testi_id>/delete')
@login_required
def admin_delete_testimonial(testi_id):
    t = Testimonial.query.get_or_404(testi_id)
    db.session.delete(t)
    db.session.commit()
    flash('Testimonial deleted.', 'success')
    return redirect(url_for('admin_testimonials'))


@app.route('/admin/messages')
@login_required
def admin_messages():
    messages = Message.query.order_by(Message.created_at.desc()).all()
    return render_admin(ADMIN_MESSAGES, tab='messages', messages=messages)


@app.route('/admin/message/<int:message_id>/delete')
@login_required
def admin_delete_message(message_id):
    m = Message.query.get_or_404(message_id)
    db.session.delete(m)
    db.session.commit()
    flash('Message deleted.', 'success')
    return redirect(url_for('admin_messages'))


@app.route('/admin/settings', methods=['GET', 'POST'])
@login_required
def admin_settings():
    if request.method == 'POST':
        for key, value in request.form.items():
            s = SiteSetting.query.filter_by(key=key).first()
            if s:
                s.value = value
        db.session.commit()
        flash('All settings saved.', 'success')
        return redirect(url_for('admin_settings'))

    settings = SiteSetting.query.order_by(SiteSetting.group, SiteSetting.id).all()
    grouped = {}
    for s in settings:
        grouped.setdefault(s.group or 'general', []).append(s)
    return render_admin(ADMIN_SETTINGS, tab='settings', grouped_settings=grouped)


@app.route('/admin/account', methods=['GET'])
@login_required
def admin_account():
    return render_admin(ADMIN_ACCOUNT, tab='account')


@app.route('/admin/account/password', methods=['POST'])
@login_required
def admin_change_password():
    admin = Admin.query.get(session['admin_id'])
    current = request.form['current']
    new = request.form['new']
    confirm = request.form['confirm']
    if not check_password_hash(admin.password_hash, current):
        flash('Current password is incorrect.', 'error')
    elif new != confirm:
        flash('New passwords do not match.', 'error')
    elif len(new) < 6:
        flash('Password must be at least 6 characters.', 'error')
    else:
        admin.password_hash = generate_password_hash(new)
        db.session.commit()
        flash('Password updated.', 'success')
    return redirect(url_for('admin_account'))


# ============================================================
# DEFAULT SETTINGS — EVERY visible text editable
# ============================================================
DEFAULT_SETTINGS = [
    # ==================== GENERAL / CONTACT ====================
    ('site_name', 'Kant PG', 'Site Name', 'general'),
    ('tagline', 'Comfort Since 2018', 'Tagline', 'general'),
    ('phone', '+91 98765 43210', 'Phone (primary)', 'general'),
    ('phone_secondary', '+91 98765 43211', 'Phone (secondary)', 'general'),
    ('email', 'stay@kantpg.com', 'Email (primary)', 'general'),
    ('email_secondary', 'bookings@kantpg.com', 'Email (secondary)', 'general'),
    ('address', '123 Green Park, Near Metro Station, New Delhi, 110016', 'Full Address', 'general'),
    ('office_hours', 'Office: 8:00 AM – 9:00 PM', 'Office Hours (topbar)', 'general'),
    ('office_hours_detailed', 'Mon–Sat: 8:00 AM – 9:00 PM\nSunday: 10:00 AM – 5:00 PM', 'Detailed Hours (contact page)', 'general'),
    ('facebook', '#', 'Facebook URL', 'general'),
    ('instagram', '#', 'Instagram URL', 'general'),
    ('youtube', '#', 'YouTube URL', 'general'),
    ('whatsapp', '#', 'WhatsApp URL', 'general'),
    ('footer_about', 'A premium paying-guest residence for students and working professionals. Safe, comfortable, and always welcoming.', 'Footer About Text', 'general'),
    ('footer_copyright', 'All rights reserved · Designed with care.', 'Footer Copyright', 'general'),
    ('footer_links_title', 'Quick Links', 'Footer — Links Column Title', 'general'),
    ('footer_rooms_title', 'Room Types', 'Footer — Rooms Column Title', 'general'),
    ('footer_contact_title', 'Get in Touch', 'Footer — Contact Column Title', 'general'),

    # ==================== NAVBAR ====================
    ('nav_home', 'Home', 'Navbar — Home', 'navbar'),
    ('nav_rooms', 'Rooms', 'Navbar — Rooms', 'navbar'),
    ('nav_staff', 'Our Team', 'Navbar — Our Team', 'navbar'),
    ('nav_about', 'About', 'Navbar — About', 'navbar'),
    ('nav_contact', 'Contact', 'Navbar — Contact', 'navbar'),
    ('nav_cta', 'Book a Room', 'Navbar — CTA Button', 'navbar'),

    # ==================== HERO ====================
    ('hero_eyebrow', 'Trusted by 1200+ residents', 'Hero — Eyebrow Badge', 'hero'),
    ('hero_title', 'Where <span class="accent">Comfort Meets Convenience</span>', 'Hero — Title (HTML allowed)', 'hero'),
    ('hero_subtitle', 'A premium paying-guest residence built for students and working professionals. Clean rooms, home-style meals, high-speed WiFi, and a location that keeps you connected.', 'Hero — Subtitle', 'hero'),
    ('hero_cta1', 'Explore Rooms', 'Hero — Button 1', 'hero'),
    ('hero_cta2', 'Book a Visit', 'Hero — Button 2', 'hero'),
    ('stat1_num', '7+', 'Stat 1 — Number', 'hero'),
    ('stat1_label', 'Years of Trust', 'Stat 1 — Label', 'hero'),
    ('stat2_num', '1200+', 'Stat 2 — Number', 'hero'),
    ('stat2_label', 'Happy Residents', 'Stat 2 — Label', 'hero'),
    ('stat3_num', '4.8★', 'Stat 3 — Number', 'hero'),
    ('stat3_label', 'Average Rating', 'Stat 3 — Label', 'hero'),
    ('stat4_num', '24/7', 'Stat 4 — Number', 'hero'),
    ('stat4_label', 'Security', 'Stat 4 — Label', 'hero'),
    ('hv_heading', 'Available Rooms', 'Hero Card — Heading', 'hero'),
    ('hv_badge', 'Live Now', 'Hero Card — Badge', 'hero'),
    ('hv_cta', 'View All Rooms', 'Hero Card — Button', 'hero'),

    # ==================== HOME SECTIONS ====================
    ('why_eyebrow', 'Why Choose Us', 'Why Section — Eyebrow', 'sections'),
    ('why_title', 'More Than Just a Room', 'Why Section — Title', 'sections'),
    ('why_subtitle', 'Kant PG combines the safety of home with the independence of independent living.', 'Why Section — Subtitle', 'sections'),
    ('rooms_eyebrow', 'Our Rooms', 'Home Rooms — Eyebrow', 'sections'),
    ('rooms_title', 'Find Your Perfect Space', 'Home Rooms — Title', 'sections'),
    ('rooms_subtitle', 'From budget-friendly sharing to premium private rooms — pick what fits your lifestyle.', 'Home Rooms — Subtitle', 'sections'),
    ('rooms_tag_available', 'Available', 'Room Card — Available Tag', 'sections'),
    ('rooms_tag_full', 'Full', 'Room Card — Full Tag', 'sections'),
    ('rooms_price_suffix', '/mo', 'Room Card — Price Suffix', 'sections'),
    ('rooms_beds_label', 'beds left', 'Room Card — Beds Label', 'sections'),
    ('rooms_btn', 'Details', 'Room Card — Button', 'sections'),
    ('rooms_cta', 'View All Rooms', 'Home Rooms — Bottom CTA', 'sections'),
    ('testi_eyebrow', 'Testimonials', 'Testimonials — Eyebrow', 'sections'),
    ('testi_title', 'What Our Residents Say', 'Testimonials — Title', 'sections'),
    ('testi_subtitle', 'Real experiences from the people who call Kant PG home.', 'Testimonials — Subtitle', 'sections'),
    ('cta_title', 'Ready to Move In?', 'CTA Banner — Title', 'sections'),
    ('cta_subtitle', 'Schedule a visit today — see the rooms, meet the team, and feel at home.', 'CTA Banner — Subtitle', 'sections'),
    ('cta_btn1', 'Book a Visit', 'CTA Banner — Button 1', 'sections'),
    ('cta_btn2', 'Call Us', 'CTA Banner — Button 2', 'sections'),

    # ==================== ROOMS PAGE ====================
    ('rooms_page_eyebrow', 'All Rooms', 'Rooms Page — Eyebrow', 'rooms_page'),
    ('rooms_page_title', 'Our Complete Room Catalogue', 'Rooms Page — Title', 'rooms_page'),
    ('rooms_page_subtitle', 'Choose the room that fits your budget and lifestyle.', 'Rooms Page — Subtitle', 'rooms_page'),
    ('rooms_page_btn', 'Book', 'Rooms Page — Card Button', 'rooms_page'),

    # ==================== ROOM DETAIL ====================
    ('room_detail_back', 'Back to all rooms', 'Room Detail — Back Link', 'room_detail'),
    ('room_detail_badge', 'No brokerage · Free visit', 'Room Detail — Badge', 'room_detail'),
    ('room_detail_beds_label', 'beds available', 'Room Detail — Beds Label', 'room_detail'),
    ('room_detail_form_title', 'Reserve Your Bed', 'Room Detail — Form Title', 'room_detail'),
    ('room_detail_full_msg', 'This room is currently full. Please contact us to join the waitlist.', 'Room Detail — Full Message', 'room_detail'),

    # ==================== BOOKING FORM ====================
    ('booking_label_name', 'Full Name *', 'Booking — Name Label', 'booking'),
    ('booking_label_occupation', 'Occupation', 'Booking — Occupation Label', 'booking'),
    ('booking_label_email', 'Email *', 'Booking — Email Label', 'booking'),
    ('booking_label_phone', 'Phone *', 'Booking — Phone Label', 'booking'),
    ('booking_label_message', 'Message', 'Booking — Message Label', 'booking'),
    ('booking_form_btn', 'Submit Booking Request', 'Booking — Submit Button', 'booking'),
    ('booking_success_msg', 'Booking request received! Our team will contact you within 24 hours.', 'Booking — Success Message', 'booking'),

    # ==================== STAFF PAGE ====================
    ('staff_eyebrow', 'Our Team', 'Staff Page — Eyebrow', 'staff_page'),
    ('staff_title', 'Meet the People Behind Kant PG', 'Staff Page — Title', 'staff_page'),
    ('staff_subtitle', 'Wardens, managers, and support staff who make your stay safe and comfortable.', 'Staff Page — Subtitle', 'staff_page'),

    # ==================== ABOUT PAGE ====================
    ('about_eyebrow', 'About Us', 'About — Eyebrow', 'about'),
    ('about_title', 'Seven Years of Welcoming Residents', 'About — Title', 'about'),
    ('about_subtitle', 'Since 2018, Kant PG has been a trusted home for students and professionals.', 'About — Subtitle', 'about'),
    ('about_story_heading', 'Our Story', 'About — Story Heading', 'about'),
    ('about_p1', 'Kant PG started with a single building and a simple belief: everyone deserves a safe, comfortable place to call home while they pursue their goals.', 'About — Paragraph 1', 'about'),
    ('about_p2', 'Today we accommodate 120+ residents across multiple floors — but our core philosophy remains unchanged.', 'About — Paragraph 2', 'about'),
    ('about_p3', 'From first-year students to working professionals, thousands have passed through our doors.', 'About — Paragraph 3', 'about'),
    ('about_stat1_num', '7+', 'About — Stat 1 Number', 'about'),
    ('about_stat1_label', 'Years of Trust', 'About — Stat 1 Label', 'about'),
    ('about_stat2_num', '1200+', 'About — Stat 2 Number', 'about'),
    ('about_stat2_label', 'Happy Residents', 'About — Stat 2 Label', 'about'),
    ('about_stat3_num', '4.8★', 'About — Stat 3 Number', 'about'),
    ('about_stat3_label', 'Average Rating', 'About — Stat 3 Label', 'about'),
    ('about_stat4_num', '24/7', 'About — Stat 4 Number', 'about'),
    ('about_stat4_label', 'Security', 'About — Stat 4 Label', 'about'),
    ('about_values_heading', 'Our Values', 'About — Values Heading', 'about'),

    # ==================== CONTACT PAGE ====================
    ('contact_eyebrow', 'Get in Touch', 'Contact — Eyebrow', 'contact'),
    ('contact_title', "We'd Love to Hear From You", 'Contact — Title', 'contact'),
    ('contact_subtitle', 'Book a visit, ask about availability, or just say hello — we respond within 24 hours.', 'Contact — Subtitle', 'contact'),
    ('contact_info_heading', 'Contact Information', 'Contact — Info Heading', 'contact'),
    ('contact_label_address', 'Visit Our PG', 'Contact — Address Label', 'contact'),
    ('contact_label_phone', 'Call Us', 'Contact — Phone Label', 'contact'),
    ('contact_label_email', 'Email Us', 'Contact — Email Label', 'contact'),
    ('contact_label_hours', 'Office Hours', 'Contact — Hours Label', 'contact'),
    ('contact_form_title', 'Send Us a Message', 'Contact — Form Title', 'contact'),
    ('contact_form_name_label', 'Your Name *', 'Contact — Name Field Label', 'contact'),
    ('contact_form_email_label', 'Email *', 'Contact — Email Field Label', 'contact'),
    ('contact_form_message_label', 'Message *', 'Contact — Message Field Label', 'contact'),
    ('contact_form_btn', 'Send Message', 'Contact — Submit Button', 'contact'),
    ('contact_success_msg', "Thank you! Your message has been sent. We'll respond within 24 hours.", 'Contact — Success Message', 'contact'),

    # ==================== LOGIN ====================
    ('login_title', 'Admin Login', 'Login — Title', 'login'),
    ('login_subtitle', 'Access the management dashboard', 'Login — Subtitle', 'login'),
]


# ============================================================
# SEED DATABASE
# ============================================================
def seed_database():
    from sqlalchemy import inspect

    try:
        db.create_all()
        inspector = inspect(db.engine)
        if 'room' in inspector.get_table_names():
            cols = [c['name'] for c in inspector.get_columns('room')]
            if 'sharing' not in cols:
                print("⚠️  Old schema detected. Rebuilding...")
                db.drop_all()
                db.create_all()
        if 'site_setting' not in inspector.get_table_names():
            print("⚠️  Missing site_setting table. Rebuilding...")
            db.drop_all()
            db.create_all()
    except Exception as e:
        print(f"⚠️  Rebuild triggered: {e}")
        db.drop_all()
        db.create_all()

    # Admin
    if not Admin.query.first():
        db.session.add(Admin(
            username='admin',
            password_hash=generate_password_hash('kant@123')
        ))

    # Settings
    for key, val, label, group in DEFAULT_SETTINGS:
        if not SiteSetting.query.filter_by(key=key).first():
            db.session.add(SiteSetting(key=key, value=val, label=label, group=group))

    # Rooms
    if not Room.query.first():
        rooms_data = [
            {'name': 'Deluxe Single Room', 'sharing': 'Single', 'floor': '2nd Floor · AC', 'price': 9500,
             'duration': '3 months', 'beds': 8,
             'description': 'Private AC room with attached bathroom, study table, wardrobe, and balcony access. Includes meals, WiFi, and daily housekeeping.',
             'icon': 'fa-user'},
            {'name': 'Comfort Double Sharing', 'sharing': 'Double', 'floor': '1st Floor · AC', 'price': 6800,
             'duration': '3 months', 'beds': 12,
             'description': 'Spacious twin-sharing room with individual wardrobes, attached bath, and a shared balcony. All-inclusive rent.',
             'icon': 'fa-user-friends'},
            {'name': 'Smart Triple Sharing', 'sharing': 'Triple', 'floor': 'Ground Floor · Non-AC', 'price': 5200,
             'duration': '3 months', 'beds': 9,
             'description': 'Budget-friendly triple sharing with personal lockers, study area, and attached bath. Ideal for students.',
             'icon': 'fa-users'},
            {'name': 'Premium Single Suite', 'sharing': 'Premium Single', 'floor': '3rd Floor · AC', 'price': 12500,
             'duration': '6 months', 'beds': 4,
             'description': 'Extra-large premium single room with attached bath, personal fridge, garden view, and priority housekeeping.',
             'icon': 'fa-crown'},
        ]
        for r in rooms_data:
            db.session.add(Room(available_beds=r['beds'], is_active=True, **r))

    # Staff
    if not Staff.query.first():
        staff_data = [
            {'name': 'Mr. Rajesh Kant', 'role': 'Founder & Manager', 'qualification': 'MBA', 'experience': '12 years',
             'bio': 'Founder of Kant PG. Personally oversees operations with a focus on resident comfort and safety.',
             'icon': 'fa-user-tie'},
            {'name': 'Mrs. Anjali Verma', 'role': 'Head Warden', 'qualification': 'B.A.', 'experience': '8 years',
             'bio': 'Resident warden known for her warmth and vigilance. Available 24/7 for any resident need.',
             'icon': 'fa-user-shield'},
            {'name': 'Mr. Suresh Nair', 'role': 'Kitchen Supervisor', 'qualification': 'Hotel Management', 'experience': '10 years',
             'bio': 'Leads the kitchen team, ensuring meals are fresh, hygienic, and home-style every single day.',
             'icon': 'fa-user-tie'},
            {'name': 'Ms. Meera Iyer', 'role': 'Housekeeping Manager', 'qualification': 'Diploma', 'experience': '6 years',
             'bio': 'Maintains spotless rooms and common areas with a keen eye for detail.',
             'icon': 'fa-user-cog'},
        ]
        for s in staff_data:
            db.session.add(Staff(is_active=True, **s))

    # Features
    if not Feature.query.first():
        features_data = [
            {'icon': 'fa-utensils', 'title': 'Home-Style Meals', 'description': 'Freshly cooked breakfast and dinner daily — nutritious, hygienic, and comforting.', 'sort_order': 1},
            {'icon': 'fa-wifi', 'title': 'High-Speed WiFi', 'description': 'Uninterrupted fibre internet throughout the building — perfect for work and study.', 'sort_order': 2},
            {'icon': 'fa-shield-alt', 'title': '24/7 Security', 'description': 'CCTV surveillance and on-site warden ensure a safe environment at all hours.', 'sort_order': 3},
            {'icon': 'fa-broom', 'title': 'Daily Housekeeping', 'description': 'Rooms and common areas cleaned daily so you can focus on what matters.', 'sort_order': 4},
            {'icon': 'fa-tshirt', 'title': 'Laundry Service', 'description': 'Convenient laundry with pick-up and drop-off to save you time each week.', 'sort_order': 5},
            {'icon': 'fa-map-marker-alt', 'title': 'Prime Location', 'description': '2 minutes from the metro station, with markets, cafes, and hospitals nearby.', 'sort_order': 6},
        ]
        for f in features_data:
            db.session.add(Feature(**f))

    # Testimonials
    if not Testimonial.query.first():
        testi_data = [
            {'name': 'Priya Sharma', 'role': 'Resident · 2 years', 'avatar': 'PS', 'stars': 5,
             'content': "I moved here for my first job and Kant PG felt like home within a week. The meals are genuinely home-style, and the staff is always ready to help.",
             'sort_order': 1},
            {'name': 'Arjun Kapoor', 'role': 'Resident · 1 year', 'avatar': 'AK', 'stars': 5,
             'content': "Clean rooms, reliable WiFi, and unbeatable location. As a student, I couldn't ask for a better setup. The warden genuinely cares about everyone's well-being.",
             'sort_order': 2},
            {'name': 'Rakesh Mehta', 'role': 'Parent of resident', 'avatar': 'RM', 'stars': 5,
             'content': "The security here is exceptional — CCTV, a resident warden, and strict visitor rules. As a parent, I feel completely at peace knowing my daughter is safe.",
             'sort_order': 3},
        ]
        for t in testi_data:
            db.session.add(Testimonial(**t))

    db.session.commit()

# MAIN
# ============================================================

# 1. Run this ALWAYS (so Vercel creates the tables in Neon)
with app.app_context():
    seed_database()

# 2. Run this ONLY when testing locally on your PC
if __name__ == '__main__':
  with app.app_context():
    seed_database()

# 2. This is ONLY for running locally on your PC
if __name__ == '__main__':
   # ... (Your routes and admin code above this) ...

# ============================================================
# SEED DATABASE
# ============================================================
def seed_database():
    # ... (this function is already in your file) ...
    db.session.commit()

# ============================================================
# MAIN  <--- PASTE IT RIGHT HERE AT THE VERY BOTTOM
# ============================================================

# 1. THIS MUST BE OUTSIDE THE IF BLOCK
with app.app_context():
    seed_database()

# 2. This is ONLY for local testing
if __name__ == '__main__':
    print("=" * 60)
    print("  Kant PG · Full CMS · Every text editable")
    print("=" * 60)
    print("  URL:     http://127.0.0.1:5000")
    print("  Admin:   http://127.0.0.1:5000/login")
    print("  Login:   admin / kant@123")
    print("=" * 60)
    app.run(debug=True)

