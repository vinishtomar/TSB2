# Last modified: 2025-06-03 10:20:57 UTC by tsbenergie # (Original timestamp, update as needed)

import os
import csv
from flask import Flask, render_template, request, redirect, url_for, flash, Response, send_file, session, abort
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_bcrypt import Bcrypt
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from io import StringIO, BytesIO
from datetime import datetime
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image as ReportLabImage
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
from werkzeug.utils import secure_filename # For secure filenames

app = Flask(__name__)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = "login"
login_manager.login_message = "Veuillez vous connecter pour accéder à cette page."
login_manager.login_message_category = "info"

# Secret key and database configuration
app.secret_key = os.environ.get('SECRET_KEY', os.urandom(24))
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
    'DATABASE_URL',
    'sqlite:///' + os.path.join(os.path.abspath(os.path.dirname(__file__)), 'site.db')
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['UPLOAD_FOLDER'] = 'uploads/images' # For storing images if saved to disk (not directly used by current DB storage)

db = SQLAlchemy(app)
migrate = Migrate(app, db)

# --- MODELS ---
class DBUser(db.Model):
    __tablename__ = 'db_user'
    id = db.Column(db.String(255), primary_key=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), nullable=False, default="user")
    last_login = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class User(UserMixin):
    def __init__(self, user_id, role="user"):
        self.id = user_id
        self.role = role

@login_manager.user_loader
def load_user(user_id):
    user_from_db = DBUser.query.filter_by(id=user_id).first()
    if user_from_db:
        return User(user_from_db.id, user_from_db.role)
    return None

class SuiviJournalier(db.Model):
    __tablename__ = 'new_suivi_journalier'
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.String(50), default=lambda: datetime.now().strftime('%Y-%m-%d %H:%M'))
    utilisateur = db.Column(db.String(255))
    nom_chantier = db.Column(db.String(255), nullable=True) # Make sure this is in your form
    last_modified = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_modified_by = db.Column(db.String(255))

    # Equipment fields
    equipement_type = db.Column(db.String(255), nullable=True)
    equipement_reference = db.Column(db.String(255), nullable=True)
    equipement_etat = db.Column(db.String(255), nullable=True)
    equipement_date_reception = db.Column(db.String(255), nullable=True)
    equipement_nombre_1 = db.Column(db.String(10), nullable=True) # Expects form field "equipement_nombre_1"
    equipement_nombre_2 = db.Column(db.String(10), nullable=True) # Expects form field "equipement_nombre_2"
    equipement_nombre_3 = db.Column(db.String(10), nullable=True) # Expects form field "equipement_nombre_3"

    # Connector fields
    connecteur_type = db.Column(db.String(255), nullable=True)
    connecteur_quantite = db.Column(db.String(255), nullable=True)
    connecteur_etat = db.Column(db.String(255), nullable=True)

    # Cable path fields
    chemin_cable_longueur = db.Column(db.String(255), nullable=True)
    chemin_cable_type = db.Column(db.String(255), nullable=True)
    chemin_cable_section = db.Column(db.String(255), nullable=True)
    chemin_cable_profondeur = db.Column(db.String(255), nullable=True)

    # Ground and cable fields
    terre_longueur = db.Column(db.String(255), nullable=True)
    cableac_section = db.Column(db.String(255), nullable=True)
    cableac_longueur = db.Column(db.String(255), nullable=True)
    cabledc_section = db.Column(db.String(255), nullable=True)
    cabledc_longueur = db.Column(db.String(255), nullable=True)
    shelter_nombre = db.Column(db.Integer, nullable=True)

    # Progress fields
    cables_dctires = db.Column(db.String(255), nullable=True)
    cables_actires = db.Column(db.String(255), nullable=True)
    cables_terretires = db.Column(db.String(255), nullable=True)
    problems = db.Column(db.Text, nullable=True)

    # Weather and work conditions
    weather_conditions = db.Column(db.String(50), nullable=True)
    temperature = db.Column(db.Float, nullable=True)
    work_hours = db.Column(db.Float, nullable=True)
    staff_count = db.Column(db.Integer, nullable=True)

    # Final measurements
    fin_zone = db.Column(db.String(255), nullable=True)
    fin_string = db.Column(db.String(255), nullable=True)
    fin_tension_dc = db.Column(db.String(255), nullable=True)
    fin_courant_dc = db.Column(db.String(255), nullable=True)
    fin_tension_ac = db.Column(db.String(255), nullable=True)
    fin_puissance = db.Column(db.String(255), nullable=True)
    fin_date = db.Column(db.String(255), nullable=True)
    fin_technicien = db.Column(db.String(255), nullable=True)
    fin_status = db.Column(db.String(255), nullable=True)

    # Validation fields
    validation_status = db.Column(db.String(50), nullable=True)
    validated_by = db.Column(db.String(255), nullable=True)
    validation_date = db.Column(db.DateTime, nullable=True)

    # Relationship to images
    images = db.relationship('SuiviJournalierImage', backref='suivi', lazy=True, cascade="all, delete-orphan")

class SuiviJournalierImage(db.Model):
    __tablename__ = 'new_suivi_journalier_image'
    id = db.Column(db.Integer, primary_key=True)
    suivi_id = db.Column(db.Integer, db.ForeignKey('new_suivi_journalier.id'), nullable=False)
    filename = db.Column(db.String(255), nullable=False) # Store secure_filename result
    content_type = db.Column(db.String(255), nullable=False)
    data = db.Column(db.LargeBinary, nullable=False)
    upload_date = db.Column(db.DateTime, default=datetime.utcnow)

# --- UTILITY FUNCTIONS ---
def create_admin_user_if_not_exists():
    if not DBUser.query.filter_by(id="admin").first():
        hashed_password = bcrypt.generate_password_hash("admin").decode('utf-8') # Change 'admin' password in production
        admin_user = DBUser(
            id="admin",
            password_hash=hashed_password,
            role="admin",
            created_at=datetime.utcnow()
        )
        db.session.add(admin_user)
        db.session.commit()
        app.logger.info(f"Default admin user created at {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}")

def validate_file_upload(file_storage):
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    if not file_storage.filename:
        return False
    # It's good practice to also check MIME type if possible, but extension check is a first step
    return '.' in file_storage.filename and \
           file_storage.filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_to_csv(data_dict):
    uploads_dir = 'uploads' # Directory for CSV backups
    os.makedirs(uploads_dir, exist_ok=True) # Ensure directory exists
    filepath = os.path.join(uploads_dir, 'suivi_journalier_local_backup.csv')
    file_exists = os.path.isfile(filepath)

    # Define fieldnames based on SuiviJournalier model columns + photos
    # This ensures all current model fields are considered for CSV
    fieldnames = [column.name for column in SuiviJournalier.__table__.columns if column.name != 'id']
    fieldnames.append('photo_chantier_filenames') # For image filenames

    try:
        with open(filepath, mode='a', newline='', encoding='utf-8') as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames, delimiter=';', extrasaction='ignore')
            if not file_exists or os.path.getsize(filepath) == 0:
                writer.writeheader()
            writer.writerow(data_dict)
    except Exception as e:
        app.logger.error(f"Error saving to CSV at {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}: {str(e)}")

# --- INITIALIZE APP CONTEXT ITEMS ---
with app.app_context():
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True) # For actual image files if saved to disk
    db.create_all()
    create_admin_user_if_not_exists()

# --- ROUTES ---
@app.route('/')
@login_required
def index():
    page = request.args.get('page', 1, type=int)
    per_page = 10 # Entries per page for pagination

    query = SuiviJournalier.query
    if current_user.role != "admin":
        query = query.filter_by(utilisateur=current_user.id)
    
    # Handle date range filtering from query parameters
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')

    if start_date_str:
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
            # Adjust to include the whole day if only date is given for 'date' field (which stores time)
            # If your 'date' field can be just a date string, this might need adjustment
            query = query.filter(SuiviJournalier.date >= start_date.strftime('%Y-%m-%d 00:00'))
        except ValueError:
            flash("Format de date de début invalide.", "warning")
    
    if end_date_str:
        try:
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
            # Adjust to include the whole day
            query = query.filter(SuiviJournalier.date <= end_date.strftime('%Y-%m-%d 23:59'))
        except ValueError:
            flash("Format de date de fin invalide.", "warning")

    pagination = query.order_by(SuiviJournalier.last_modified.desc()).paginate(page=page, per_page=per_page, error_out=False)
    entries_on_page = pagination.items

    # This template should be your main page, containing the form and the history list.
    # It now receives pagination data.
    return render_template('index.html',
                           entries=entries_on_page,
                           current_page=page,
                           total_pages=pagination.pages,
                           pagination=pagination,
                           current_user=current_user)

@app.route('/admin/view_entries')
@login_required
def admin_view_all_suivi_journalier():
    if current_user.role != "admin":
        flash("Accès non autorisé. Réservé aux administrateurs.", "danger")
        return redirect(url_for('index'))

    page = request.args.get('page', 1, type=int)
    entries_per_page = 15 # Or your preferred number for admin view

    # Using SuiviJournalier model, not 'Entry'
    entries_pagination = SuiviJournalier.query.order_by(SuiviJournalier.last_modified.desc())\
        .paginate(page=page, per_page=entries_per_page, error_out=False)

    # You might want a specific admin template for this, e.g., 'admin_view_entries.html'
    return render_template('admin_view_entries.html', # Or 'suivi_journalier.html' if it's generic enough
                         entries=entries_pagination.items,
                         pagination=entries_pagination,
                         current_page=page,
                         total_pages=entries_pagination.pages)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user_from_db = DBUser.query.filter_by(id=username).first()
        if user_from_db and bcrypt.check_password_hash(user_from_db.password_hash, password):
            user_obj = User(user_from_db.id, user_from_db.role)
            login_user(user_obj)
            user_from_db.last_login = datetime.utcnow()
            db.session.commit()
            flash("Connexion réussie!", "success")
            return redirect(url_for('index'))
        else:
            flash("Nom d'utilisateur ou mot de passe incorrect.", "danger")
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    session.clear() # Clear the session to ensure full logout
    flash("Vous avez été déconnecté.", "success")
    return redirect(url_for('login'))

@app.route('/suivi-journalier', methods=['POST']) # Renamed function
@login_required
def add_suivi_journalier_entry():
    try:
        # Ensure 'nom_chantier' is present in your form for this to work
        nom_chantier_val = request.form.get("nom_chantier")
        if not nom_chantier_val:
            flash("Le champ 'Nom du chantier' est requis.", "danger")
            # It's better to re-render the form with errors and previously entered data.
            # For now, redirecting to index. You might want to pass form data back.
            return redirect(url_for('index'))

        data_to_save = {
            "utilisateur": current_user.id,
            "date": datetime.now().strftime('%Y-%m-%d %H:%M'), # Or get from form if needed
            "nom_chantier": nom_chantier_val,
            "last_modified_by": current_user.id, # last_modified is auto-updated by model
            
            # Equipment data - ensure form names match these keys
            "equipement_type": request.form.get("equipement_type"),
            "equipement_reference": request.form.get("equipement_reference"),
            "equipement_etat": request.form.get("equipement_etat"),
            "equipement_date_reception": request.form.get("equipement_date_reception"),
            "equipement_nombre_1": request.form.get("equipement_nombre_1"), # Expects separate form fields
            "equipement_nombre_2": request.form.get("equipement_nombre_2"),
            "equipement_nombre_3": request.form.get("equipement_nombre_3"),
            
            # Connector data
            "connecteur_type": request.form.get("connecteur_type"),
            "connecteur_quantite": request.form.get("connecteur_quantite"),
            "connecteur_etat": request.form.get("connecteur_etat"),

            # Cable path data
            "chemin_cable_longueur": request.form.get("chemin_cable_longueur"),
            "chemin_cable_type": request.form.get("chemin_cable_type"),
            "chemin_cable_section": request.form.get("chemin_cable_section"),
            "chemin_cable_profondeur": request.form.get("chemin_cable_profondeur"),

            # Ground and cable data
            "terre_longueur": request.form.get("terre_longueur"),
            "cableac_section": request.form.get("cableac_section"),
            "cableac_longueur": request.form.get("cableac_longueur"),
            "cabledc_section": request.form.get("cabledc_section"),
            "cabledc_longueur": request.form.get("cabledc_longueur"),
            "shelter_nombre": request.form.get("shelter_nombre", type=int) if request.form.get("shelter_nombre") else None,
            
            # Progress data
            "cables_dctires": request.form.get("cables_dctires"),
            "cables_actires": request.form.get("cables_actires"),
            "cables_terretires": request.form.get("cables_terretires"),
            "problems": request.form.get("problems"),

            # Weather and work conditions
            "weather_conditions": request.form.get("weather_conditions"),
            "temperature": float(request.form.get("temperature")) if request.form.get("temperature") else None,
            "work_hours": float(request.form.get("work_hours")) if request.form.get("work_hours") else None,
            "staff_count": int(request.form.get("staff_count")) if request.form.get("staff_count") else None,

            # Final measurements
            "fin_zone": request.form.get("fin_zone"),
            "fin_string": request.form.get("fin_string"),
            "fin_tension_dc": request.form.get("fin_tension_dc"),
            "fin_courant_dc": request.form.get("fin_courant_dc"),
            "fin_tension_ac": request.form.get("fin_tension_ac"),
            "fin_puissance": request.form.get("fin_puissance"),
            "fin_date": request.form.get("fin_date"),
            "fin_technicien": request.form.get("fin_technicien"),
            "fin_status": request.form.get("fin_status"),
        }
        
        entry = SuiviJournalier(**data_to_save)
        db.session.add(entry)
        db.session.flush() # Get entry.id before adding images

        # Handle image uploads - ensure your form has <input type="file" name="photo_chantier[]" multiple>
        photos = request.files.getlist('photo_chantier[]')
        image_filenames_for_csv = []
        
        for photo_storage in photos:
            if photo_storage and photo_storage.filename:
                if not validate_file_upload(photo_storage): # Pass the FileStorage object
                    flash(f"Type de fichier non autorisé pour '{photo_storage.filename}'. Seuls PNG, JPG, JPEG, GIF sont permis.", "danger")
                    continue # Skip this file
                
                # Secure the filename before storing
                s_filename = secure_filename(photo_storage.filename)
                if not s_filename: # If filename becomes empty after securing
                    s_filename = f"untitled_image_{datetime.utcnow().timestamp()}"


                img = SuiviJournalierImage(
                    suivi_id=entry.id,
                    filename=s_filename,
                    content_type=photo_storage.content_type,
                    data=photo_storage.read(), # Reads the file content into memory
                    upload_date=datetime.utcnow()
                )
                db.session.add(img)
                image_filenames_for_csv.append(s_filename)

        db.session.commit()
        flash("Entrée enregistrée avec succès.", "success")

        # Optional: Save to CSV backup
        csv_data_payload = data_to_save.copy() # This is the form data
        csv_data_payload["photo_chantier_filenames"] = ";".join(image_filenames_for_csv)
        save_to_csv(csv_data_payload)

    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error in add_suivi_journalier_entry at {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}: {str(e)}")
        flash(f"❌ Erreur Serveur lors de l'enregistrement: {str(e)}", "danger")
    
    return redirect(url_for('index'))

@app.route('/modify-history/<int:entry_id>', methods=['GET', 'POST'])
@login_required
def modify_history(entry_id):
    entry = SuiviJournalier.query.get_or_404(entry_id)
    if current_user.role != "admin" and entry.utilisateur != current_user.id:
        flash("Droits insuffisants pour modifier cette entrée.", "danger")
        return redirect(url_for('index'))

    if request.method == 'POST':
        try:
            # Update fields from form
            for column in SuiviJournalier.__table__.columns:
                col_name = column.name
                if col_name in request.form and col_name not in ['id', 'date', 'utilisateur', 'last_modified']:
                    value = request.form.get(col_name)
                    
                    if col_name == "shelter_nombre":
                        value = int(value) if value and value.strip() else None
                    elif col_name in ["temperature", "work_hours"]:
                        value = float(value) if value and value.strip() else None
                    elif col_name == "staff_count":
                        value = int(value) if value and value.strip() else None
                    
                    setattr(entry, col_name, value)
            
            entry.last_modified_by = current_user.id # last_modified is auto-updated by onupdate

            # Handle image deletion
            delete_ids_str = request.form.get('delete_images', '')
            if delete_ids_str:
                delete_ids = [int(img_id) for img_id in delete_ids_str.split(',') if img_id.strip().isdigit()]
                for img_id_to_delete in delete_ids:
                    img_to_delete = SuiviJournalierImage.query.get(img_id_to_delete)
                    if img_to_delete and img_to_delete.suivi_id == entry.id: # Security check
                        db.session.delete(img_to_delete)
            
            # Handle new image uploads
            photos = request.files.getlist('photo_chantier[]') # Ensure form name is photo_chantier[]
            for photo_storage in photos:
                if photo_storage and photo_storage.filename:
                    if not validate_file_upload(photo_storage):
                        flash(f"Type de fichier non autorisé pour '{photo_storage.filename}'.", "danger")
                        continue
                    
                    s_filename = secure_filename(photo_storage.filename)
                    if not s_filename:
                         s_filename = f"untitled_image_{datetime.utcnow().timestamp()}"

                    img = SuiviJournalierImage(
                        suivi_id=entry.id,
                        filename=s_filename,
                        content_type=photo_storage.content_type,
                        data=photo_storage.read(),
                        upload_date=datetime.utcnow()
                    )
                    db.session.add(img)
            
            db.session.commit()
            flash("Entrée modifiée avec succès.", "success")
            return redirect(url_for('index'))
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Error modifying history entry {entry_id} at {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}: {str(e)}")
            flash(f"Erreur lors de la modification : {str(e)}", "danger")
            
    return render_template('modify_history.html', entry=entry, current_user=current_user) # Pass current_user if template uses it

@app.route('/delete-history/<int:entry_id>', methods=['POST']) # Should be POST for destructive action
@login_required
def delete_history(entry_id):
    # For CSRF protection with fetch, you'd typically use Flask-WTF or a similar library.
    # Ensure your JS sends a CSRF token if you implement server-side CSRF checks.
    if current_user.role != "admin":
        flash("Accès refusé : Administrateur seulement.", "danger")
        # For AJAX, might return a JSON response instead of redirect
        return redirect(url_for('index')) # Or abort(403) / jsonify error
    try:
        entry_to_delete = SuiviJournalier.query.get_or_404(entry_id)
        db.session.delete(entry_to_delete)
        db.session.commit()
        flash("Entrée supprimée avec succès.", "success")
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error deleting history entry {entry_id} at {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}: {str(e)}")
        flash(f"Erreur lors de la suppression de l'entrée: {str(e)}", "danger")
    return redirect(url_for('index')) # Or return jsonify({'status': 'success'}) for AJAX

@app.route('/image/<int:image_id>')
@login_required
def get_image(image_id):
    image = SuiviJournalierImage.query.get_or_404(image_id)
    # Access control: only admin or owner of the related entry can view
    if current_user.role != 'admin' and image.suivi.utilisateur != current_user.id:
        abort(403) # Forbidden
    return send_file(BytesIO(image.data), mimetype=image.content_type)

@app.route('/telecharger-historique') # CSV Export
@login_required
def telecharger_historique_csv(): # Renamed for clarity
    query = SuiviJournalier.query
    if current_user.role != "admin":
        query = query.filter_by(utilisateur=current_user.id)
    
    rows = query.order_by(SuiviJournalier.date.desc()).all()
    
    # Define fieldnames for CSV consistently
    fieldnames = [col.name for col in SuiviJournalier.__table__.columns if col.name != 'id']
    fieldnames.append('images_filenames') # For associated image filenames
    
    csv_buffer = StringIO()
    writer = csv.writer(csv_buffer, delimiter=';')
    writer.writerow(fieldnames) # Write header

    for row in rows:
        row_data = []
        for field in fieldnames:
            if field == 'images_filenames':
                photo_filenames_str = ";".join([img.filename for img in row.images])
                row_data.append(photo_filenames_str)
            else:
                row_data.append(getattr(row, field, "")) # Get attribute, default to empty string
        writer.writerow(row_data)
        
    csv_buffer.seek(0)
    return Response(
        csv_buffer.getvalue(),
        mimetype='text/csv',
        headers={
            "Content-Disposition": f"attachment;filename=historique_suivi_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        }
    )

@app.route('/telecharger-historique-pdf') # PDF Export
@login_required
def telecharger_historique_pdf():
    if current_user.role != "admin":
        flash("Accès refusé. Réservé aux administrateurs.", "danger")
        return redirect(url_for('index'))

    rows = SuiviJournalier.query.order_by(SuiviJournalier.date.desc()).all() # Admins see all
    
    pdf_buffer = BytesIO()
    doc = SimpleDocTemplate(
        pdf_buffer,
        pagesize=landscape(letter),
        topMargin=0.5*inch, bottomMargin=0.5*inch,
        leftMargin=0.3*inch, rightMargin=0.3*inch
    )
    
    elements = []
    styles = getSampleStyleSheet()
    
    small_body_style = ParagraphStyle('smallBodyText', parent=styles['Normal'], fontSize=7)
    small_bold_style = ParagraphStyle('smallBoldText', parent=styles['Normal'], fontSize=7, fontName='Helvetica-Bold')

    title_style = styles['h1'] # Use h1 for main title
    title_style.alignment = 1 # Center alignment
    elements.append(Paragraph(f"Historique des Suivi Journaliers (Généré le {datetime.now().strftime('%Y-%m-%d %H:%M')})", title_style))
    elements.append(Spacer(1, 0.2*inch))

    pdf_fieldnames = [
        "date", "utilisateur", "nom_chantier", "equipement_type", "equipement_reference", "equipement_etat",
        "weather_conditions", "temperature", "cables_dctires", "cables_actires", "cables_terretires",
        "problems", "fin_status", "images_count" # Renamed for clarity
    ]
    
    pdf_headers = {
        "date": "Date", "utilisateur": "Utilisateur", "nom_chantier": "Chantier",
        "equipement_type": "Type Équip.", "equipement_reference": "Réf. Équip.", "equipement_etat": "État Équip.",
        "weather_conditions": "Météo", "temperature": "Temp.°C",
        "cables_dctires": "DC Tirés", "cables_actires": "AC Tirés", "cables_terretires": "Terre Tirés",
        "problems": "Problèmes", "fin_status": "Stat. Fin", "images_count": "Photos"
    }

    header_paragraphs = [Paragraph(f"<b>{pdf_headers.get(fn, fn.replace('_', ' ').title())}</b>", small_bold_style) for fn in pdf_fieldnames]
    data_for_table = [header_paragraphs]

    for row in rows:
        row_data_paragraphs = []
        for field_key in pdf_fieldnames:
            cell_content_str = ""
            if field_key == 'images_count':
                cell_content_str = str(len(row.images))
            elif hasattr(row, field_key):
                value = getattr(row, field_key, "")
                cell_content_str = str(value) if value is not None else ""
            
            max_len = 25 # Max length for cell content before truncation
            if len(cell_content_str) > max_len:
                cell_content_str = cell_content_str[:max_len-3] + "..."
            row_data_paragraphs.append(Paragraph(cell_content_str, small_body_style))
        data_for_table.append(row_data_paragraphs)

    if len(data_for_table) > 1: # If there's data beyond headers
        # Adjusted column widths based on likely content size
        col_widths = [
            0.8*inch, 0.7*inch, 0.9*inch,  # date, util, nom_chantier
            0.7*inch, 0.7*inch, 0.6*inch,  # equip_type, ref, etat
            0.6*inch, 0.5*inch,            # weather, temp
            0.6*inch, 0.6*inch, 0.7*inch,  # cables (dc, ac, terre)
            1.2*inch, 0.6*inch, 0.4*inch   # problems, status, photos_count
        ]
        if len(col_widths) != len(pdf_fieldnames):
            app.logger.warning(f"PDF col_widths ({len(col_widths)}) mismatch with pdf_fieldnames ({len(pdf_fieldnames)})")
            # Fallback to equal widths if mismatch
            col_widths = [(doc.width - doc.leftMargin - doc.rightMargin) / len(pdf_fieldnames)] * len(pdf_fieldnames)


        table = Table(data_for_table, colWidths=col_widths, repeatRows=1)
        table_style = TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.darkslategray), ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'), ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'), ('FONTSIZE', (0, 0), (-1, 0), 7),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8), ('TOPPADDING', (0, 0), (-1, 0), 8),
            ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey), ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('LEFTPADDING', (0,0), (-1,-1), 4), ('RIGHTPADDING', (0,0), (-1,-1), 4),
            ('TOPPADDING', (0,1), (-1,-1), 4), ('BOTTOMPADDING', (0,1), (-1,-1), 4),
        ])
        table.setStyle(table_style)
        elements.append(table)
    else:
        elements.append(Paragraph("Aucune donnée à afficher.", styles['Normal']))

    doc.build(elements)
    pdf_buffer.seek(0)
    return send_file(
        pdf_buffer,
        mimetype='application/pdf',
        as_attachment=True, # Changed from download_name for modern Flask/Werkzeug
        download_name=f"historique_suivi_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    )

@app.route('/admin', methods=['GET', 'POST'])
@login_required
def admin_panel():
    if current_user.role != "admin":
        flash("Accès refusé : Administrateur seulement.", "danger")
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        action = request.form.get('action')
        username = request.form.get('username')
        password = request.form.get('password')
        role = request.form.get('role', 'user') # Default to 'user' if not provided

        if action == "add" and username and password:
            if not DBUser.query.filter_by(id=username).first():
                hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
                new_user = DBUser(id=username, password_hash=hashed_password, role=role, created_at=datetime.utcnow())
                db.session.add(new_user)
                db.session.commit()
                flash(f"✅ Utilisateur '{username}' ajouté avec le rôle '{role}'.", "success")
            else:
                flash(f"L'utilisateur '{username}' existe déjà.", "warning")
        elif action == "delete" and username:
            if username == "admin": # Prevent deleting the main admin user
                flash("❌ Impossible de supprimer l'utilisateur 'admin'.", "danger")
            else:
                user_to_delete = DBUser.query.filter_by(id=username).first()
                if user_to_delete:
                    db.session.delete(user_to_delete)
                    db.session.commit()
                    flash(f"🗑️ Utilisateur '{username}' supprimé.", "success")
                else:
                    flash(f"Utilisateur '{username}' non trouvé.", "warning")
        else:
            flash("❌ Action invalide ou champs manquants (nom d'utilisateur et mot de passe requis pour ajout).", "danger")
        return redirect(url_for('admin_panel')) # Redirect to refresh the admin panel

    users = DBUser.query.all()
    return render_template('admin.html', utilisateurs=users, current_user=current_user)

# Optional: Error handlers for common HTTP errors
@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404 # Create a 404.html template

@app.errorhandler(500)
def internal_server_error(e):
    db.session.rollback() # Rollback session in case of DB error leading to 500
    return render_template('500.html'), 500 # Create a 500.html template

@app.errorhandler(403)
def forbidden_access(e):
    return render_template('403.html'), 403 # Create a 403.html template


if __name__ == '__main__':
    # For local development, debug=True can be helpful.
    # For production (like on Render), debug should be False.
    # Gunicorn or another WSGI server will handle this in production.
    app.run(
        host='0.0.0.0',
        port=int(os.environ.get('PORT', 5000)), # Changed default port for local dev
        debug=os.environ.get('FLASK_DEBUG', 'False').lower() == 'true' # Read from env var
    )
