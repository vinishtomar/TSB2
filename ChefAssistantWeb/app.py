# Last modified: 2025-06-03 10:20:57 UTC by tsbenergie

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
    nom_chantier = db.Column(db.String(255), nullable=True)
    last_modified = db.Column(db.DateTime, default=datetime.utcnow)
    last_modified_by = db.Column(db.String(255))

    # Equipment fields
    equipement_type = db.Column(db.String(255), nullable=True)
    equipement_reference = db.Column(db.String(255), nullable=True)
    equipement_etat = db.Column(db.String(255), nullable=True)
    equipement_date_reception = db.Column(db.String(255), nullable=True)
    equipement_nombre_1 = db.Column(db.String(10), nullable=True)
    equipement_nombre_2 = db.Column(db.String(10), nullable=True)
    equipement_nombre_3 = db.Column(db.String(10), nullable=True)

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
    filename = db.Column(db.String(255), nullable=False)
    content_type = db.Column(db.String(255), nullable=False)
    data = db.Column(db.LargeBinary, nullable=False)
    upload_date = db.Column(db.DateTime, default=datetime.utcnow)

# --- UTILITY FUNCTIONS ---
def create_admin_user_if_not_exists():
    if not DBUser.query.filter_by(id="admin").first():
        hashed_password = bcrypt.generate_password_hash("admin").decode('utf-8')
        admin_user = DBUser(
            id="admin", 
            password_hash=hashed_password, 
            role="admin",
            created_at=datetime.utcnow()
        )
        db.session.add(admin_user)
        db.session.commit()
        app.logger.info("Default admin user created at " + datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S'))

def validate_file_upload(file):
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    if not file.filename:
        return False
    extension = file.filename.rsplit('.', 1)[1].lower()
    return extension in ALLOWED_EXTENSIONS

def save_to_csv(data_dict):
    filepath = os.path.join('uploads', 'suivi_journalier_local_backup.csv')
    file_exists = os.path.isfile(filepath)
    fieldnames = [column.name for column in SuiviJournalier.__table__.columns]
    fieldnames.append('photo_chantier_filenames')
    
    try:
        with open(filepath, mode='a', newline='', encoding='utf-8') as file:
            writer = csv.DictWriter(file, fieldnames=fieldnames, delimiter=';', extrasaction='ignore')
            if not file_exists or os.path.getsize(filepath) == 0:
                writer.writeheader()
            writer.writerow(data_dict)
    except Exception as e:
        app.logger.error(f"Error saving to CSV at {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}: {str(e)}")

# --- INITIALIZE DATABASE AND ADMIN USER ---
with app.app_context():
    db.create_all()
    create_admin_user_if_not_exists()

# --- ROUTES ---
@app.route('/')
@login_required
@app.route('/suivi_journalier')
@login_required
def suivi_journalier():
    if not current_user.role == "admin":
        flash("Accès non autorisé", "error")
        return redirect(url_for('index'))

    page = request.args.get('page', 1, type=int)
    entries_per_page = 10

    # Get all entries with all fields
    entries = db.session.query(Entry)\
        .order_by(Entry.created_at.desc())\
        .paginate(page=page, per_page=entries_per_page, error_out=False)

    return render_template('suivi_journalier.html',
                         entries=entries.items,
                         current_page=page,
                         total_pages=entries.pages,
                         entries_per_page=entries_per_page)

def index():
    if current_user.role == "admin":
        all_lignes = SuiviJournalier.query.order_by(SuiviJournalier.date.desc()).all()
    else:
        all_lignes = SuiviJournalier.query.filter_by(utilisateur=current_user.id).order_by(SuiviJournalier.date.desc()).all()
    return render_template('index.html', all_lignes=all_lignes, current_user=current_user)

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
            return redirect(url_for('index'))
        else:
            flash("Nom d'utilisateur ou mot de passe incorrect.", "danger")
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    session.clear()
    flash("Vous avez été déconnecté.", "success")
    return redirect(url_for('login'))

@app.route('/suivi-journalier', methods=['POST'])
@login_required
def suivi_journalier():
    try:
        data_to_save = {
            "utilisateur": current_user.id,
            "date": datetime.now().strftime('%Y-%m-%d %H:%M'),
            "nom_chantier": request.form.get("nom_chantier"),
            "last_modified": datetime.utcnow(),
            "last_modified_by": current_user.id,
            
            # Equipment data
            "equipement_type": request.form.get("equipement_type_1"),
            "equipement_reference": request.form.get("equipement_reference_1"),
            "equipement_etat": request.form.get("equipement_etat_1"),
            "equipement_date_reception": request.form.get("equipement_date_reception_1"),
            "equipement_nombre_1": request.form.get("equipement_nombre_1"),
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
            "shelter_nombre": request.form.get("shelter_nombre", type=int),
            
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

        # Validate required fields
        required_fields = ["nom_chantier"]
        for field in required_fields:
            if not data_to_save.get(field):
                flash(f"Le champ {field} est requis.", "danger")
                return redirect(url_for('index'))

        entry = SuiviJournalier(**data_to_save)
        db.session.add(entry)
        db.session.flush()

        # Handle image uploads
        photos = request.files.getlist('photo_chantier[]')
        image_filenames_for_csv = []
        
        for photo in photos:
            if photo and photo.filename:
                if not validate_file_upload(photo):
                    flash("Type de fichier non autorisé.", "danger")
                    continue
                    
                img = SuiviJournalierImage(
                    suivi_id=entry.id,
                    filename=photo.filename,
                    content_type=photo.content_type,
                    data=photo.read(),
                    upload_date=datetime.utcnow()
                )
                db.session.add(img)
                image_filenames_for_csv.append(photo.filename)

        db.session.commit()
        flash("Entrée enregistrée avec succès.", "success")

        # Optional: Save to CSV backup
        csv_data = data_to_save.copy()
        csv_data["photo_chantier_filenames"] = ";".join(image_filenames_for_csv)
        save_to_csv(csv_data)

    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error in suivi_journalier at {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}: {str(e)}")
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
                if col_name in request.form and col_name not in ['id', 'date', 'utilisateur']:
                    value = request.form.get(col_name)
                    
                    # Type conversion for specific fields
                    if col_name == "shelter_nombre":
                        value = int(value) if value and value.strip() else None
                    elif col_name in ["temperature", "work_hours"]:
                        value = float(value) if value and value.strip() else None
                    elif col_name == "staff_count":
                        value = int(value) if value and value.strip() else None
                    
                    setattr(entry, col_name, value)
            
            # Update metadata
            entry.last_modified = datetime.utcnow()
            entry.last_modified_by = current_user.id

            # Handle image deletion
            delete_ids_str = request.form.get('delete_images', '')
            if delete_ids_str:
                delete_ids = [int(img_id) for img_id in delete_ids_str.split(',') if img_id.strip().isdigit()]
                for img_id_to_delete in delete_ids:
                    img_to_delete = SuiviJournalierImage.query.get(img_id_to_delete)
                    if img_to_delete and img_to_delete.suivi_id == entry.id:
                        db.session.delete(img_to_delete)
            
            # Handle new image uploads
            photos = request.files.getlist('photo_chantier[]')
            for photo in photos:
                if photo and photo.filename:
                    if not validate_file_upload(photo):
                        flash("Type de fichier non autorisé.", "danger")
                        continue

                    img = SuiviJournalierImage(
                        suivi_id=entry.id,
                        filename=photo.filename,
                        content_type=photo.content_type,
                        data=photo.read(),
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
            
    return render_template('modify_history.html', entry=entry)

@app.route('/delete-history/<int:entry_id>', methods=['POST'])
@login_required
def delete_history(entry_id):
    if current_user.role != "admin":
        flash("Accès refusé : Administrateur seulement.", "danger")
        return redirect(url_for('index'))
    try:
        entry_to_delete = SuiviJournalier.query.get_or_404(entry_id)
        db.session.delete(entry_to_delete)
        db.session.commit()
        flash("Entrée supprimée avec succès.", "success")
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error deleting history entry {entry_id} at {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}: {str(e)}")
        flash(f"Erreur lors de la suppression de l'entrée: {str(e)}", "danger")
    return redirect(url_for('index'))

@app.route('/image/<int:image_id>')
@login_required
def get_image(image_id):
    image = SuiviJournalierImage.query.get_or_404(image_id)
    if current_user.role != 'admin' and image.suivi.utilisateur != current_user.id:
        abort(403)
    return send_file(BytesIO(image.data), mimetype=image.content_type)

@app.route('/telecharger-historique')
@login_required
def telecharger_historique():
    if current_user.role == "admin":
        rows = SuiviJournalier.query.order_by(SuiviJournalier.date.desc()).all()
    else:
        rows = SuiviJournalier.query.filter_by(utilisateur=current_user.id).order_by(SuiviJournalier.date.desc()).all()
    
    fieldnames = [col.name for col in SuiviJournalier.__table__.columns if col.name != 'id'] + ['images_filenames']
    
    csv_buffer = StringIO()
    writer = csv.writer(csv_buffer, delimiter=';')
    writer.writerow(fieldnames)

    for row in rows:
        row_data = []
        for field in fieldnames:
            if field == 'images_filenames':
                photo_filenames = ";".join([img.filename for img in row.images])
                row_data.append(photo_filenames)
            else:
                row_data.append(getattr(row, field, ""))
        writer.writerow(row_data)
        
    csv_buffer.seek(0)
    return Response(
        csv_buffer.getvalue(),
        mimetype='text/csv',
        headers={
            "Content-Disposition": f"attachment;filename=historique_suivi_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        }
    )

@app.route('/telecharger-historique-pdf')
@login_required
def telecharger_historique_pdf():
    if current_user.role != "admin":
        flash("Accès refusé.", "danger")
        return redirect(url_for('index'))

    rows = SuiviJournalier.query.order_by(SuiviJournalier.date.desc()).all()
    
    pdf_buffer = BytesIO()
    doc = SimpleDocTemplate(
        pdf_buffer, 
        pagesize=landscape(letter), 
        topMargin=0.5*inch, 
        bottomMargin=0.5*inch, 
        leftMargin=0.3*inch, 
        rightMargin=0.3*inch
    )
    
    elements = []
    styles = getSampleStyleSheet()
    
    # Custom styles
    small_body_style = ParagraphStyle(
        'smallBodyText',
        parent=styles['Normal'],
        fontSize=7
    )
    small_bold_style = ParagraphStyle(
        'smallBoldText',
        parent=styles['Normal'],
        fontSize=7,
        fontName='Helvetica-Bold'
    )

    # Title
    title_style = styles['Heading1']
    title_style.alignment = 1
    elements.append(Paragraph(
        f"Historique des Suivi Journaliers (Généré le {datetime.now().strftime('%Y-%m-%d %H:%M')})",
        title_style
    ))
    elements.append(Spacer(1, 0.2*inch))

    # Define columns for PDF
    pdf_fieldnames = [
        "date", "utilisateur", "nom_chantier",
        "equipement_type", "equip_ref", "equip_etat",
        "weather_conditions", "temperature",
        "cables_dc", "cables_ac", "cables_terre",
        "problems", "fin_stat", "img_count"
    ]
    
    pdf_headers = {
        "date": "Date", "utilisateur": "Utilisateur",
        "nom_chantier": "Nom du Chantier",
        "equipement_type": "Type Équip.",
        "equip_ref": "Réf. Équip.",
        "equip_etat": "État Équip.",
        "weather_conditions": "Météo",
        "temperature": "Temp. °C",
        "cables_dc": "Câbles DC (m)",
        "cables_ac": "Câbles AC (m)",
        "cables_terre": "Terre (m)",
        "problems": "Problèmes",
        "fin_stat": "Status",
        "img_count": "Photos"
    }

    header_paragraphs = [
        Paragraph(f"<b>{pdf_headers.get(fn, fn.replace('_', ' ').title())}</b>", small_bold_style)
        for fn in pdf_fieldnames
    ]
    data_for_table = [header_paragraphs]

    for row in rows:
        row_data_paragraphs = []
        for field in pdf_fieldnames:
            cell_content_str = ""
            if field == 'img_count':
                cell_content_str = str(len(row.images))
            elif field == 'equip_ref':
                cell_content_str = str(getattr(row, "equipement_reference", ""))
            elif field == 'equip_etat':
                cell_content_str = str(getattr(row, "equipement_etat", ""))
            elif field == 'cables_dc':
                cell_content_str = str(getattr(row, "cables_dctires", ""))
            elif field == 'cables_ac':
                cell_content_str = str(getattr(row, "cables_actires", ""))
            elif field == 'cables_terre':
                cell_content_str = str(getattr(row, "cables_terretires", ""))
            elif field == 'fin_stat':
                cell_content_str = str(getattr(row, "fin_status", ""))
            elif hasattr(row, field):
                cell_content_str = str(getattr(row, field, ""))
            
            # Truncate long text
            max_len = 25
            if len(cell_content_str) > max_len:
                cell_content_str = cell_content_str[:max_len-3] + "..."
            row_data_paragraphs.append(Paragraph(cell_content_str, small_body_style))
        data_for_table.append(row_data_paragraphs)

    if len(data_for_table) > 1:
        col_widths = [
            1.0*inch, 0.8*inch, 1.0*inch,  # date, util, nom_chantier
            0.8*inch, 0.8*inch, 0.7*inch,  # equip_type, ref, etat
            0.7*inch, 0.5*inch,            # weather, temp
            0.7*inch, 0.7*inch, 0.7*inch,  # cables (dc, ac, terre)
            1.5*inch, 0.7*inch, 0.5*inch   # problems, status, photos
        ]
        
        table = Table(data_for_table, colWidths=col_widths, repeatRows=1)
        table_style = TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.darkslategray),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 7),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('TOPPADDING', (0, 0), (-1, 0), 8),
            ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('FONTSIZE', (0, 1), (-1, -1), 7),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('LEFTPADDING', (0,0), (-1,-1), 4),
            ('RIGHTPADDING', (0,0), (-1,-1), 4),
            ('TOPPADDING', (0,1), (-1,-1), 4),
            ('BOTTOMPADDING', (0,1), (-1,-1), 4),
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
        as_attachment=True,
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
        role = request.form.get('role', 'user')

        if action == "add" and username and password:
            if not DBUser.query.filter_by(id=username).first():
                hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
                new_user = DBUser(
                    id=username,
                    password_hash=hashed_password,
                    role=role,
                    created_at=datetime.utcnow()
                )
                db.session.add(new_user)
                db.session.commit()
                flash(f"✅ Utilisateur '{username}' ajouté avec le rôle '{role}'.", "success")
            else:
                flash(f"L'utilisateur '{username}' existe déjà.", "warning")
        elif action == "delete" and username:
            if username == "admin":
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
            flash("❌ Action invalide ou champs manquants.", "danger")
        return redirect(url_for('admin_panel'))

    users = DBUser.query.all()
    return render_template('admin.html', utilisateurs=users, current_user=current_user)

if __name__ == '__main__':
    app.run(
        host='0.0.0.0',
        port=int(os.environ.get('PORT', 10000)),
        debug=False
    )
