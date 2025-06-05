import os
import csv
from flask import Flask, render_template, request, redirect, url_for, flash, Response, send_file, session, abort
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_bcrypt import Bcrypt
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import distinct, desc
from io import StringIO, BytesIO
from datetime import datetime
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
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

# --- !!! HARDCODED DATABASE URI - NOT RECOMMENDED FOR PRODUCTION !!! ---
YOUR_DATABASE_LINK = "postgresql://tsb_jilz_user:WQuuirqxSdknwZjsvldYzD0DbhcOBzQ7@dpg-d0jjegmmcj7s73836lp0-a/tsb_jilz"
app.config['SQLALCHEMY_DATABASE_URI'] = YOUR_DATABASE_LINK
app.logger.info(f"INFO: Using HARDCODED DATABASE_URL: {app.config['SQLALCHEMY_DATABASE_URI']}")
# --- END OF HARDCODED DATABASE URI ---

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
    nom_du_chantier = db.Column(db.String(255), nullable=True, index=True) # Added index for faster lookups

    chantier_type = db.Column(db.String(50), nullable=True)
    interconnexion = db.Column(db.String(255), nullable=True)
    nombre_panneaux = db.Column(db.Integer, nullable=True)
    nombre_rail = db.Column(db.Integer, nullable=True)

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
    onduleur_nombre = db.Column(db.Integer, nullable=True)

    equipe = db.Column(db.String(255), nullable=True)
    onduleur_details_avancement = db.Column(db.Text, nullable=True)
    heure_de_travail = db.Column(db.String(50), nullable=True)

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
    
    images = db.relationship('VinishSuiviImage', backref='suivi_entry', lazy=True, cascade="all, delete-orphan")

class VinishSuiviImage(db.Model):
    __tablename__ = 'vinish_database_image'
    id = db.Column(db.Integer, primary_key=True)
    suivi_entry_id = db.Column(db.Integer, db.ForeignKey('vinish_database.id'), nullable=False)
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
    base_query = VinishSuivi.query
    if current_user.role != "admin":
        base_query = base_query.filter(VinishSuivi.utilisateur == current_user.id)

    filter_utilisateur_req = request.args.get('filter_utilisateur')
    filter_nom_chantier_req = request.args.get('filter_nom_chantier')
    active_tab_from_url = request.args.get('active_tab', 'reception')

    if filter_utilisateur_req:
        if current_user.role == "admin": # Admin can filter by any user
            base_query = base_query.filter(VinishSuivi.utilisateur == filter_utilisateur_req)
    
    if filter_nom_chantier_req:
        base_query = base_query.filter(VinishSuivi.nom_du_chantier == filter_nom_chantier_req)

    all_lignes = base_query.order_by(desc(VinishSuivi.date)).all() # Use desc() for SQLAlchemy

    distinct_users = []
    distinct_nom_chantiers = []
    if current_user.role == "admin":
        distinct_users_query = db.session.query(distinct(VinishSuivi.utilisateur)).order_by(VinishSuivi.utilisateur).all()
        distinct_users = [user[0] for user in distinct_users_query if user[0]]
        
        distinct_nom_chantiers_query = db.session.query(distinct(VinishSuivi.nom_du_chantier))\
            .filter(VinishSuivi.nom_du_chantier.isnot(None), VinishSuivi.nom_du_chantier != '')\
            .order_by(VinishSuivi.nom_du_chantier).all()
        distinct_nom_chantiers = [name[0] for name in distinct_nom_chantiers_query if name[0]]
    else: # For regular users, show only their own distinct chantiers
        user_has_entries = VinishSuivi.query.filter_by(utilisateur=current_user.id).first()
        if user_has_entries:
            distinct_users = [current_user.id] # Only self for filtering if non-admin

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
    active_tab_after_submit = "reception" # Default
    try:
        form_data = request.form.to_dict()
        section = form_data.get("section")
        submitted_nom_chantier = form_data.get("nom_du_chantier")

        entry = None
        is_reception_section = section in ["equipements", "connecteur", "chemin_cable", "terre", "cable_ac", "cable_dc", "onduleur_nombre", "shelter_nombre_reception"]

        if not submitted_nom_chantier and is_reception_section:
            flash("Erreur: Nom du chantier manquant pour la section Réception. Veuillez commencer par l'onglet Équipements et saisir un nom de chantier.", "danger")
            return redirect(url_for('index', active_tab='reception'))
        
        if not submitted_nom_chantier and (section == "avancement" or section == "fin"):
            flash(f"Erreur: Nom du chantier manquant pour la section {section.capitalize()}. Veuillez saisir un nom de chantier.", "danger")
            return redirect(url_for('index', active_tab=section))


        if submitted_nom_chantier:
            # Try to find an existing entry for this user and chantier name
            base_query = VinishSuivi.query.filter_by(
                utilisateur=current_user.id,
                nom_du_chantier=submitted_nom_chantier
            )
            entry = base_query.order_by(desc(VinishSuivi.id)).first()


        if not entry: # If no entry found at all for this nom_chantier, create a new one
            entry = VinishSuivi(
                utilisateur=current_user.id,
                date=datetime.now().strftime('%Y-%m-%d %H:%M'),
                nom_du_chantier=submitted_nom_chantier,
                chantier_type=session.get('chantier_type')
            )
            db.session.add(entry)
            db.session.flush() # Get ID for new entry if it's new
        else:
            # If updating an existing entry, ensure chantier_type from session is used
            # (though it should ideally be consistent for a given chantier entry)
            entry.chantier_type = session.get('chantier_type', entry.chantier_type)
            # Update the date to reflect the latest modification
            entry.date = datetime.now().strftime('%Y-%m-%d %H:%M')


        # Update fields based on the submitted section
        if section == "equipements":
            active_tab_after_submit = "reception"
            entry.equipement_type = form_data.get("equipement_type_1")
            entry.equipement_reference = form_data.get("equipement_reference_1")
            entry.equipement_etat = form_data.get("equipement_etat_1")
            entry.equipement_date_reception = form_data.get("equipement_date_reception_1")
            entry.equipement_nombre_1 = form_data.get("equipement_nombre_1")
            entry.equipement_nombre_2 = form_data.get("equipement_nombre_2")
            entry.equipement_nombre_3 = form_data.get("equipement_nombre_3")
            
            # Potentially clear old images if updating this section for an existing entry
            # For simplicity, this example always adds. For "update" behavior, you might delete existing images first.
            # Example: VinishSuiviImage.query.filter_by(suivi_entry_id=entry.id).delete()
            
            photos = request.files.getlist('photo_chantier[]')
            for photo in photos:
                if photo and photo.filename:
                    img = VinishSuiviImage(suivi_entry_id=entry.id, filename=photo.filename, content_type=photo.content_type, data=photo.read())
                    db.session.add(img)

        elif section == "connecteur":
            active_tab_after_submit = "reception"
            entry.connecteur_type = form_data.get("connecteur_type")
            entry.connecteur_quantite = form_data.get("connecteur_quantite")
            entry.connecteur_etat = form_data.get("connecteur_etat")

        elif section == "chemin_cable":
            active_tab_after_submit = "reception"
            entry.chemin_cable_type = form_data.get("chemin_cable_type")
            entry.chemin_cable_longueur = form_data.get("chemin_cable_longueur")
            entry.chemin_cable_section = form_data.get("chemin_cable_section")
            entry.chemin_cable_profondeur = form_data.get("chemin_cable_profondeur")
        
        elif section == "terre":
            active_tab_after_submit = "reception"
            entry.terre_longueur = form_data.get("terre_longueur")

        elif section == "cable_ac":
            active_tab_after_submit = "reception"
            entry.cableac_section = form_data.get("cableac_section")
            entry.cableac_longueur = form_data.get("cableac_longueur")

        elif section == "cable_dc":
            active_tab_after_submit = "reception"
            entry.cabledc_section = form_data.get("cabledc_section")
            entry.cabledc_longueur = form_data.get("cabledc_longueur")

        elif section == "onduleur_nombre":
            active_tab_after_submit = "reception"
            onduleur_val = form_data.get("onduleur_nombre")
            entry.onduleur_nombre = int(onduleur_val) if onduleur_val and onduleur_val.strip() else None
            
        elif section == "shelter_nombre_reception":
            active_tab_after_submit = "reception"
            shelter_val = form_data.get("shelter_nombre")
            entry.shelter_nombre = int(shelter_val) if shelter_val and shelter_val.strip() else None

        elif section == "avancement":
            active_tab_after_submit = "avancement"
            entry.cables_dctires = form_data.get("cables_dctires")
            entry.cables_actires = form_data.get("cables_actires")
            entry.cables_terretires = form_data.get("cables_terretires")
            entry.equipe = form_data.get("equipe_avancement")
            entry.onduleur_details_avancement = form_data.get("onduleur_avancement")
            entry.heure_de_travail = form_data.get("heure_travail_avancement")
            entry.problems = form_data.get("problems")
            
            current_chantier_type = entry.chantier_type
            if current_chantier_type in ['centrale-sol', 'ombriere']:
                entry.interconnexion = form_data.get("interconnexion")
            elif current_chantier_type == 'toiture':
                nb_panneaux_val = form_data.get("nombre_panneaux")
                entry.nombre_panneaux = int(nb_panneaux_val) if nb_panneaux_val and nb_panneaux_val.strip() else None
                nb_rail_val = form_data.get("nombre_rail")
                entry.nombre_rail = int(nb_rail_val) if nb_rail_val and nb_rail_val.strip() else None
        
        elif section == "fin":
            active_tab_after_submit = "fin"
            # Note: This only saves the first row from the "fin" table in HTML.
            # For multiple "fin" entries, a different data model (e.g., one-to-many) would be needed.
            entry.fin_zone = request.form.getlist("fin_zone[]")[0] if request.form.getlist("fin_zone[]") and request.form.getlist("fin_zone[]")[0] else None
            entry.fin_string = request.form.getlist("fin_string[]")[0] if request.form.getlist("fin_string[]") and request.form.getlist("fin_string[]")[0] else None
            entry.fin_tension_dc = request.form.getlist("fin_tension_dc[]")[0] if request.form.getlist("fin_tension_dc[]") and request.form.getlist("fin_tension_dc[]")[0] else None
            entry.fin_courant_dc = request.form.getlist("fin_courant_dc[]")[0] if request.form.getlist("fin_courant_dc[]") and request.form.getlist("fin_courant_dc[]")[0] else None
            entry.fin_tension_ac = request.form.getlist("fin_tension_ac[]")[0] if request.form.getlist("fin_tension_ac[]") and request.form.getlist("fin_tension_ac[]")[0] else None
            entry.fin_puissance = request.form.getlist("fin_puissance[]")[0] if request.form.getlist("fin_puissance[]") and request.form.getlist("fin_puissance[]")[0] else None
            entry.fin_date = request.form.getlist("fin_date[]")[0] if request.form.getlist("fin_date[]") and request.form.getlist("fin_date[]")[0] else None
            entry.fin_technicien = request.form.getlist("fin_technicien[]")[0] if request.form.getlist("fin_technicien[]") and request.form.getlist("fin_technicien[]")[0] else None
            entry.fin_status = request.form.getlist("fin_status[]")[0] if request.form.getlist("fin_status[]") and request.form.getlist("fin_status[]")[0] else None

        db.session.commit()
        flash("Entrée enregistrée/mise à jour avec succès.", "success")

    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error in suivi_journalier: {str(e)}", exc_info=True) # Log full traceback
        flash(f"❌ Erreur Serveur lors de l'enregistrement: {str(e)}", "danger")
    
    return redirect(url_for('index', active_tab=active_tab_after_submit, 
                            filter_nom_chantier=submitted_nom_chantier if submitted_nom_chantier else request.args.get('filter_nom_chantier') ))


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
                    if col_name in ['id', 'date', 'utilisateur']: # 'chantier_type' could be modifiable
                        continue
                    
                    value = request.form.get(col_name)
                    if col_name in ["shelter_nombre", "nombre_panneaux", "nombre_rail", "onduleur_nombre"]:
                        value = int(value) if value and value.strip() else None
                    
                    # For other fields, ensure empty strings become None if appropriate for your DB schema
                    if isinstance(getattr(entry, col_name), (int, float)) and (value == "" or value is None):
                        value = None
                    elif value == "": # For string fields, decide if empty string is okay or should be None
                        pass # Or value = None if empty string should be null

                    setattr(entry, col_name, value)
            
            # This is now handled by the loop above if chantier_type is in the form
            # if 'chantier_type' in request.form:
            #    entry.chantier_type = request.form.get('chantier_type')

            # Update date on modification
            entry.date = datetime.now().strftime('%Y-%m-%d %H:%M')

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
            return redirect(url_for('index', active_tab='history', filter_nom_chantier=entry.nom_du_chantier))
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Error modifying history entry {entry_id}: {str(e)}", exc_info=True)
            flash(f"Erreur lors de la modification : {str(e)}", "danger")
            
    # Pass the entry to the template for GET request
    return render_template('modify_history.html', entry=entry, current_user=current_user)


@app.route('/delete-history/<int:entry_id>', methods=['POST'])
@login_required
def delete_history(entry_id):
    # Only admin can delete for now, adjust if needed
    if current_user.role != "admin":
        flash("Accès refusé : Administrateur seulement.", "danger")
        return redirect(url_for('index', active_tab='history'))
    try:
        entry_to_delete = VinishSuivi.query.get_or_404(entry_id)
        # Storing nom_chantier before deletion for redirect
        nom_chantier_filter = entry_to_delete.nom_du_chantier 
        db.session.delete(entry_to_delete)
        db.session.commit()
        flash("Entrée supprimée avec succès.", "success")
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error deleting history entry {entry_id}: {str(e)}", exc_info=True)
        flash(f"Erreur lors de la suppression de l'entrée: {str(e)}", "danger")
    return redirect(url_for('index', active_tab='history', filter_nom_chantier=nom_chantier_filter))


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
    elif filter_utilisateur_req: # Admin filtering by user
        base_query = base_query.filter(VinishSuivi.utilisateur == filter_utilisateur_req)
    
    if filter_nom_chantier_req:
        base_query = base_query.filter(VinishSuivi.nom_du_chantier == filter_nom_chantier_req)
        
    return base_query.order_by(desc(VinishSuivi.date)).all() # Use desc() for SQLAlchemy


@app.route('/telecharger-historique')
@login_required
def telecharger_historique():
    rows = _get_filtered_rows()
    fieldnames = [col.name for col in VinishSuivi.__table__.columns if col.name not in ['id']] + ['images_filenames']
    
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
    filename_parts = [current_user.id if current_user.role != "admin" else "admin"]
    filter_utilisateur_req = request.args.get('filter_utilisateur')
    filter_nom_chantier_req = request.args.get('filter_nom_chantier')
    if filter_utilisateur_req:
        filename_parts.append(f"user_{filter_utilisateur_req.replace(' ','_')}")
    if filter_nom_chantier_req:
        filename_parts.append(f"chantier_{filter_nom_chantier_req.replace(' ','_')}")
    filename_parts.append("historique_suivi.csv")
    download_filename = "_".join(filename_parts)

    return Response(
        csv_buffer.getvalue(),
        mimetype='text/csv',
        headers={"Content-Disposition": f"attachment;filename={download_filename}"}
    )


@app.route('/telecharger-historique-pdf')
@login_required
def telecharger_historique_pdf():
    if current_user.role != "admin":
        flash("Accès refusé. Le PDF global est pour les administrateurs.", "danger")
        return redirect(url_for('index', active_tab='history'))

    rows = _get_filtered_rows()
    
    pdf_buffer = BytesIO()
    doc = SimpleDocTemplate(pdf_buffer, pagesize=landscape(letter), topMargin=0.4*inch, bottomMargin=0.4*inch, leftMargin=0.05*inch, rightMargin=0.05*inch)
    elements = []
    styles = getSampleStyleSheet()
    
    small_body_style = ParagraphStyle('smallBodyText', parent=styles['Normal'], fontSize=3.5) 
    small_bold_style = ParagraphStyle('smallBoldText', parent=styles['Normal'], fontSize=3.5, fontName='Helvetica-Bold')

    title_style = styles['h1']
    title_style.alignment = 1 # Center alignment for ReportLab
    filter_utilisateur_req = request.args.get('filter_utilisateur')
    filter_nom_chantier_req = request.args.get('filter_nom_chantier')
    title_text = "Historique des Suivi Journaliers"
    if filter_utilisateur_req or filter_nom_chantier_req:
        title_text += " (Filtré)"
        if filter_utilisateur_req: title_text += f" - Utilisateur: {filter_utilisateur_req}"
        if filter_nom_chantier_req: title_text += f" - Chantier: {filter_nom_chantier_req}"
    elements.append(Paragraph(title_text, title_style))
    elements.append(Spacer(1, 0.15*inch))

    pdf_fieldnames = [ # These are keys for the pdf_headers and for mapping to model attributes
        "date", "util", "nom_chantier", "type_chantier",
        "equipe", "onduleur_avanc", "heure_travail", 
        "equip_type", "equip_ref", "equip_etat", "date_recept_equip", "nb_equip_1",
        "conn_type", "conn_qte", "conn_etat",
        "ch_cable_type", "ch_cable_long", "ch_cable_sect", "ch_cable_prof",
        "terre_long", "ac_sect", "ac_long", "dc_sect", "dc_long",
        "nb_onduleur_recept", "nb_shelter_recept",
        "cables_dc", "cables_ac", "cables_terre",
        "interconnexion", "nb_panneaux", "nb_rail",
        "problems", 
        "fin_zone", "fin_string", "fin_tension_dc", "fin_courant_dc", "fin_tension_ac", "fin_puissance", "fin_date_mesure", "fin_tech", "fin_stat",
        "img_count"
    ]
    
    pdf_headers = { # Display names for headers
        "date": "Date", "util": "Util.", "nom_chantier": "Nom Chant.", "type_chantier": "Type C.",
        "equipe": "Équipe", "onduleur_avanc": "Ondul.(Av)", "heure_travail": "H Trav.", 
        "equip_type": "Type Éq.", "equip_ref": "Réf. Éq.", "equip_etat": "État Éq.", "date_recept_equip": "Dt Réc.Éq", "nb_equip_1": "Nb Éq.1",
        "conn_type": "Type Conn.", "conn_qte": "Qté Conn.", "conn_etat": "État Conn.",
        "ch_cable_type": "Typ Ch.Cbl", "ch_cable_long": "Lg Ch.Cbl", "ch_cable_sect": "Sec Ch.Cbl", "ch_cable_prof": "Pr Ch.Cbl",
        "terre_long": "Lg Terre", "ac_sect": "Sec.AC", "ac_long": "Lg.AC", "dc_sect": "Sec.DC", "dc_long": "Lg.DC",
        "nb_onduleur_recept": "Nb Ond.(R)", "nb_shelter_recept": "Nb Shel.(R)",
        "cables_dc": "DC Tiré", "cables_ac": "AC Tiré", "cables_terre": "Terre T.",
        "interconnexion": "Interco.", "nb_panneaux": "Nb Pan.", "nb_rail": "Nb Rail",
        "problems": "Problèmes", 
        "fin_zone": "Zone Fin", "fin_string": "Str Fin", "fin_tension_dc": "VDC Fin", "fin_courant_dc": "ADC Fin", "fin_tension_ac": "VAC Fin", "fin_puissance": "W Fin", "fin_date_mesure": "Dt Mes.Fin", "fin_tech": "Tech.Fin", "fin_stat": "Stat.Fin",
        "img_count": "Imgs"
    }

    header_paragraphs = [Paragraph(f"<b>{pdf_headers.get(fn, fn.replace('_', ' ').title())}</b>", small_bold_style) for fn in pdf_fieldnames]
    data_for_table = [header_paragraphs]

    # Attribute mapping from pdf_fieldnames (keys) to VinishSuivi model attributes (values)
    attr_map = {
        "util": "utilisateur", "nom_chantier": "nom_du_chantier", "type_chantier": "chantier_type",
        "onduleur_avanc": "onduleur_details_avancement", "heure_travail": "heure_de_travail",
        "equip_type": "equipement_type", "equip_ref": "equipement_reference", "equip_etat": "equipement_etat", "date_recept_equip": "equipement_date_reception", "nb_equip_1": "equipement_nombre_1",
        "conn_type": "connecteur_type", "conn_qte": "connecteur_quantite", "conn_etat": "connecteur_etat",
        "ch_cable_type": "chemin_cable_type", "ch_cable_long": "chemin_cable_longueur", "ch_cable_sect": "chemin_cable_section", "ch_cable_prof": "chemin_cable_profondeur",
        "terre_long": "terre_longueur", "ac_sect": "cableac_section", "ac_long": "cableac_longueur", "dc_sect": "cabledc_section", "dc_long": "cabledc_longueur",
        "nb_onduleur_recept": "onduleur_nombre", "nb_shelter_recept": "shelter_nombre",
        "cables_dc": "cables_dctires", "cables_ac": "cables_actires", "cables_terre": "cables_terretires",
        "nb_panneaux": "nombre_panneaux", "nb_rail": "nombre_rail",
        "fin_zone": "fin_zone", "fin_string": "fin_string", "fin_tension_dc": "fin_tension_dc", "fin_courant_dc": "fin_courant_dc", "fin_tension_ac": "fin_tension_ac", "fin_puissance": "fin_puissance", "fin_date_mesure": "fin_date", "fin_tech": "fin_technicien", "fin_stat": "fin_status",
        # direct match fields: date, equipe, interconnexion, problems
    }

    for row in rows:
        row_data_paragraphs = []
        for field_key in pdf_fieldnames:
            cell_content_str = ""
            actual_attr = attr_map.get(field_key, field_key) # Get mapped attribute or use key itself

            if field_key == 'img_count': 
                cell_content_str = str(len(row.images))
            elif actual_attr and hasattr(row, actual_attr):
                 val = getattr(row, actual_attr, None)
                 # Conditional display for specific chantier_types
                 if field_key == 'interconnexion' and row.chantier_type not in ['centrale-sol', 'ombriere']: val = '-'
                 elif (field_key == 'nb_panneaux' or field_key == 'nb_rail') and row.chantier_type != 'toiture': val = '-'
                 
                 cell_content_str = str(val) if val is not None and val != '-' else (val if val == '-' else "")
            
            max_len = 10 # Truncate long strings for PDF
            if len(cell_content_str) > max_len:
                cell_content_str = cell_content_str[:max_len-3] + "..."
            row_data_paragraphs.append(Paragraph(cell_content_str, small_body_style))
        data_for_table.append(row_data_paragraphs)

    if len(data_for_table) > 1: # If there's data
        # Adjust colWidths based on the number of fields in pdf_fieldnames
        num_cols = len(pdf_fieldnames)
        # Basic even distribution, adjust as needed for better layout
        avg_width = (landscape(letter)[0] - 0.1*inch) / num_cols 
        col_widths = [avg_width] * num_cols
        # Example of more specific widths if you want to fine-tune:
        # col_widths = [0.5*inch, 0.35*inch, ...] 

        table = Table(data_for_table, colWidths=col_widths, repeatRows=1)
        table_style = TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.darkslategray), ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'), ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'), ('FONTSIZE', (0, 0), (-1, 0), 3.5), # Adjusted font size
            ('BOTTOMPADDING', (0, 0), (-1, 0), 1), ('TOPPADDING', (0, 0), (-1, 0), 1),
            ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey), ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('FONTSIZE', (0, 1), (-1, -1), 3.5), # Adjusted font size
            ('GRID', (0, 0), (-1, -1), 0.25, colors.black), # Thinner grid
            ('LEFTPADDING', (0,0), (-1,-1), 1), ('RIGHTPADDING', (0,0), (-1,-1), 1),
            ('TOPPADDING', (0,1), (-1,-1), 1), ('BOTTOMPADDING', (0,1), (-1,-1), 1),
        ])
        table.setStyle(table_style)
        elements.append(table)
    else:
        elements.append(Paragraph("Aucune donnée à afficher pour les filtres sélectionnés.", styles['Normal']))

    doc.build(elements)
    pdf_buffer.seek(0)
    filename_parts_pdf = ["historique_suivi"]
    if filter_utilisateur_req: filename_parts_pdf.append(f"user_{filter_utilisateur_req.replace(' ','_')}")
    if filter_nom_chantier_req: filename_parts_pdf.append(f"chantier_{filter_nom_chantier_req.replace(' ','_')}")
    filename_parts_pdf.append(".pdf")
    pdf_download_filename = "_".join(filename_parts_pdf)

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
        role = request.form.get('role', 'user') # Default to 'user' if not provided

        if not username: # Basic validation
            flash("❌ Nom d'utilisateur requis.", "danger")
            return redirect(url_for('admin_panel'))

        if action == "add":
            if not password:
                flash("❌ Mot de passe requis pour ajouter un utilisateur.", "danger")
                return redirect(url_for('admin_panel'))
            if not DBUser.query.filter_by(id=username).first():
                hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
                new_user = DBUser(id=username, password_hash=hashed_password, role=role)
                db.session.add(new_user)
                db.session.commit()
                flash(f"✅ Utilisateur '{username}' ajouté avec le rôle '{role}'.", "success")
            else:
                flash(f"L'utilisateur '{username}' existe déjà.", "warning")
        elif action == "delete":
            if username == "admin": # Prevent deleting the main admin
                flash("❌ Impossible de supprimer l'utilisateur 'admin'.", "danger")
            else:
                user_to_delete = DBUser.query.filter_by(id=username).first()
                if user_to_delete:
                    db.session.delete(user_to_delete)
                    db.session.commit()
                    flash(f"🗑️ Utilisateur '{username}' supprimé.", "success")
                else:
                    flash(f"Utilisateur '{username}' non trouvé.", "warning")
        elif action == "update_role": # Optional: Add role update functionality
            user_to_update = DBUser.query.filter_by(id=username).first()
            if user_to_update:
                if user_to_update.id == "admin" and role != "admin":
                     flash("❌ Le rôle de l'utilisateur 'admin' ne peut pas être changé.", "danger")
                else:
                    user_to_update.role = role
                    db.session.commit()
                    flash(f"🔄 Rôle de l'utilisateur '{username}' mis à jour à '{role}'.", "success")
            else:
                flash(f"Utilisateur '{username}' non trouvé pour la mise à jour du rôle.", "warning")

        else:
            flash("❌ Action invalide ou champs manquants.", "danger")
        return redirect(url_for('admin_panel'))

    users = DBUser.query.all()
    return render_template('admin.html', utilisateurs=users, current_user=current_user)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 10000)), debug=False)
