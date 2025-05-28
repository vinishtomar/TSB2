import os
import csv
from flask import Flask, render_template, request, redirect, url_for, flash, Response, send_file, session
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_bcrypt import Bcrypt
from flask_sqlalchemy import SQLAlchemy
from io import StringIO, BytesIO
from datetime import datetime

app = Flask(__name__)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = "login"
app.secret_key = os.urandom(24)

# PostgreSQL config (replace with your own DB URI if needed)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite3'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

os.makedirs('uploads', exist_ok=True)

# User model
class DBUser(db.Model):
    id = db.Column(db.String(255), primary_key=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), nullable=False, default="user")

class User(UserMixin):
    def __init__(self, id):
        self.id = id
        user = DBUser.query.filter_by(id=id).first()
        self.role = user.role if user else "user"

@login_manager.user_loader
def load_user(user_id):
    user = DBUser.query.filter_by(id=user_id).first()
    if user:
        u = User(user_id)
        u.role = user.role
        return u
    return None

class SuiviJournalier(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.String(50))
    chantier_du_jour = db.Column(db.String(255))
    equipe_presente = db.Column(db.String(255))
    heures_travail = db.Column(db.String(255))
    materiel_livre = db.Column(db.String(255))
    travaux_realises = db.Column(db.String(255))
    problemes = db.Column(db.String(255))
    avancement = db.Column(db.String(255))
    objectif_special = db.Column(db.String(255))
    cable_dc = db.Column(db.String(255))
    cable_ac = db.Column(db.String(255))
    nombre_rail = db.Column(db.String(255))
    pose_onduleur = db.Column(db.String(255))
    cable_terre = db.Column(db.String(255))
    utilisateur = db.Column(db.String(255))
    images = db.relationship('SuiviJournalierImage', backref='suivi', lazy=True)

class SuiviJournalierImage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    suivi_id = db.Column(db.Integer, db.ForeignKey('suivi_journalier.id'), nullable=False)
    filename = db.Column(db.String(255))
    content_type = db.Column(db.String(255))
    data = db.Column(db.LargeBinary)

with app.app_context():
    db.create_all()
    if not DBUser.query.filter_by(id="admin").first():
        pw = bcrypt.generate_password_hash("admin").decode("utf-8")
        db.session.add(DBUser(id="admin", password_hash=pw, role="admin"))
        db.session.commit()

@app.route('/')
@login_required
def index():
    # For admin, get all lines for history tab
    all_lignes = []
    if current_user.role == "admin":
        all_lignes = SuiviJournalier.query.all()
    return render_template('index.html', all_lignes=all_lignes)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        chantier_type = request.form.get('chantier_type')
        user = DBUser.query.filter_by(id=username).first()
        if user and bcrypt.check_password_hash(user.password_hash, password):
            user_obj = User(user.id)
            user_obj.role = user.role
            login_user(user_obj)
            session['chantier_type'] = chantier_type
            return redirect(url_for('index'))
        flash("Incorrect username or password", "danger")
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    session.clear()
    return redirect(url_for('login'))

@app.route('/suivi-journalier', methods=['GET', 'POST'])
@login_required
def suivi_journalier():
    if request.method == 'POST':
        try:
            data = {k: request.form.get(k, "") for k in [
                "chantier_du_jour", "equipe_presente", "heures_travail", "materiel_livre",
                "travaux_realises", "problemes", "avancement", "objectif_special",
                "cable_dc", "cable_ac", "nombre_rail", "pose_onduleur", "cable_terre"]}
            entry = SuiviJournalier(
                date=datetime.now().strftime('%Y-%m-%d %H:%M'),
                utilisateur=current_user.id,
                **data
            )
            db.session.add(entry)
            db.session.flush()
            photos = request.files.getlist('photo_chantier')
            for photo in photos:
                if photo and photo.filename:
                    img = SuiviJournalierImage(
                        suivi_id=entry.id,
                        filename=photo.filename,
                        content_type=photo.content_type,
                        data=photo.read()
                    )
                    db.session.add(img)
            db.session.commit()
            save_to_csv({
                "date": entry.date,
                **data,
                "photo_chantier": ";".join([p.filename for p in photos if p and p.filename]),
                "utilisateur": current_user.id
            })
            return redirect(url_for('index'))
        except Exception as e:
            db.session.rollback()
            return f"❌ Server Error: {str(e)}", 500
    return render_template('suivi_journalier.html')

@app.route('/image/<int:image_id>')
@login_required
def get_image(image_id):
    image = SuiviJournalierImage.query.get_or_404(image_id)
    return send_file(BytesIO(image.data), mimetype=image.content_type, as_attachment=False, download_name=image.filename)

@app.route('/historique')
@login_required
def historique():
    try:
        if current_user.role == "admin":
            lignes_utilisateur = SuiviJournalier.query.all()
        else:
            lignes_utilisateur = SuiviJournalier.query.filter_by(
                utilisateur=current_user.id
            ).all()
        def parse_date_safe(date_str):
            try:
                return datetime.strptime(date_str, "%Y-%m-%d %H:%M")
            except Exception:
                return datetime(1900, 1, 1)
        rows = sorted(
            lignes_utilisateur,
            key=lambda r: (r.chantier_du_jour or "", parse_date_safe(r.date or ""))
        )
        lignes_dicts = []
        chantier_totals = {}
        for obj in rows:
            row = {c.name: getattr(obj, c.name) for c in obj.__table__.columns}
            chantier = row.get('chantier_du_jour') or ""
            def safe_float(val):
                try:
                    return float(val)
                except (ValueError, TypeError):
                    return 0.0
            dc = safe_float(row.get('cable_dc'))
            ac = safe_float(row.get('cable_ac'))
            rail = safe_float(row.get('nombre_rail'))
            if chantier not in chantier_totals:
                chantier_totals[chantier] = {'dc': 0, 'ac': 0, 'rail': 0}
            chantier_totals[chantier]['dc'] += dc
            chantier_totals[chantier]['ac'] += ac
            chantier_totals[chantier]['rail'] += rail
            row['total_cable_dc'] = chantier_totals[chantier]['dc']
            row['total_cable_ac'] = chantier_totals[chantier]['ac']
            row['total_rails'] = chantier_totals[chantier]['rail']
            row['image_ids'] = [img.id for img in getattr(obj, "images", [])]
            lignes_dicts.append(row)
        return render_template('historique.html', lignes=lignes_dicts)
    except Exception as e:
        return f"Server Error in /historique: {str(e)}", 500

@app.route('/telecharger-historique')
@login_required
def telecharger_historique():
    if current_user.role == "admin":
        rows = SuiviJournalier.query.all()
    else:
        rows = SuiviJournalier.query.filter_by(utilisateur=current_user.id).all()
    fieldnames = [
        "id", "date", "chantier_du_jour", "equipe_presente", "heures_travail", "materiel_livre",
        "travaux_realises", "problemes", "avancement", "objectif_special",
        "cable_dc", "cable_ac", "nombre_rail", "pose_onduleur", "cable_terre",
        "photo_chantier", "utilisateur"
    ]
    csv_buffer = StringIO()
    writer = csv.writer(csv_buffer, delimiter=';')
    writer.writerow(fieldnames)
    for row in rows:
        photo_chantier = ";".join([img.filename for img in row.images])
        row_dict = {field: getattr(row, field, "") for field in fieldnames}
        row_dict["photo_chantier"] = photo_chantier
        writer.writerow([row_dict.get(field, "") for field in fieldnames])
    return Response(
        csv_buffer.getvalue(),
        mimetype='text/csv',
        headers={"Content-Disposition": f"attachment;filename={current_user.id}_historique.csv"}
    )

# Example PDF export (for demonstration, returns a simple text PDF)
@app.route('/telecharger-historique-pdf')
@login_required
def telecharger_historique_pdf():
    from reportlab.lib.pagesizes import letter
    from reportlab.pdfgen import canvas
    from io import BytesIO

    if current_user.role != "admin":
        return "Unauthorized", 403
    rows = SuiviJournalier.query.all()
    pdf_buffer = BytesIO()
    c = canvas.Canvas(pdf_buffer, pagesize=letter)
    width, height = letter
    y = height - 40
    c.setFont("Helvetica-Bold", 12)
    c.drawString(40, y, "Historique des Suivi Journaliers")
    y -= 25
    c.setFont("Helvetica", 8)
    fieldnames = [
        "date", "chantier_du_jour", "equipe_presente", "heures_travail", "materiel_livre",
        "travaux_realises", "problemes", "avancement", "objectif_special",
        "cable_dc", "cable_ac", "nombre_rail", "pose_onduleur", "cable_terre",
        "utilisateur"
    ]
    c.drawString(40, y, "; ".join(fieldnames))
    y -= 15
    for row in rows:
        row_dict = {field: getattr(row, field, "") for field in fieldnames}
        text = "; ".join(str(row_dict.get(field, "")) for field in fieldnames)
        c.drawString(40, y, text[:1100])  # fit on page
        y -= 12
        if y < 40:
            c.showPage()
            y = height - 40
    c.save()
    pdf_buffer.seek(0)
    return send_file(pdf_buffer, mimetype='application/pdf', as_attachment=True, download_name="historique.pdf")

@app.route('/admin', methods=['GET', 'POST'])
@login_required
def admin_panel():
    if current_user.role != "admin":
        flash("Access denied: Admin only", "danger")
        return redirect(url_for('index'))
    if request.method == 'POST':
        action = request.form.get('action')
        username = request.form.get('username')
        password = request.form.get('password')
        role = request.form.get('role', 'user')
        if action == "add" and username and password:
            if not DBUser.query.filter_by(id=username).first():
                hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
                new_user = DBUser(id=username, password_hash=hashed_password, role=role)
                db.session.add(new_user)
                db.session.commit()
                flash(f"✅ User '{username}' added.", "success")
            else:
                flash(f"User '{username}' already exists.", "warning")
        elif action == "delete" and username:
            user = DBUser.query.filter_by(id=username).first()
            if user and username != "admin":
                db.session.delete(user)
                db.session.commit()
                flash(f"❌ User '{username}' deleted.", "success")
            else:
                flash("❌ Cannot delete this user.", "danger")
        else:
            flash("❌ Invalid action or missing fields.", "danger")
    users = DBUser.query.all()
    return render_template('admin.html', utilisateurs=users)

@app.route('/delete-history/<int:entry_id>', methods=['POST'])
@login_required
def delete_history(entry_id):
    if current_user.role != "admin":
        flash("Access denied: Admin only", "danger")
        return redirect(url_for('historique'))
    try:
        entry = SuiviJournalier.query.get(entry_id)
        if entry:
            for img in entry.images:
                db.session.delete(img)
            db.session.delete(entry)
            db.session.commit()
            flash("Entry deleted successfully.", "success")
        else:
            flash("Entry not found.", "warning")
    except Exception as e:
        db.session.rollback()
        flash(f"Error deleting entry: {str(e)}", "danger")
    return redirect(url_for('historique'))

@app.route('/modify-history/<int:entry_id>', methods=['GET', 'POST'])
@login_required
def modify_history(entry_id):
    entry = SuiviJournalier.query.get(entry_id)
    if not entry:
        flash("Entrée non trouvée.", "danger")
        return redirect(url_for('historique'))
    if current_user.role != "admin" and entry.utilisateur != current_user.id:
        flash("Droits insuffisants pour modifier cette entrée.", "danger")
        return redirect(url_for('historique'))
    if request.method == 'POST':
        entry.chantier_du_jour = request.form.get('chantier_du_jour', entry.chantier_du_jour)
        entry.equipe_presente = request.form.get('equipe_presente', entry.equipe_presente)
        entry.heures_travail = request.form.get('heures_travail', entry.heures_travail)
        entry.materiel_livre = request.form.get('materiel_livre', entry.materiel_livre)
        entry.travaux_realises = request.form.get('travaux_realises', entry.travaux_realises)
        entry.problemes = request.form.get('problemes', entry.problemes)
        entry.avancement = request.form.get('avancement', entry.avancement)
        entry.objectif_special = request.form.get('objectif_special', entry.objectif_special)
        entry.cable_dc = request.form.get('cable_dc', entry.cable_dc)
        entry.cable_ac = request.form.get('cable_ac', entry.cable_ac)
        entry.nombre_rail = request.form.get('nombre_rail', entry.nombre_rail)
        entry.pose_onduleur = request.form.get('pose_onduleur', entry.pose_onduleur)
        entry.cable_terre = request.form.get('cable_terre', entry.cable_terre)
        delete_ids = request.form.getlist('delete_images')
        for img in entry.images[:]:
            if str(img.id) in delete_ids:
                db.session.delete(img)
        photos = request.files.getlist('photo_chantier')
        for photo in photos:
            if photo and photo.filename:
                img = SuiviJournalierImage(
                    suivi_id=entry.id,
                    filename=photo.filename,
                    content_type=photo.content_type,
                    data=photo.read()
                )
                db.session.add(img)
        db.session.commit()
        flash("Entrée modifiée avec succès.", "success")
        return redirect(url_for('historique'))
    return render_template('modify_history.html', entry=entry)

def save_to_csv(data):
    filepath = os.path.join('uploads', 'suivi_journalier.csv')
    file_exists = os.path.isfile(filepath)
    fieldnames = [
        "date", "chantier_du_jour", "equipe_presente", "heures_travail", "materiel_livre",
        "travaux_realises", "problemes", "avancement", "objectif_special",
        "cable_dc", "cable_ac", "nombre_rail", "pose_onduleur", "cable_terre",
        "photo_chantier", "utilisateur"
    ]
    try:
        with open(filepath, mode='a', newline='', encoding='utf-8') as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames, delimiter=';')
            if not file_exists:
                writer.writeheader()
            writer.writerow(data)
    except Exception as e:
        print("❌ CSV save error:", e)

if __name__ == '__main__':
    app.run(debug=True)
