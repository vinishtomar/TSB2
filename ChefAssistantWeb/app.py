import os
import csv
from flask import Flask, render_template, request, redirect, url_for, flash, Response, send_file, session, abort # Added session
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_bcrypt import Bcrypt
from flask_sqlalchemy import SQLAlchemy
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

app.secret_key = os.environ.get('SECRET_KEY', os.urandom(24))

app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get(
    'DATABASE_URL',
    'sqlite:///' + os.path.join(os.path.abspath(os.path.dirname(__file__)), 'site.db')
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class DBUser(db.Model):
    __tablename__ = 'db_user'
    id = db.Column(db.String(255), primary_key=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(50), nullable=False, default="user")

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
    nom_du_chantier = db.Column(db.String(255), nullable=True)

    # --- ADDED FOR CHANTIER TYPE AND CONDITIONAL FIELDS --- START
    chantier_type = db.Column(db.String(50), nullable=True) # e.g., 'centrale-sol', 'ombriere', 'toiture'
    interconnexion = db.Column(db.String(255), nullable=True) # For 'centrale-sol' and 'ombriere'
    nombre_panneaux = db.Column(db.Integer, nullable=True)   # For 'toiture'
    nombre_rail = db.Column(db.Integer, nullable=True)       # For 'toiture'
    # --- ADDED FOR CHANTIER TYPE AND CONDITIONAL FIELDS --- END

    equipement_type = db.Column(db.String(255), nullable=True)
    equipement_reference = db.Column(db.String(255), nullable=True)
    equipement_etat = db.Column(db.String(255), nullable=True)
    equipement_date_reception = db.Column(db.String(255), nullable=True)
    equipement_nombre_1 = db.Column(db.String(10), nullable=True)
    equipement_nombre_2 = db.Column(db.String(10), nullable=True)
    equipement_nombre_3 = db.Column(db.String(10), nullable=True)
    connecteur_type = db.Column(db.String(255), nullable=True)
    connecteur_quantite = db.Column(db.String(255), nullable=True)
    connecteur_etat = db.Column(db.String(255), nullable=True)
    chemin_cable_longueur = db.Column(db.String(255), nullable=True)
    chemin_cable_type = db.Column(db.String(255), nullable=True)
    chemin_cable_section = db.Column(db.String(255), nullable=True)
    chemin_cable_profondeur = db.Column(db.String(255), nullable=True)
    terre_longueur = db.Column(db.String(255), nullable=True)
    cableac_section = db.Column(db.String(255), nullable=True)
    cableac_longueur = db.Column(db.String(255), nullable=True)
    cabledc_section = db.Column(db.String(255), nullable=True)
    cabledc_longueur = db.Column(db.String(255), nullable=True)
    shelter_nombre = db.Column(db.Integer, nullable=True)
    cables_dctires = db.Column(db.String(255), nullable=True)
    cables_actires = db.Column(db.String(255), nullable=True)
    cables_terretires = db.Column(db.String(255), nullable=True)
    problems = db.Column(db.Text, nullable=True)
    fin_zone = db.Column(db.String(255), nullable=True)
    fin_string = db.Column(db.String(255), nullable=True)
    fin_tension_dc = db.Column(db.String(255), nullable=True)
    fin_courant_dc = db.Column(db.String(255), nullable=True)
    fin_tension_ac = db.Column(db.String(255), nullable=True)
    fin_puissance = db.Column(db.String(255), nullable=True)
    fin_date = db.Column(db.String(255), nullable=True)
    fin_technicien = db.Column(db.String(255), nullable=True)
    fin_status = db.Column(db.String(255), nullable=True)
    images = db.relationship('SuiviJournalierImage', backref='suivi', lazy=True, cascade="all, delete-orphan")

class SuiviJournalierImage(db.Model):
    __tablename__ = 'new_suivi_journalier_image'
    id = db.Column(db.Integer, primary_key=True)
    suivi_id = db.Column(db.Integer, db.ForeignKey('new_suivi_journalier.id'), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    content_type = db.Column(db.String(255), nullable=False)
    data = db.Column(db.LargeBinary, nullable=False)

def create_admin_user_if_not_exists():
    if not DBUser.query.filter_by(id="admin").first():
        hashed_password = bcrypt.generate_password_hash("admin").decode('utf-8')
        admin_user = DBUser(id="admin", password_hash=hashed_password, role="admin")
        db.session.add(admin_user)
        db.session.commit()
        app.logger.info("Default admin user created.")

with app.app_context():
    db.create_all()
    create_admin_user_if_not_exists()

@app.route('/')
@login_required
def index():
    if current_user.role == "admin":
        all_lignes = SuiviJournalier.query.order_by(SuiviJournalier.date.desc()).all()
    else:
        all_lignes = SuiviJournalier.query.filter_by(utilisateur=current_user.id).order_by(SuiviJournalier.date.desc()).all()
    # Pass session to template so chantier_type can be accessed for conditional rendering
    return render_template('index.html', all_lignes=all_lignes, current_user=current_user, session=session)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        # --- ADDED FOR CHANTIER TYPE --- START
        chantier_type_from_form = request.form.get('chantier_type')
        # --- ADDED FOR CHANTIER TYPE --- END

        user_from_db = DBUser.query.filter_by(id=username).first()
        if user_from_db and bcrypt.check_password_hash(user_from_db.password_hash, password):
            user_obj = User(user_from_db.id, user_from_db.role)
            login_user(user_obj)
            # --- ADDED FOR CHANTIER TYPE --- START
            session['chantier_type'] = chantier_type_from_form # Store in session
            # --- ADDED FOR CHANTIER TYPE --- END
            return redirect(url_for('index'))
        else:
            flash("Nom d'utilisateur ou mot de passe incorrect.", "danger")
    return render_template('login.html') # login.html is your template name

@app.route('/logout')
@login_required
def logout():
    # --- ADDED FOR CHANTIER TYPE --- START
    session.pop('chantier_type', None) # Clear chantier_type from session
    # --- ADDED FOR CHANTIER TYPE --- END
    logout_user()
    # session.clear() # This would also clear chantier_type, but explicit pop is fine
    flash("Vous avez été déconnecté.", "success")
    return redirect(url_for('login'))

@app.route('/suivi-journalier', methods=['POST'])
@login_required
def suivi_journalier():
    try:
        data_to_save = {
            "utilisateur": current_user.id,
            "date": datetime.now().strftime('%Y-%m-%d %H:%M'),
            "nom_du_chantier": request.form.get("nom_du_chantier"),
            # --- ADDED FOR CHANTIER TYPE AND CONDITIONAL FIELDS --- START
            "chantier_type": session.get('chantier_type'), # Get from session
            # --- ADDED FOR CHANTIER TYPE AND CONDITIONAL FIELDS --- END
            "equipement_type": request.form.get("equipement_type_1"),
            "equipement_reference": request.form.get("equipement_reference_1"),
            "equipement_etat": request.form.get("equipement_etat_1"),
            "equipement_date_reception": request.form.get("equipement_date_reception_1"),
            "equipement_nombre_1": request.form.get("equipement_nombre_1"),
            "equipement_nombre_2": request.form.get("equipement_nombre_2"),
            "equipement_nombre_3": request.form.get("equipement_nombre_3"),
            "connecteur_type": request.form.get("connecteur_type"),
            "connecteur_quantite": request.form.get("connecteur_quantite"),
            "connecteur_etat": request.form.get("connecteur_etat"),
            "chemin_cable_longueur": request.form.get("chemin_cable_longueur"),
            "chemin_cable_type": request.form.get("chemin_cable_type"),
            "chemin_cable_section": request.form.get("chemin_cable_section"),
            "chemin_cable_profondeur": request.form.get("chemin_cable_profondeur"),
            "terre_longueur": request.form.get("terre_longueur"),
            "cableac_section": request.form.get("cableac_section"),
            "cableac_longueur": request.form.get("cableac_longueur"),
            "cabledc_section": request.form.get("cabledc_section"),
            "cabledc_longueur": request.form.get("cabledc_longueur"),
            "shelter_nombre": request.form.get("shelter_nombre", type=int) if request.form.get("shelter_nombre") else None,
            "cables_dctires": request.form.get("cables_dctires"),
            "cables_actires": request.form.get("cables_actires"),
            "cables_terretires": request.form.get("cables_terretires"),
            "problems": request.form.get("problems"),
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

        # --- ADDED FOR CHANTIER TYPE AND CONDITIONAL FIELDS --- START
        current_chantier_type = session.get('chantier_type')
        if request.form.get("section") == "avancement": # Only for avancement section
            if current_chantier_type in ['centrale-sol', 'ombriere']:
                data_to_save["interconnexion"] = request.form.get("interconnexion")
            elif current_chantier_type == 'toiture':
                data_to_save["nombre_panneaux"] = request.form.get("nombre_panneaux", type=int) if request.form.get("nombre_panneaux") else None
                data_to_save["nombre_rail"] = request.form.get("nombre_rail", type=int) if request.form.get("nombre_rail") else None
        # --- ADDED FOR CHANTIER TYPE AND CONDITIONAL FIELDS --- END

        entry = SuiviJournalier(**data_to_save)
        db.session.add(entry)
        db.session.flush()

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
        flash("Entrée enregistrée avec succès.", "success")

    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error in suivi_journalier: {str(e)}")
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
            for column in SuiviJournalier.__table__.columns:
                col_name = column.name
                if col_name in request.form:
                    if col_name in ['id', 'date', 'utilisateur', 'chantier_type']: # Protect chantier_type from direct modification here
                        continue
                    
                    value = request.form.get(col_name)
                    if col_name == "shelter_nombre":
                        value = int(value) if value and value.strip() else None
                    # --- ADDED FOR CHANTIER TYPE AND CONDITIONAL FIELDS (modify) --- START
                    elif col_name == "nombre_panneaux":
                        value = int(value) if value and value.strip() else None
                    elif col_name == "nombre_rail":
                        value = int(value) if value and value.strip() else None
                    # interconnexion is string, handled by default
                    # --- ADDED FOR CHANTIER TYPE AND CONDITIONAL FIELDS (modify) --- END
                    setattr(entry, col_name, value)
            
            # If chantier_type specific fields were submitted (because they were visible on the form)
            # and they are not directly in SuiviJournalier.__table__.columns for the generic loop
            # (though they are, so the above loop should catch them)
            # This is more of a safeguard or alternative for explicit handling:
            if entry.chantier_type in ['centrale-sol', 'ombriere']:
                if 'interconnexion' in request.form:
                    entry.interconnexion = request.form.get('interconnexion')
            elif entry.chantier_type == 'toiture':
                if 'nombre_panneaux' in request.form:
                    entry.nombre_panneaux = request.form.get('nombre_panneaux', type=int) if request.form.get('nombre_panneaux') else None
                if 'nombre_rail' in request.form:
                    entry.nombre_rail = request.form.get('nombre_rail', type=int) if request.form.get('nombre_rail') else None

            delete_ids_str = request.form.get('delete_images', '')
            if delete_ids_str:
                delete_ids = [int(img_id) for img_id in delete_ids_str.split(',') if img_id.strip().isdigit()]
                for img_id_to_delete in delete_ids:
                    img_to_delete = SuiviJournalierImage.query.get(img_id_to_delete)
                    if img_to_delete and img_to_delete.suivi_id == entry.id:
                        db.session.delete(img_to_delete)
            
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
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Error modifying history entry {entry_id}: {str(e)}")
            flash(f"Erreur lors de la modification : {str(e)}", "danger")
            
    return render_template('modify_history.html', entry=entry) # Make sure modify_history.html exists

@app.route('/delete-history/<int:entry_id>', methods=['POST'])
@login_required
def delete_history(entry_id):
    # ... (no changes needed here for this feature)
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
        app.logger.error(f"Error deleting history entry {entry_id}: {str(e)}")
        flash(f"Erreur lors de la suppression de l'entrée: {str(e)}", "danger")
    return redirect(url_for('index'))

@app.route('/image/<int:image_id>')
@login_required
def get_image(image_id):
    # ... (no changes needed here for this feature)
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
    
    # --- MODIFIED FOR CHANTIER TYPE FIELDS (CSV) --- START
    # The dynamic fieldname generation will pick up the new columns.
    # Ensure the order is logical if desired, or list them explicitly.
    # For simplicity, we'll let the dynamic generation include them.
    # If specific order is needed:
    # fieldnames = ["date", "utilisateur", "nom_du_chantier", "chantier_type", "equipement_type", ..., "interconnexion", "nombre_panneaux", "nombre_rail", ..., "images_filenames"]
    fieldnames = [col.name for col in SuiviJournalier.__table__.columns if col.name not in ['id']] + ['images_filenames']
    # --- MODIFIED FOR CHANTIER TYPE FIELDS (CSV) --- END
    
    csv_buffer = StringIO()
    writer = csv.writer(csv_buffer, delimiter=';')
    writer.writerow(fieldnames)

    for row in rows:
        row_data = []
        for field in fieldnames:
            if field == 'images_filenames':
                photo_filenames = ";".join([img.filename for img in row.images])
                row_data.append(photo_filenames)
            elif hasattr(row, field):
                row_data.append(getattr(row, field, ""))
            else:
                row_data.append("")
        writer.writerow(row_data)
        
    csv_buffer.seek(0)
    return Response(
        csv_buffer.getvalue(),
        mimetype='text/csv',
        headers={"Content-Disposition": f"attachment;filename={current_user.id}_historique_suivi.csv"}
    )

@app.route('/telecharger-historique-pdf')
@login_required
def telecharger_historique_pdf():
    if current_user.role != "admin":
        flash("Accès refusé.", "danger")
        return redirect(url_for('index'))

    rows = SuiviJournalier.query.order_by(SuiviJournalier.date.desc()).all()
    
    pdf_buffer = BytesIO()
    doc = SimpleDocTemplate(pdf_buffer, pagesize=landscape(letter), topMargin=0.5*inch, bottomMargin=0.5*inch, leftMargin=0.1*inch, rightMargin=0.1*inch) # Adjusted margins
    elements = []
    styles = getSampleStyleSheet()
    
    small_body_style = ParagraphStyle('smallBodyText', parent=styles['Normal'], fontSize=5) # Even smaller
    small_bold_style = ParagraphStyle('smallBoldText', parent=styles['Normal'], fontSize=5, fontName='Helvetica-Bold')

    title_style = styles['h1']
    title_style.alignment = 1
    elements.append(Paragraph("Historique des Suivi Journaliers", title_style))
    elements.append(Spacer(1, 0.2*inch))

    # --- MODIFIED FOR CHANTIER TYPE FIELDS (PDF) --- START
    pdf_fieldnames = [
        "date", "util", "nom_chantier", "type_chantier", # Added type_chantier
        "equip_type", "equip_ref", "equip_etat",
        "cables_dc", "cables_ac", "cables_terre",
        "interconnexion", "nb_panneaux", "nb_rail",      # Added new fields
        "problems", "fin_stat", "img_count" 
    ]
    
    pdf_headers = {
        "date": "Date", "util": "Util.", "nom_chantier": "Nom Chant.", "type_chantier": "Type Chant.",
        "equip_type": "Type Éq.", "equip_ref": "Réf. Éq.", "equip_etat": "État Éq.",
        "cables_dc": "DC Tiré", "cables_ac": "AC Tiré", "cables_terre": "Terre Tiré",
        "interconnexion": "Interco.", "nb_panneaux": "Nb Pan.", "nb_rail": "Nb Rail",
        "problems": "Problèmes", "fin_stat": "Stat. Fin", "img_count": "Imgs"
    }
    # --- MODIFIED FOR CHANTIER TYPE FIELDS (PDF) --- END

    header_paragraphs = [Paragraph(f"<b>{pdf_headers.get(fn, fn.replace('_', ' ').title())}</b>", small_bold_style) for fn in pdf_fieldnames]
    data_for_table = [header_paragraphs]

    for row in rows:
        row_data_paragraphs = []
        for field_key in pdf_fieldnames: # Use field_key to iterate pdf_fieldnames
            cell_content_str = ""
            # Map pdf_fieldnames keys to actual SuiviJournalier model attribute names
            actual_attr = ""
            if field_key == 'img_count': cell_content_str = str(len(row.images))
            elif field_key == 'util': actual_attr = "utilisateur"
            elif field_key == 'nom_chantier': actual_attr = "nom_du_chantier"
            elif field_key == 'type_chantier': actual_attr = "chantier_type"
            elif field_key == 'equip_type': actual_attr = "equipement_type"
            elif field_key == 'equip_ref': actual_attr = "equipement_reference"
            elif field_key == 'equip_etat': actual_attr = "equipement_etat"
            elif field_key == 'cables_dc': actual_attr = "cables_dctires"
            elif field_key == 'cables_ac': actual_attr = "cables_actires"
            elif field_key == 'cables_terre': actual_attr = "cables_terretires"
            elif field_key == 'interconnexion':
                if row.chantier_type in ['centrale-sol', 'ombriere']:
                    actual_attr = "interconnexion"
                else: cell_content_str = "-" # Explicitly empty if not applicable
            elif field_key == 'nb_panneaux':
                if row.chantier_type == 'toiture':
                    actual_attr = "nombre_panneaux"
                else: cell_content_str = "-"
            elif field_key == 'nb_rail':
                if row.chantier_type == 'toiture':
                    actual_attr = "nombre_rail"
                else: cell_content_str = "-"
            elif field_key == 'problems': actual_attr = "problems"
            elif field_key == 'fin_stat': actual_attr = "fin_status"
            elif field_key == 'date': actual_attr = "date" # direct map

            if actual_attr and hasattr(row, actual_attr):
                 cell_content_str = str(getattr(row, actual_attr, ""))
            
            max_len = 15 # Adjusted for very small font
            if len(cell_content_str) > max_len:
                cell_content_str = cell_content_str[:max_len-3] + "..."
            row_data_paragraphs.append(Paragraph(cell_content_str, small_body_style))
        data_for_table.append(row_data_paragraphs)

    if len(data_for_table) > 1:
        # --- MODIFIED FOR CHANTIER TYPE FIELDS (PDF col widths) --- START
        # Total width ~10.8 inches. 16 columns. ~0.675 inch per column on average.
        col_widths = [
            0.7*inch, 0.5*inch, 0.7*inch, 0.6*inch,  # date, util, nom_chantier, type_chantier
            0.6*inch, 0.6*inch, 0.5*inch,           # equip_type, ref, etat
            0.5*inch, 0.5*inch, 0.5*inch,           # dc, ac, terre
            0.7*inch, 0.5*inch, 0.5*inch,           # interco, nb_pan, nb_rail
            1.2*inch, 0.6*inch, 0.5*inch            # problems, fin_stat, img_count
        ] # Sum: 10.3 inches
        # --- MODIFIED FOR CHANTIER TYPE FIELDS (PDF col widths) --- END
        
        table = Table(data_for_table, colWidths=col_widths, repeatRows=1) 
        table_style = TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.darkslategray), ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'), ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'), ('FONTSIZE', (0, 0), (-1, 0), 5),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 4), ('TOPPADDING', (0, 0), (-1, 0), 4),
            ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey), ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('FONTSIZE', (0, 1), (-1, -1), 5), ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('LEFTPADDING', (0,0), (-1,-1), 2), ('RIGHTPADDING', (0,0), (-1,-1), 2),
            ('TOPPADDING', (0,1), (-1,-1), 2), ('BOTTOMPADDING', (0,1), (-1,-1), 2),
        ])
        table.setStyle(table_style)
        elements.append(table)
    else:
        elements.append(Paragraph("Aucune donnée à afficher.", styles['Normal']))

    doc.build(elements)
    pdf_buffer.seek(0)
    return send_file(pdf_buffer, mimetype='application/pdf', as_attachment=True, download_name="historique_suivi.pdf")

@app.route('/admin', methods=['GET', 'POST'])
@login_required
def admin_panel():
    # ... (no changes needed here for this feature)
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
                new_user = DBUser(id=username, password_hash=hashed_password, role=role)
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
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 10000)), debug=False)
