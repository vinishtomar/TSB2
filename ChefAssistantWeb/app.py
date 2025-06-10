import os
import csv
from flask import (Flask, render_template, request, redirect, url_for, flash, 
                   Response, send_file, session, abort)
from flask_login import (LoginManager, UserMixin, login_user, login_required, 
                         logout_user, current_user)
from flask_bcrypt import Bcrypt
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import distinct
from io import StringIO, BytesIO
from datetime import datetime
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import (SimpleDocTemplate, Table, TableStyle, 
                                Paragraph, Spacer)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch

# --- TOP LEVEL - NO INDENTATION BEFORE THESE LINES ---
app = Flask(__name__)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = "login"
login_manager.login_message = "Veuillez vous connecter pour accéder à cette page."
login_manager.login_message_category = "info"

app.secret_key = os.environ.get('SECRET_KEY', os.urandom(24))

# Use the provided database link
YOUR_DATABASE_LINK = "postgresql://tsb_jilz_user:WQuuirqxSdknwZjsvldYzD0DbhcOBzQ7@dpg-d0jjegmmcj7s73836lp0-a/tsb_jilz"
app.config['SQLALCHEMY_DATABASE_URI'] = YOUR_DATABASE_LINK
print(f"INFO: Using HARDCODED DATABASE_URL: {app.config['SQLALCHEMY_DATABASE_URI']}")

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)
# --- END OF TOP LEVEL CONFIGURATION ---

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

class VinishSuivi(db.Model):
    __tablename__ = 'vinish_database'
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.String(50), default=lambda: datetime.now().strftime('%Y-%m-%d %H:%M'))
    utilisateur = db.Column(db.String(255))
    nom_du_chantier = db.Column(db.String(255), nullable=True)
    chantier_type = db.Column(db.String(50), nullable=True)

    # Reception Fields
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
    chemin_cable_type = db.Column(db.String(255), nullable=True)
    chemin_cable_longueur = db.Column(db.String(255), nullable=True)
    chemin_cable_section = db.Column(db.String(255), nullable=True)
    chemin_cable_profondeur = db.Column(db.String(255), nullable=True)
    terre_longueur = db.Column(db.String(255), nullable=True)
    cableac_section = db.Column(db.String(255), nullable=True)
    cableac_longueur = db.Column(db.String(255), nullable=True)
    cabledc_section = db.Column(db.String(255), nullable=True)
    cabledc_longueur = db.Column(db.String(255), nullable=True)
    onduleur_nombre = db.Column(db.Integer, nullable=True)
    shelter_nombre = db.Column(db.Integer, nullable=True)

    # Avancement Fields
    cables_dctires = db.Column(db.String(255), nullable=True)
    cables_actires = db.Column(db.String(255), nullable=True)
    cables_terretires = db.Column(db.String(255), nullable=True)
    equipe = db.Column(db.String(255), nullable=True)
    onduleur_details_avancement = db.Column(db.Text, nullable=True)
    heure_de_travail = db.Column(db.String(50), nullable=True)
    interconnexion = db.Column(db.String(255), nullable=True)
    nombre_panneaux = db.Column(db.Integer, nullable=True)
    nombre_rail = db.Column(db.Integer, nullable=True)
    problems = db.Column(db.Text, nullable=True)

    # Fin Fields
    fin_zone = db.Column(db.String(255), nullable=True)
    fin_string = db.Column(db.String(255), nullable=True)
    fin_tension_dc = db.Column(db.String(255), nullable=True)
    fin_courant_dc = db.Column(db.String(255), nullable=True)
    fin_tension_ac = db.Column(db.String(255), nullable=True)
    fin_puissance = db.Column(db.String(255), nullable=True)
    fin_date = db.Column(db.String(255), nullable=True)
    fin_technicien = db.Column(db.String(255), nullable=True)
    fin_status = db.Column(db.String(255), nullable=True)
    
    images = db.relationship('VinishSuiviImage', backref='suivi_entry', lazy=True, cascade="all, delete-orphan")

class VinishSuiviImage(db.Model):
    __tablename__ = 'vinish_database_image'
    id = db.Column(db.Integer, primary_key=True)
    suivi_entry_id = db.Column(db.Integer, db.ForeignKey('vinish_database.id'), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    content_type = db.Column(db.String(255), nullable=False)
    data = db.Column(db.LargeBinary, nullable=False)

def create_admin_user_if_not_exists():
    with app.app_context():
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
    base_query = VinishSuivi.query
    if current_user.role != "admin":
        base_query = base_query.filter(VinishSuivi.utilisateur == current_user.id)

    filter_utilisateur_req = request.args.get('filter_utilisateur')
    filter_nom_chantier_req = request.args.get('filter_nom_chantier')
    active_tab_from_url = request.args.get('active_tab', 'reception')

    if filter_utilisateur_req:
        if current_user.role == "admin":
            base_query = base_query.filter(VinishSuivi.utilisateur == filter_utilisateur_req)
    
    if filter_nom_chantier_req:
        base_query = base_query.filter(VinishSuivi.nom_du_chantier == filter_nom_chantier_req)

    all_lignes = base_query.order_by(VinishSuivi.date.desc()).all()

    distinct_users = []
    distinct_nom_chantiers = []
    if current_user.role == "admin":
        distinct_users_query = db.session.query(distinct(VinishSuivi.utilisateur)).order_by(VinishSuivi.utilisateur).all()
        distinct_users = [user[0] for user in distinct_users_query if user[0]]
        distinct_nom_chantiers_query = db.session.query(distinct(VinishSuivi.nom_du_chantier))\
            .filter(VinishSuivi.nom_du_chantier.isnot(None), VinishSuivi.nom_du_chantier != '')\
            .order_by(VinishSuivi.nom_du_chantier).all()
        distinct_nom_chantiers = [name[0] for name in distinct_nom_chantiers_query if name[0]]
    else:
        user_has_entries = VinishSuivi.query.filter_by(utilisateur=current_user.id).first()
        if user_has_entries:
            distinct_users = [current_user.id]
        
        distinct_nom_chantiers_user_query = db.session.query(distinct(VinishSuivi.nom_du_chantier))\
            .filter(VinishSuivi.utilisateur == current_user.id)\
            .filter(VinishSuivi.nom_du_chantier.isnot(None), VinishSuivi.nom_du_chantier != '')\
            .order_by(VinishSuivi.nom_du_chantier).all()
        distinct_nom_chantiers = [name[0] for name in distinct_nom_chantiers_user_query if name[0]]

    return render_template('index.html',
                           all_lignes=all_lignes,
                           current_user=current_user,
                           session=session,
                           distinct_users=distinct_users,
                           distinct_nom_chantiers=distinct_nom_chantiers,
                           current_filter_utilisateur=filter_utilisateur_req,
                           current_filter_nom_chantier=filter_nom_chantier_req,
                           active_tab=active_tab_from_url)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        chantier_type_from_form = request.form.get('chantier_type')
        user_from_db = DBUser.query.filter_by(id=username).first()
        if user_from_db and bcrypt.check_password_hash(user_from_db.password_hash, password):
            user_obj = User(user_from_db.id, user_from_db.role)
            login_user(user_obj)
            session['chantier_type'] = chantier_type_from_form
            return redirect(url_for('index'))
        else:
            flash("Nom d'utilisateur ou mot de passe incorrect.", "danger")
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    session.pop('chantier_type', None)
    logout_user()
    flash("Vous avez été déconnecté.", "success")
    return redirect(url_for('login'))

@app.route('/suivi-journalier', methods=['POST'])
@login_required
def suivi_journalier():
    active_tab_after_submit = "reception"
    section = request.form.get("section")
    
    try:
        if section == "reception_complete":
            active_tab_after_submit = "reception"
            entry = VinishSuivi(
                utilisateur=current_user.id,
                chantier_type=session.get('chantier_type'),
                nom_du_chantier=request.form.get("nom_du_chantier_reception"),
                equipement_type=request.form.get("equipement_type_1"),
                equipement_reference=request.form.get("equipement_reference_1"),
                equipement_etat=request.form.get("equipement_etat_1"),
                equipement_date_reception=request.form.get("equipement_date_reception_1"),
                equipement_nombre_1=request.form.get("equipement_nombre_1"),
                equipement_nombre_2=request.form.get("equipement_nombre_2"),
                equipement_nombre_3=request.form.get("equipement_nombre_3"),
                connecteur_type=request.form.get("connecteur_type"),
                connecteur_quantite=request.form.get("connecteur_quantite"),
                connecteur_etat=request.form.get("connecteur_etat"),
                chemin_cable_type=request.form.get("chemin_cable_type"),
                chemin_cable_longueur=request.form.get("chemin_cable_longueur"),
                chemin_cable_section=request.form.get("chemin_cable_section"),
                chemin_cable_profondeur=request.form.get("chemin_cable_profondeur"),
                terre_longueur=request.form.get("terre_longueur"),
                cableac_section=request.form.get("cableac_section"),
                cableac_longueur=request.form.get("cableac_longueur"),
                cabledc_section=request.form.get("cabledc_section"),
                cabledc_longueur=request.form.get("cabledc_longueur"),
                onduleur_nombre=request.form.get("onduleur_nombre_reception", type=int) if request.form.get("onduleur_nombre_reception") else None,
                shelter_nombre=request.form.get("shelter_nombre_reception", type=int) if request.form.get("shelter_nombre_reception") else None,
            )
            db.session.add(entry)
            db.session.flush()

            photos = request.files.getlist('photo_chantier_reception[]')
            for photo in photos:
                if photo and photo.filename:
                    img = VinishSuiviImage(
                        suivi_entry_id=entry.id,
                        filename=photo.filename,
                        content_type=photo.content_type,
                        data=photo.read()
                    )
                    db.session.add(img)

        elif section == "avancement":
            active_tab_after_submit = "avancement"
            entry = VinishSuivi(
                utilisateur=current_user.id,
                chantier_type=session.get('chantier_type'),
                nom_du_chantier=request.form.get("nom_du_chantier_avancement"),
                cables_dctires=request.form.get("cables_dctires"),
                cables_actires=request.form.get("cables_actires"),
                cables_terretires=request.form.get("cables_terretires"),
                problems=request.form.get("problems"),
                equipe=request.form.get("equipe_avancement"),
                onduleur_details_avancement=request.form.get("onduleur_avancement"),
                heure_de_travail=request.form.get("heure_travail_avancement"),
            )
            current_chantier_type = session.get('chantier_type')
            if current_chantier_type in ['centrale-sol', 'ombriere']:
                entry.interconnexion = request.form.get("interconnexion")
            elif current_chantier_type == 'toiture':
                entry.nombre_panneaux = request.form.get("nombre_panneaux", type=int) if request.form.get("nombre_panneaux") else None
                entry.nombre_rail = request.form.get("nombre_rail", type=int) if request.form.get("nombre_rail") else None
            
            db.session.add(entry)
            db.session.flush()

            photos = request.files.getlist('photo_chantier_avancement[]')
            for photo in photos:
                if photo and photo.filename:
                    img = VinishSuiviImage(
                        suivi_entry_id=entry.id,
                        filename=photo.filename,
                        content_type=photo.content_type,
                        data=photo.read()
                    )
                    db.session.add(img)

        elif section == "fin":
            active_tab_after_submit = "fin"
            zones = request.form.getlist("fin_zone[]")
            strings = request.form.getlist("fin_string[]")
            tensions_dc = request.form.getlist("fin_tension_dc[]")
            courants_dc = request.form.getlist("fin_courant_dc[]")
            tensions_ac = request.form.getlist("fin_tension_ac[]")
            puissances = request.form.getlist("fin_puissance[]")
            dates = request.form.getlist("fin_date[]")
            techniciens = request.form.getlist("fin_technicien[]")
            statuses = request.form.getlist("fin_status[]")
            
            photos_data = []
            photos = request.files.getlist('photo_chantier_fin[]')
            for photo in photos:
                if photo and photo.filename:
                    photos_data.append({
                        "filename": photo.filename,
                        "content_type": photo.content_type,
                        "data": photo.read()
                    })

            for i in range(len(zones)):
                if zones[i] or strings[i]:
                    entry = VinishSuivi(
                        utilisateur=current_user.id,
                        chantier_type=session.get('chantier_type'),
                        nom_du_chantier=request.form.get("nom_du_chantier_fin"),
                        fin_zone=zones[i],
                        fin_string=strings[i],
                        fin_tension_dc=tensions_dc[i],
                        fin_courant_dc=courants_dc[i],
                        fin_tension_ac=tensions_ac[i],
                        fin_puissance=puissances[i],
                        fin_date=dates[i],
                        fin_technicien=techniciens[i],
                        fin_status=statuses[i],
                    )
                    db.session.add(entry)
                    db.session.flush()

                    for p_data in photos_data:
                        img = VinishSuiviImage(
                            suivi_entry_id=entry.id,
                            filename=p_data["filename"],
                            content_type=p_data["content_type"],
                            data=p_data["data"]
                        )
                        db.session.add(img)
        
        else:
            app.logger.warning(f"Received submission for unhandled section: {section}")
            flash("Action non reconnue ou section invalide.", "warning")
            return redirect(url_for('index', active_tab=active_tab_after_submit))

        db.session.commit()
        flash("Entrée enregistrée avec succès.", "success")

    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error in suivi_journalier (section: {section}): {str(e)}")
        flash(f"❌ Erreur Serveur lors de l'enregistrement: {str(e)}", "danger")
    
    return redirect(url_for('index', active_tab=active_tab_after_submit))


@app.route('/modify-history/<int:entry_id>', methods=['GET', 'POST'])
@login_required
def modify_history(entry_id):
    entry = VinishSuivi.query.get_or_404(entry_id)
    if current_user.role != "admin" and entry.utilisateur != current_user.id:
        flash("Droits insuffisants pour modifier cette entrée.", "danger")
        return redirect(url_for('index', active_tab='history'))

    if request.method == 'POST':
        try:
            for column in VinishSuivi.__table__.columns:
                col_name = column.name
                if col_name in request.form:
                    if col_name in ['id', 'date', 'utilisateur', 'chantier_type']:
                        continue
                    
                    value = request.form.get(col_name)
                    if col_name in ["shelter_nombre", "nombre_panneaux", "nombre_rail", "onduleur_nombre"]:
                        value = int(value) if value and value.strip() else None
                    elif isinstance(getattr(entry, col_name, None), int) and not value:
                        value = None
                    setattr(entry, col_name, value)
            
            delete_ids_str = request.form.get('delete_images', '')
            if delete_ids_str:
                delete_ids = [int(img_id) for img_id in delete_ids_str.split(',') if img_id.strip().isdigit()]
                for img_id_to_delete in delete_ids:
                    img_to_delete = VinishSuiviImage.query.get(img_id_to_delete)
                    if img_to_delete and img_to_delete.suivi_entry_id == entry.id:
                        db.session.delete(img_to_delete)
            
            photos = request.files.getlist('photo_chantier[]')
            for photo in photos:
                if photo and photo.filename:
                    img = VinishSuiviImage(
                        suivi_entry_id=entry.id,
                        filename=photo.filename,
                        content_type=photo.content_type,
                        data=photo.read()
                    )
                    db.session.add(img)
            
            db.session.commit()
            flash("Entrée modifiée avec succès.", "success")
            return redirect(url_for('index', active_tab='history'))
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Error modifying history entry {entry_id}: {str(e)}")
            flash(f"Erreur lors de la modification : {str(e)}", "danger")
            
    return render_template('modify_history.html', entry=entry, current_user=current_user)


@app.route('/delete-history/<int:entry_id>', methods=['POST'])
@login_required
def delete_history(entry_id):
    if current_user.role != "admin":
        flash("Accès refusé : Administrateur seulement.", "danger")
        return redirect(url_for('index'))
    try:
        entry_to_delete = VinishSuivi.query.get_or_404(entry_id)
        db.session.delete(entry_to_delete)
        db.session.commit()
        flash("Entrée supprimée avec succès.", "success")
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error deleting history entry {entry_id}: {str(e)}")
        flash(f"Erreur lors de la suppression de l'entrée: {str(e)}", "danger")
    return redirect(url_for('index', active_tab='history'))

@app.route('/image/<int:image_id>')
@login_required
def get_image(image_id):
    image = VinishSuiviImage.query.get_or_404(image_id)
    if current_user.role != 'admin' and (not image.suivi_entry or image.suivi_entry.utilisateur != current_user.id):
        abort(403)
    return send_file(BytesIO(image.data), mimetype=image.content_type)

def _get_filtered_rows():
    base_query = VinishSuivi.query
    filter_utilisateur_req = request.args.get('filter_utilisateur')
    filter_nom_chantier_req = request.args.get('filter_nom_chantier')

    if current_user.role != "admin":
        base_query = base_query.filter(VinishSuivi.utilisateur == current_user.id)
    elif filter_utilisateur_req:
        base_query = base_query.filter(VinishSuivi.utilisateur == filter_utilisateur_req)
    
    if filter_nom_chantier_req:
        base_query = base_query.filter(VinishSuivi.nom_du_chantier == filter_nom_chantier_req)
        
    return base_query.order_by(VinishSuivi.date.desc()).all()

@app.route('/telecharger-historique')
@login_required
def telecharger_historique():
    rows = _get_filtered_rows()
    fieldnames = [col.name for col in VinishSuivi.__table__.columns if col.name != 'id'] + ['images_filenames']
    
    csv_buffer = StringIO()
    writer = csv.writer(csv_buffer, delimiter=';')
    writer.writerow(fieldnames)

    for row in rows:
        row_data = []
        for field in fieldnames:
            if field == 'images_filenames':
                photo_filenames = "; ".join([img.filename for img in row.images]) 
                row_data.append(photo_filenames)
            elif hasattr(row, field):
                row_data.append(getattr(row, field, ""))
            else:
                row_data.append("")
        writer.writerow(row_data)
        
    csv_buffer.seek(0)
    filename_parts = [current_user.id if current_user.role != "admin" else "admin"]
    filter_utilisateur_req = request.args.get('filter_utilisateur')
    filter_nom_chantier_req = request.args.get('filter_nom_chantier')
    if filter_utilisateur_req:
        filename_parts.append(f"user_{filter_utilisateur_req.replace(' ','_')}")
    if filter_nom_chantier_req:
        filename_parts.append(f"chantier_{filter_nom_chantier_req.replace(' ','_')}")
    filename_parts.append(f"historique_suivi_{datetime.now().strftime('%Y%m%d')}.csv")
    download_filename = "_".join(filename_parts)

    return Response(
        csv_buffer.getvalue(),
        mimetype='text/csv',
        headers={"Content-Disposition": f"attachment;filename={download_filename}"}
    )

@app.route('/telecharger-historique-pdf')
@login_required
def telecharger_historique_pdf():
    # Role check removed to allow all users to download their own filtered PDF
    all_rows = _get_filtered_rows()
    
    reception_rows = []
    avancement_rows = []
    fin_rows = []

    for row in all_rows:
        if row.equipement_type or row.connecteur_type or row.chemin_cable_type or row.terre_longueur or row.cableac_section or row.cabledc_section or row.onduleur_nombre or row.shelter_nombre:
            reception_rows.append(row)
        elif row.cables_dctires or row.cables_actires or row.cables_terretires or row.problems or row.interconnexion or row.nombre_panneaux or row.nombre_rail or row.equipe or row.onduleur_details_avancement or row.heure_de_travail:
            avancement_rows.append(row)
        elif row.fin_zone or row.fin_string:
            fin_rows.append(row)

    pdf_buffer = BytesIO()
    doc = SimpleDocTemplate(pdf_buffer, pagesize=landscape(letter), topMargin=0.5*inch, bottomMargin=0.5*inch, leftMargin=0.25*inch, rightMargin=0.25*inch)
    elements = []
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='SectionTitle', fontSize=14, fontName='Helvetica-Bold', spaceAfter=12))

    title_text = "Historique des Suivi Journaliers"
    elements.append(Paragraph(title_text, styles['h1']))
    elements.append(Spacer(1, 0.2*inch))

    def build_section_table(title, headers, data_rows, attributes, col_widths):
        if not data_rows:
            return

        elements.append(Paragraph(title, styles['SectionTitle']))
        
        table_data = [headers]
        paragraph_style = styles['Normal']
        paragraph_style.fontSize = 7
        for row in data_rows:
            row_data = [Paragraph(str(getattr(row, attr, "")), paragraph_style) for attr in attributes]
            row_data.append(str(len(row.images)))
            table_data.append(row_data)

        table = Table(table_data, repeatRows=1, colWidths=col_widths)
        
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.darkslategray),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 7.5),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 4),
        ]))
        elements.append(table)
        elements.append(Spacer(1, 0.4*inch))

    # Reception Table
    reception_headers = ["Date", "User", "Nom Chantier", "Type Équip.", "Réf.", "État", "Date Récept.", "Nb", "Type Conn.", "Qté", "État", "Type Ch.Câble", "Long.", "Sect.", "Prof.", "L. Terre", "Sect. AC", "L. AC", "Sect. DC", "L. DC", "Nb Ondul.", "Nb Shelter", "Img"]
    reception_attrs = ["date", "utilisateur", "nom_du_chantier", "equipement_type", "equipement_reference", "equipement_etat", "equipement_date_reception", "equipement_nombre_1", "connecteur_type", "connecteur_quantite", "connecteur_etat", "chemin_cable_type", "chemin_cable_longueur", "chemin_cable_section", "chemin_cable_profondeur", "terre_longueur", "cableac_section", "cableac_longueur", "cabledc_section", "cabledc_longueur", "onduleur_nombre", "shelter_nombre"]
    reception_col_widths = [0.5*inch, 0.4*inch, 0.7*inch, 0.55*inch, 0.4*inch, 0.4*inch, 0.5*inch, 0.2*inch, 0.45*inch, 0.25*inch, 0.4*inch, 0.5*inch, 0.3*inch, 0.35*inch, 0.3*inch, 0.4*inch, 0.4*inch, 0.4*inch, 0.4*inch, 0.4*inch, 0.4*inch, 0.4*inch, 0.2*inch]
    build_section_table("Réception du Chantier", reception_headers, reception_rows, reception_attrs, reception_col_widths)

    # Avancement Table
    avancement_headers = ["Date", "User", "Nom Chantier", "Type", "Équipe", "Onduleur", "Heures", "DC (m)", "AC (m)", "Terre (m)", "Interco.", "Panneaux", "Rails (m)", "Problèmes", "Img"]
    avancement_attrs = ["date", "utilisateur", "nom_du_chantier", "chantier_type", "equipe", "onduleur_details_avancement", "heure_de_travail", "cables_dctires", "cables_actires", "cables_terretires", "interconnexion", "nombre_panneaux", "nombre_rail", "problems"]
    avancement_col_widths = [0.6*inch, 0.5*inch, 0.9*inch, 0.6*inch, 0.8*inch, 0.8*inch, 0.4*inch, 0.4*inch, 0.4*inch, 0.4*inch, 0.8*inch, 0.5*inch, 0.5*inch, 1.3*inch, 0.2*inch]
    build_section_table("Avancement du Chantier", avancement_headers, avancement_rows, avancement_attrs, avancement_col_widths)

    # Fin Table
    fin_headers = ["Date Entrée", "User", "Nom Chantier", "Zone", "String", "Tension DC", "Courant DC", "Tension AC", "Puissance", "Date Mesure", "Technicien", "Statut", "Img"]
    fin_attrs = ["date", "utilisateur", "nom_du_chantier", "fin_zone", "fin_string", "fin_tension_dc", "fin_courant_dc", "fin_tension_ac", "fin_puissance", "fin_date", "fin_technicien", "fin_status"]
    fin_col_widths = [0.7*inch, 0.6*inch, 1.1*inch, 0.7*inch, 0.7*inch, 0.7*inch, 0.7*inch, 0.7*inch, 0.7*inch, 0.7*inch, 0.8*inch, 0.8*inch, 0.2*inch]
    build_section_table("Fin du Chantier", fin_headers, fin_rows, fin_attrs, fin_col_widths)
    
    if not elements:
        elements.append(Paragraph("Aucune donnée à afficher pour les filtres sélectionnés.", styles['Normal']))

    doc.build(elements)
    pdf_buffer.seek(0)
    pdf_download_filename = f"historique_suivi_{datetime.now().strftime('%Y%m%d')}.pdf"
    return send_file(pdf_buffer, mimetype='application/pdf', as_attachment=True, download_name=pdf_download_filename)


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
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 10000)), debug=True)
