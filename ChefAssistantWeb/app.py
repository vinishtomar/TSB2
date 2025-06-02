import os
import csv
from flask import Flask, render_template, request, redirect, url_for, flash, Response, send_file, session
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_bcrypt import Bcrypt
from flask_sqlalchemy import SQLAlchemy
from io import StringIO, BytesIO
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

app = Flask(__name__)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = "login"
app.secret_key = os.urandom(24)

# Use PostgreSQL for production; replace with your URI if needed
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://tsb_jilz_user:WQuuirqxSdknwZjsvldYzD0DbhcOBzQ7@dpg-d0jjegmmcj7s73836lp0-a/tsb_jilz'
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
    __tablename__ = 'new_suivi_journalier'
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.String(50))
    utilisateur = db.Column(db.String(255))

    # Only the first machine's fields are stored in main table for legacy compatibility
    equipement_type = db.Column(db.String(255))
    equipement_reference = db.Column(db.String(255))
    equipement_etat = db.Column(db.String(255))
    equipement_date_reception = db.Column(db.String(255))
    equipement_nombre_1 = db.Column(db.String(10))
    equipement_nombre_2 = db.Column(db.String(10))
    equipement_nombre_3 = db.Column(db.String(10))

    # Réception du Chantier: Connecteur
    connecteur_type = db.Column(db.String(255))
    connecteur_quantite = db.Column(db.String(255))
    connecteur_etat = db.Column(db.String(255))

    # Réception du Chantier: Chemin de câble
    chemin_cable_longueur = db.Column(db.String(255))
    chemin_cable_type = db.Column(db.String(255))
    chemin_cable_section = db.Column(db.String(255))
    chemin_cable_profondeur = db.Column(db.String(255))

    # Réception du Chantier: Terre
    terre_longueur = db.Column(db.String(255))

    # Réception du Chantier: Câble AC
    cableac_section = db.Column(db.String(255))
    cableac_longueur = db.Column(db.String(255))

    # Réception du Chantier: Câble DC
    cabledc_section = db.Column(db.String(255))
    cabledc_longueur = db.Column(db.String(255))

    # Réception du Chantier: Shelter nombre (NEW FIELD)
    shelter_nombre = db.Column(db.Integer)

    # Avancement du Chantier
    cables_dctires = db.Column(db.String(255))
    cables_actires = db.Column(db.String(255))
    cables_terretires = db.Column(db.String(255))

    # Avancement du Chantier: Problems (NEW FIELD)
    problems = db.Column(db.String(255))

    # Fin du Chantier
    fin_zone = db.Column(db.String(255))
    fin_string = db.Column(db.String(255))
    fin_tension_dc = db.Column(db.String(255))
    fin_courant_dc = db.Column(db.String(255))
    fin_tension_ac = db.Column(db.String(255))
    fin_puissance = db.Column(db.String(255))
    fin_date = db.Column(db.String(255))
    fin_technicien = db.Column(db.String(255))
    fin_status = db.Column(db.String(255))

    # Images
    images = db.relationship('SuiviJournalierImage', backref='suivi', lazy=True)

class SuiviJournalierImage(db.Model):
    __tablename__ = 'new_suivi_journalier_image'
    id = db.Column(db.Integer, primary_key=True)
    suivi_id = db.Column(db.Integer, db.ForeignKey('new_suivi_journalier.id'), nullable=False)
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
    if current_user.role == "admin":
        all_lignes = SuiviJournalier.query.all()
    else:
        all_lignes = SuiviJournalier.query.filter_by(utilisateur=current_user.id).all()
    return render_template('index.html', all_lignes=all_lignes, current_user=current_user)

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
            # Collect three machines' equipment data, including nombre
            equipements = []
            for i in range(1, 4):
                equipements.append({
                    "type": request.form.get(f"equipement_type_{i}", ""),
                    "reference": request.form.get(f"equipement_reference_{i}", ""),
                    "etat": request.form.get(f"equipement_etat_{i}", ""),
                    "date_reception": request.form.get(f"equipement_date_reception_{i}", ""),
                    "nombre": request.form.get(f"equipement_nombre_{i}", "")
                })

            # Determine the active section based on form data
            data = {}
            if any(f"equipement_type_{i}" in request.form for i in range(1, 4)) or \
                "connecteur_type" in request.form or "chemin_cable_longueur" in request.form or \
                "terre_longueur" in request.form or "cableac_section" in request.form or \
                "cabledc_section" in request.form or "shelter_nombre" in request.form:
                data.update({
                    "equipement_type": equipements[0]["type"] if equipements[0]["type"] else None,
                    "equipement_reference": equipements[0]["reference"] if equipements[0]["reference"] else None,
                    "equipement_etat": equipements[0]["etat"] if equipements[0]["etat"] else None,
                    "equipement_date_reception": equipements[0]["date_reception"] if equipements[0]["date_reception"] else None,
                    "equipement_nombre_1": equipements[0]["nombre"] if equipements[0]["nombre"] else None,
                    "equipement_nombre_2": equipements[1]["nombre"] if equipements[1]["nombre"] else None,
                    "equipement_nombre_3": equipements[2]["nombre"] if equipements[2]["nombre"] else None,
                    "connecteur_type": request.form.get("connecteur_type", ""),
                    "connecteur_quantite": request.form.get("connecteur_quantite", ""),
                    "connecteur_etat": request.form.get("connecteur_etat", ""),
                    "chemin_cable_longueur": request.form.get("chemin_cable_longueur", ""),
                    "chemin_cable_type": request.form.get("chemin_cable_type", ""),
                    "chemin_cable_section": request.form.get("chemin_cable_section", ""),
                    "chemin_cable_profondeur": request.form.get("chemin_cable_profondeur", ""),
                    "terre_longueur": request.form.get("terre_longueur", ""),
                    "cableac_section": request.form.get("cableac_section", ""),
                    "cableac_longueur": request.form.get("cableac_longueur", ""),
                    "cabledc_section": request.form.get("cabledc_section", ""),
                    "cabledc_longueur": request.form.get("cabledc_longueur", ""),
                    "shelter_nombre": request.form.get("shelter_nombre", None)
                })
            elif "cables_dctires" in request.form or "cables_actires" in request.form or "cables_terretires" in request.form or "problems" in request.form:
                data.update({
                    "cables_dctires": request.form.get("cables_dctires", ""),
                    "cables_actires": request.form.get("cables_actires", ""),
                    "cables_terretires": request.form.get("cables_terretires", ""),
                    "problems": request.form.get("problems", "")
                })
            elif any(f"fin_{field}" in request.form for field in ["zone", "string", "tension_dc", "courant_dc", "tension_ac", "puissance", "date", "technicien", "status"]):
                data.update({
                    "fin_zone": request.form.get("fin_zone", ""),
                    "fin_string": request.form.get("fin_string", ""),
                    "fin_tension_dc": request.form.get("fin_tension_dc", ""),
                    "fin_courant_dc": request.form.get("fin_courant_dc", ""),
                    "fin_tension_ac": request.form.get("fin_tension_ac", ""),
                    "fin_puissance": request.form.get("fin_puissance", ""),
                    "fin_date": request.form.get("fin_date", ""),
                    "fin_technicien": request.form.get("fin_technicien", ""),
                    "fin_status": request.form.get("fin_status", "")
                })

            entry = SuiviJournalier(
                date=datetime.now().strftime('%Y-%m-%d %H:%M'),
                utilisateur=current_user.id,
                **data
            )
            db.session.add(entry)
            db.session.flush()
            # Handle multiple images
            photos = request.files.getlist('photo_chantier[]')
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
            # Save CSV
            save_to_csv({
                "date": entry.date,
                "utilisateur": current_user.id,
                **{k: v for k, v in data.items() if v},
                "photo_chantier": ";".join([p.filename for p in photos if p and p.filename])
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

@app.route('/telecharger-historique')
@login_required
def telecharger_historique():
    if current_user.role == "admin":
        rows = SuiviJournalier.query.all()
    else:
        rows = SuiviJournalier.query.filter_by(utilisateur=current_user.id).all()
    fieldnames = [
        "date", "utilisateur",
        "equipement_type", "equipement_reference", "equipement_etat", "equipement_date_reception",
        "equipement_nombre_1", "equipement_nombre_2", "equipement_nombre_3",
        "connecteur_type", "connecteur_quantite", "connecteur_etat",
        "chemin_cable_longueur", "chemin_cable_type", "chemin_cable_section", "chemin_cable_profondeur",
        "terre_longueur",
        "cableac_section", "cableac_longueur",
        "cabledc_section", "cabledc_longueur",
        "shelter_nombre",   # NEW FIELD
        "cables_dctires", "cables_actires", "cables_terretires",
        "problems",        # NEW FIELD
        "fin_zone", "fin_string", "fin_tension_dc", "fin_courant_dc", "fin_tension_ac", "fin_puissance", "fin_date", "fin_technicien", "fin_status",
        "photo_chantier"
    ]
    csv_buffer = StringIO()
    writer = csv.writer(csv_buffer, delimiter=';')
    writer.writerow(fieldnames)
    for row in rows:
        photo_chantier = ";".join([img.filename for img in row.images])
        row_dict = {field: getattr(row, field, "") for field in fieldnames if field != "photo_chantier"}
        row_dict["photo_chantier"] = photo_chantier
        writer.writerow([row_dict.get(field, "") for field in fieldnames])
    return Response(
        csv_buffer.getvalue(),
        mimetype='text/csv',
        headers={"Content-Disposition": f"attachment;filename={current_user.id}_historique.csv"}
    )

@app.route('/telecharger-historique-pdf')
@login_required
def telecharger_historique_pdf():
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
    c.setFont("Helvetica", 7)
    fieldnames = [
        "date", "utilisateur",
        "equipement_type", "equipement_reference", "equipement_etat", "equipement_date_reception",
        "equipement_nombre_1", "equipement_nombre_2", "equipement_nombre_3",
        "connecteur_type", "connecteur_quantite", "connecteur_etat",
        "chemin_cable_longueur", "chemin_cable_type", "chemin_cable_section", "chemin_cable_profondeur",
        "terre_longueur",
        "cableac_section", "cableac_longueur",
        "cabledc_section", "cabledc_longueur",
        "shelter_nombre",   # NEW FIELD
        "cables_dctires", "cables_actires", "cables_terretires",
        "problems",        # NEW FIELD
        "fin_zone", "fin_string", "fin_tension_dc", "fin_courant_dc", "fin_tension_ac", "fin_puissance", "fin_date", "fin_technicien", "fin_status"
    ]
    c.drawString(40, y, "; ".join(fieldnames))
    y -= 15
    for row in rows:
        row_dict = {field: getattr(row, field, "") for field in fieldnames}
        text = "; ".join(str(row_dict.get(field, "")) for field in fieldnames)
        lines = [text[i:i+100] for i in range(0, len(text), 100)]  # Split into 100-char lines
        for line in lines:
            if y < 40:
                c.showPage()
                y = height - 40
            c.drawString(40, y, line)
            y -= 10
    c.showPage()
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
        return redirect(url_for('index'))
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
    return redirect(url_for('index'))

@app.route('/modify-history/<int:entry_id>', methods=['GET', 'POST'])
@login_required
def modify_history(entry_id):
    entry = SuiviJournalier.query.get_or_404(entry_id)
    if not entry:
        flash("Entrée non trouvée.", "danger")
        return redirect(url_for('index'))
    if current_user.role != "admin" and entry.utilisateur != current_user.id:
        flash("Droits insuffisants pour modifier cette entrée.", "danger")
        return redirect(url_for('index'))
    print(f"Debug - Entry data: {entry.__dict__}")
    if request.method == 'POST':
        for field in [
            "equipement_type", "equipement_reference", "equipement_etat", "equipement_date_reception",
            "equipement_nombre_1", "equipement_nombre_2", "equipement_nombre_3",
            "connecteur_type", "connecteur_quantite", "connecteur_etat",
            "chemin_cable_longueur", "chemin_cable_type", "chemin_cable_section", "chemin_cable_profondeur",
            "terre_longueur",
            "cableac_section", "cableac_longueur",
            "cabledc_section", "cabledc_longueur",
            "shelter_nombre",   # NEW FIELD
            "cables_dctires", "cables_actires", "cables_terretires",
            "problems",        # NEW FIELD
            "fin_zone", "fin_string", "fin_tension_dc", "fin_courant_dc", "fin_tension_ac", "fin_puissance", "fin_date", "fin_technicien", "fin_status"
        ]:
            setattr(entry, field, request.form.get(field, getattr(entry, field)))
        delete_ids = request.form.getlist('delete_images')
        for img in entry.images[:]:
            if str(img.id) in delete_ids:
                db.session.delete(img)
        photos = request.files.getlist('photo_chantier[]')
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
        return redirect(url_for('index'))
    return render_template('modify_history.html', entry=entry)

def save_to_csv(data):
    filepath = os.path.join('uploads', 'suivi_journalier.csv')
    file_exists = os.path.isfile(filepath)
    fieldnames = [
        "date", "utilisateur",
        "equipement_type", "equipement_reference", "equipement_etat", "equipement_date_reception",
        "equipement_nombre_1", "equipement_nombre_2", "equipement_nombre_3",
        "connecteur_type", "connecteur_quantite", "connecteur_etat",
        "chemin_cable_longueur", "chemin_cable_type", "chemin_cable_section", "chemin_cable_profondeur",
        "terre_longueur",
        "cableac_section", "cableac_longueur",
        "cabledc_section", "cabledc_longueur",
        "shelter_nombre",   # NEW FIELD
        "cables_dctires", "cables_actires", "cables_terretires",
        "problems",        # NEW FIELD
        "fin_zone", "fin_string", "fin_tension_dc", "fin_courant_dc", "fin_tension_ac", "fin_puissance", "fin_date", "fin_technicien", "fin_status",
        "photo_chantier"
    ]
    try:
        with open(filepath, mode='a', newline='', encoding='utf-8') as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames, delimiter=';')
            if not file_exists:
                writer.writeheader()
            writer.writerow({k: v for k, v in data.items() if k in fieldnames})
    except Exception as e:
        print("❌ CSV save error:", e)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
