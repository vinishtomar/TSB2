import os
import csv
from flask import Flask, render_template, request, redirect, url_for, flash, Response, send_file, session, abort
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_bcrypt import Bcrypt
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import distinct
from io import StringIO, BytesIO
from datetime import datetime
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.    __tablename__ = 'new_suivi_journalier'
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.String(50), default=lambda: datetime.now().strftime('%Y-%m-%d %H:%M'))
    utilisateur = db.Column(db.String(255))
    nom_du_chantier = db.Column(db.String(255), nullable=True)

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

    # New fields for Avancement du Chantier
    equipe = db.Column(db.String(255), nullable=True)
    onduleur_details_avancement = db.Column(db.Text, nullable=True)
    heure_de_travail = db.Column(db.String(50), nullable=True)

    cables_dctires = db.Column(db.String(255), nullable=True)
    cables_actires = db.Column(db.String(255), nullable=True)
    cables_terretires = db.Column(db.String(255), nullable=True)
    problems = dblib.styles import getSampleStyleSheet, ParagraphStyle
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

    chantier_type = db.Column(db.String(50), nullable=True)
    interconnexion = db.Column(db.String(255), nullable=True)
    nombre_panneaux = db.Column(db.Integer, nullable=True)
    nombre_rail = db.Column(db.Integer, nullable=True)

    equipement_type = db.Column(db.String(255), nullable=True)
    equipement_reference = db.Column(db.String(255), nullable=True)
    equipement_etat = db.Column(db.String(.Column(db.Text, nullable=True)

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
    if not255), nullable=True)
    equipement_date_reception = db.Column(db.String(255), nullable=True)
    equipement_nombre_1 = db.Column(db.String(10), nullable=True)
    equipement_nombre_2 = db.Column(db.String(10), nullable=True)
    equipement_nombre_3 = db.Column(db.String(10), nullable=True)
    connecteur_type = db.Column(db.String(255), nullable=True)
    connecteur_quantite = db.Column(db.String(255), nullable=True)
    connecteur_etat = db.Column(db.String(255), nullable=True)
    chemin_cable_longueur = db.Column(db.String(255), nullable=True)
    chemin_cable_type = db.Column(db.String DBUser.query.filter_by(id="admin").first():
        hashed_password = bcrypt.generate_password_hash("admin").decode('utf-8')
        admin_user = DBUser(id="admin", password_hash=hashed_password, role="admin")
        db.session.add(admin_user)
        db.session.commit()
        app.logger.info("Default admin user created.")

with app.app_context():
    db.create_all()
    create_admin_user_if_(255), nullable=True)
    chemin_cable_section = db.Column(db.String(255), nullable=True)
    chemin_cable_profondeur = db.Column(db.String(255), nullable=True)
    terre_longueur = db.Column(db.String(255), nullable=True)
    cableac_section = db.Column(db.String(255), nullable=True)
    cableac_longueur = db.Column(db.String(255), nullable=True)
    cabledc_section = db.Column(db.String(255), nullable=True)
    cabledc_longueur = db.Column(db.String(255), nullable=True)
    shelter_nombre = db.Column(db.Integer, nullable=True) 
    onduleur_nombre = db.Column(db.Integer, nullable=True)not_exists()

@app.route('/')
@login_required
def index():
    base_query = SuiviJournalier.query
    if current_user.role != "admin":
        base_query = base_query.filter(SuiviJournalier.utilisateur == current_user.id)

    filter_utilisateur_req = request.args.get('filter_utilisateur')
    filter_nom_chantier_req = request.args.get('filter_nom_chantier')
    active_tab_from_url = 

    # START: New fields for Avancement du Chantier
    equipe = db.Column(db.String(255), nullable=True)
    onduleur_details_avancement = db.Column(db.Text, nullable=True) 
    heure_de_travail = db.Column(db.String(50), nullable=True)
    # END: New fields for Avancement du Chantier

    cables request.args.get('active_tab', 'reception')

    if filter_utilisateur_req:
        if current_user.role == "admin":
            base_query = base_query.filter(SuiviJournalier.utilisateur == filter_utilisateur_req)
    if filter_nom_chantier_req:
        base_query = base_query.filter(SuiviJournalier.nom_du_chantier == filter_nom_chantier_req)

    all_lignes = base_query.order_by(SuiviJournalier.date.desc()).all()

    distinct_users = []
    distinct_nom_chantiers = []
    if current_user.role == "admin":
        distinct_users_query_dctires = db.Column(db.String(255), nullable=True)
    cables_actires = db.Column(db.String(255), nullable=True)
    cables = db.session.query(distinct(SuiviJournalier.utilisateur)).order_by(SuiviJournalier.utilisateur).all()
        distinct_users = [user[0] for user in distinct_users_query if user[0]]
        distinct_nom_chantiers_query = db.session.query(distinct_terretires = db.Column(db.String(255), nullable=True)
    problems = db.Column(db.Text, nullable=True)

    fin_zone = db.Column(db.String(255), nullable=True)
    fin_string = db.Column(db.String(255), nullable=True)
    fin_tension_dc = db.Column(db.String(255), nullable=True)
    fin_courant_dc = db.Column(db.(SuiviJournalier.nom_du_chantier))\
            .filter(SuiviJournalier.nom_du_chantier.isnot(None), SuiviJournalier.nom_du_chantier != '')\
            .order_by(SuiviJournalier.nom_du_chantier).all()
        String(255), nullable=True)
    fin_tension_ac = db.Column(db.String(255), nullable=True)
    fin_puissance = db.Column(db.String(255), nullable=True)
    fin_date = db.Column(db.String(2distinct_nom_chantiers = [name[0] for name in distinct_nom_chantiers_query if name[0]]
    else:
        user_has_entries = SuiviJournalier.query55), nullable=True)
    fin_technicien = db.Column(db.String(255), nullable=True)
    fin_status = db.Column(db.String(255.filter_by(utilisateur=current_user.id).first()
        if user_has_entries:
            distinct_users = [current_user.id]
        distinct_nom_chantiers_user), nullable=True)
    images = db.relationship('SuiviJournalierImage', backref='suivi', lazy=True, cascade="all, delete-orphan")

class SuiviJournalierImage(db.Model):
    __tablename__ = 'new_suivi_journalier_image'
    id = db._query = db.session.query(distinct(SuiviJournalier.nom_du_chantier))\
            .filter(SuiviJournalier.utilisateur == current_user.id)\
            .filter(SuiviColumn(db.Integer, primary_key=True)
    suivi_id = db.Column(dbJournalier.nom_du_chantier.isnot(None), SuiviJournalier.nom_du_chantier != '')\
            .order_by(SuiviJournalier.nom_du_chantier)..Integer, db.ForeignKey('new_suivi_journalier.id'), nullable=False)
    filenameall()
        distinct_nom_chantiers = [name[0] for name in distinct_nom_ = db.Column(db.String(255), nullable=False)
    content_type = dbchantiers_user_query if name[0]]

    return render_template('index.html',
                           all_.Column(db.String(255), nullable=False)
    data = db.Column(db.LargeBinary, nullable=False)

def create_admin_user_if_not_exists():
    lignes=all_lignes,
                           current_user=current_user,
                           session=session,
                           distinct_users=distinct_users,
                           distinct_nom_chantiers=distinct_nom_if not DBUser.query.filter_by(id="admin").first():
        hashed_password = bcrypt.generate_password_hash("admin").decode('utf-8')
        admin_user = DBUser(id="adminchantiers,
                           current_filter_utilisateur=filter_utilisateur_req,
                           current_filter_nom_chantier=filter_nom_chantier_req,
                           active_tab=active_tab_", password_hash=hashed_password, role="admin")
        db.session.add(admin_user)
        db.session.commit()
        app.logger.info("Default admin user created.")

withfrom_url)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    if app.app_context():
    db.create_all()
    create_admin_user_if_not_exists()

@app.route('/')
@login_required
def index():
    base_query request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        chantier_type_from_form = request.form.get('chantier_type')
        user_from_db = DBUser.query.filter_by(id= = SuiviJournalier.query
    if current_user.role != "admin":
        base_query = base_query.filter(SuiviJournalier.utilisateur == current_user.id)

    filter_utilisateur_req = request.args.get('filter_utilisateur')
    filter_nom_chantier_requsername).first()
        if user_from_db and bcrypt.check_password_hash(user_from_db.password_hash, password):
            user_obj = User(user_from_db.id = request.args.get('filter_nom_chantier')
    active_tab_from_url =, user_from_db.role)
            login_user(user_obj)
            session['chantier_type'] = chantier_type_from_form
            return redirect(url_for('index'))
 request.args.get('active_tab', 'reception')

    if filter_utilisateur_req:
        if current_user.role == "admin":
            base_query = base_query.filter(SuiviJournal        else:
            flash("Nom d'utilisateur ou mot de passe incorrect.", "danger")
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():ier.utilisateur == filter_utilisateur_req)
    if filter_nom_chantier_req:
        base_query = base_query.filter(SuiviJournalier.nom_du_chantier == filter_
    session.pop('chantier_type', None)
    logout_user()
    flash("Vousnom_chantier_req)

    all_lignes = base_query.order_by(Suivi avez été déconnecté.", "success")
    return redirect(url_for('login'))

@app.route('/suivi-journalier', methods=['POST'])
@login_required
def suivi_journalier():Journalier.date.desc()).all()

    distinct_users = []
    distinct_nom_chantiers = []
    if current_user.role == "admin":
        distinct_users_query = db
    active_tab_after_submit = "reception"
    try:
        data_to_.session.query(distinct(SuiviJournalier.utilisateur)).order_by(SuiviJournalier.utilisateur).all()
        distinct_users = [user[0] for user in distinct_users_query if usersave = {
            "utilisateur": current_user.id,
            "date": datetime.now().strftime('%Y-%m-%d %H:%M'),
            "chantier_type": session.get('chant[0]]
        distinct_nom_chantiers_query = db.session.query(distinct(Suier_type'),
            "equipement_type": request.form.get("equipement_type_1"),
            iviJournalier.nom_du_chantier))\
            .filter(SuiviJournalier.nom_du"equipement_reference": request.form.get("equipement_reference_1"),
            "equipement_chantier.isnot(None), SuiviJournalier.nom_du_chantier != '')\
_etat": request.form.get("equipement_etat_1"),
            "equipement_date_            .order_by(SuiviJournalier.nom_du_chantier).all()
        distinct_nom_chantiers = [name[0] for name in distinct_nom_chantiers_query ifreception": request.form.get("equipement_date_reception_1"),
            "equipement_nombre_1": request.form.get("equipement_nombre_1"),
            "equipement_ name[0]]
    else:
        user_has_entries = SuiviJournalier.query.filter_by(utilisateur=current_user.id).first()
        if user_has_entries:
            nombre_2": request.form.get("equipement_nombre_2"),
            "equipement_nombre_3": request.form.get("equipement_nombre_3"),
            "connecteur_type":distinct_users = [current_user.id]
        distinct_nom_chantiers_user_query = db.session.query(distinct(SuiviJournalier.nom_du_chantier))\
            . request.form.get("connecteur_type"),
            "connecteur_quantite": request.form.get("connecteur_quantite"),
            "connecteur_etat": request.form.get("connecteurfilter(SuiviJournalier.utilisateur == current_user.id)\
            .filter(SuiviJournalier.nom_du_chantier.isnot(None), SuiviJournalier.nom_du_chantier != '')\
            .order_by(SuiviJournalier.nom_du_chantier).all()_etat"),
            "chemin_cable_longueur": request.form.get("chemin_cable_longueur"),
            "chemin_cable_type": request.form.get("chemin_cable_type"),
            "chemin_cable_section": request.form.get("chemin_cable_section"),
            "chemin_cable_profondeur": request.form.get("chemin_cable_profondeur"),

        distinct_nom_chantiers = [name[0] for name in distinct_nom_chantiers_user_query if name[0]]

    return render_template('index.html',
                           all_lignes=all_lignes,
                           current_user=current_user,
                           session=session,
                           distinct_users=distinct_users,
                           distinct_nom_chantiers=distinct_nom            "terre_longueur": request.form.get("terre_longueur"),
            "cableac_section": request.form.get("cableac_section"),
            "cableac_longueur": request._chantiers,
                           current_filter_utilisateur=filter_utilisateur_req,
                           current_filter_nom_chantier=filter_nom_chantier_req,
                           active_tab=active_tabform.get("cableac_longueur"),
            "cabledc_section": request.form.get("cabledc_section"),
            "cabledc_longueur": request.form.get("c_from_url)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        chantier_type_from_form = request.form.get('chantier_type')
        user_from_db = DBUser.query.filter_by(idabledc_longueur"),
            "shelter_nombre": None, # Will be set if submitted by specific reception forms
            "onduleur_nombre": None, # Will be set if submitted by specific reception forms
            "cables_dctires": request.form.get("cables_dctires"),
            "cables_actires": request.form.get("cables_actires"),
            "cables_terretires": request.form.get("cables_terretires"),
            "problems": request.form.get=username).first()
        if user_from_db and bcrypt.check_password_hash(user_from_db.password_hash, password):
            user_obj = User(user_from_db.id, user_from_db.role)
            login_user(user_obj)
            session['chantier_type'] = chantier_type_from_form
            return redirect(url_for('index'))
        else:
            flash("Nom d'utilisateur ou mot de passe incorrect.", "danger")
    return render("problems"),
        }

        section = request.form.get("section")

        # Handle nom_du_chantier based on which form submitted it
        if request.form.get("nom_du_chantier"):
            data_to_save["nom_du_chantier"] = request.form.get("nom_du_chantier")

        if section in ["equipements", "connecteur", "chemin_cable", "terre", "cable_ac", "cable_dc", "onduleur_nombre", "shelter_template('login.html')

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
    try:
        data_to__nombre_reception"]:
            active_tab_after_submit = "reception"
            if section == "shelter_nombre_reception": # From Reception -> Shelter Nombre tab
                 data_to_save["shelter_nombre"] = request.form.get("shelter_nombre", type=int) if request.form.get("shelter_nombre") else None
            if section == "onduleur_nombre": # From Reception -> Onduleur Nombre tab
                 data_to_save["onduleur_nombre"] = request.form.get("onduleur_nombre", type=int) if request.form.get("onduleur_nombre") else None

        elif section == "avancement":
            active_tab_after_submitsave = {
            "utilisateur": current_user.id,
            "date": datetime.now().strftime('%Y-%m-%d %H:%M'),
            "chantier_type": session.get('chantier_type'),
            "equipement_type": request.form.get("equipement_type_1"),
            "equipement_reference": request.form.get("equipement_reference_1"),
            "equipement_etat": request.form.get("equipement_etat_1"),
            "equipement_date_reception": request.form.get("equipement_date_reception_1"),
            "equipement_nombre_1": request.form.get("equipement_nombre_1"),
            " = "avancement"
            current_chantier_type = session.get('chantier_type')
            if current_chantier_type in ['centrale-sol', 'ombriere']:
                data_to_save["interconnexion"] = request.form.get("interconnexion")
            elif current_chantier_type == 'toiture':
                data_to_save["nombre_panneaux"] = requestequipement_nombre_2": request.form.get("equipement_nombre_2"),
            "equipement_nombre_3": request.form.get("equipement_nombre_3"),
            "connecteur_type": request.form.get("connecteur_type"),
            "connecteur_quantite": request.form.get("connecteur_quantite"),
            "connecteur_etat": request.form.get("connecteur_etat"),
            "chemin_cable_longueur": request.form.get("chemin_cable_longueur"),
            "chemin_cable_type": request.form.get("chemin_cable_.form.get("nombre_panneaux", type=int) if request.form.get("nombre_panneaux") else None
                data_to_save["nombre_rail"] = request.form.get("nombre_rail", type=int) if request.form.get("nombre_rail") else None
            
            data_to_save["equipe"] = request.form.get("equipe_avancement")
            data_to_save["onduleur_details_avancement"] = request.form.get("onduleur_avancement")
            data_to_save["heure_de_travail"] = request.form.type"),
            "chemin_cable_section": request.form.get("chemin_cable_section"),
            "chemin_cable_profondeur": request.form.get("chemin_cable_profondeur"),
            "terre_longueur": request.form.get("terre_longueur"),
            "cableac_section": request.form.get("cableac_section"),
            "cableac_longueur": request.form.get("cableac_longueur"),
            "cabledc_section": request.form.get("cabledc_section"),
            "cabledc_longueur": request.form.get("cabledc_longueur"),
            # Note: shelter_nombre and onduleur_nombre are handledget("heure_travail_avancement")

        elif section == "fin":
            active_tab_after_submit = "fin"
            data_to_save["fin_zone"] = request.form.getlist("fin_zone[]")[0] if request.form.getlist("fin_zone[]") else None
            data_to_save["fin_string"] = request.form.getlist("fin_string[]")[0] if request.form.getlist("fin_string[]") else None
            data_to_save["fin_tension_dc"] = request.form.getlist("fin_tension_dc[]")[0] if request.form.getlist("fin_tension_dc[]") else None
            data_to_save["fin_courant_dc"] = request.form.getlist("fin_courant_dc[]")[0 based on section below
            "cables_dctires": request.form.get("cables_dctires"),
            "cables_actires": request.form.get("cables_actires"),
            "cables_terretires": request.form.get("cables_terretires"),
            "problems": request.form.get("problems"),
        }

        section = request.form.get("section")

        if request.form.get("nom_du_chantier"): # Common field for all data-entry forms
            data_to_save["nom_du_chantier"] = request.form.get("nom_] if request.form.getlist("fin_courant_dc[]") else None
            data_to_save["fin_tension_ac"] = request.form.getlist("fin_tension_ac[]")[0] if request.form.getlist("fin_tension_ac[]") else None
            data_to_save["fin_puissance"] = request.form.getlist("fin_puissance[]")[0] if request.form.getlist("fin_puissance[]") else None
            data_to_save["fin_date"] = request.form.getlist("fin_date[]")[0] if request.form.getlist("fin_date[]") else None
            data_to_save["fin_technicien"] = request.form.getlist("fin_technicien[]")[0] if request.form.getlist("fin_technicien[]") else None
            data_to_save["fin_status"] = request.form.getlist("fin_status[]")[0] if request.form.getlist("fin_status[]") else None

        entry = SuiviJournalier(**data_to_save)
        db.sessiondu_chantier")

        if section in ["equipements", "connecteur", "chemin_cable", "terre", "cable_ac", "cable_dc", "onduleur_nombre", "shelter_nombre_reception"]:
            active_tab_after_submit = "reception"
            if section == "onduleur_nombre": # This is for Reception -> Onduleur Nombre tab
                 data_to_save["onduleur_nombre"] = request.form.get("onduleur_nombre", type=int) if request.form.get("onduleur_nombre") else None
            if section == "shelter_nombre_reception": # This is for Reception -> Shelter Nombre tab
                 data_to_save["shelter_nombre"] = request.form.get("shelter_nombre", type=int) if request.form.get("shelter_nombre") else None

        elif section == "avancement":
            active_tab_after_submit = "av.add(entry)
        db.session.flush()

        if section == "equipements": # Only equipements form has photo upload
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
    
    returnancement"
            current_chantier_type = session.get('chantier_type')
            if current_chantier_type in ['centrale-sol', 'ombriere']:
                data_to_save["interconnexion"] = request.form.get("interconnexion")
            elif current_chantier_type == 'toiture':
                data_to_save["nombre_panneaux"] = request.form. redirect(url_for('index', active_tab=active_tab_after_submit))


@app.route('/modify-history/<int:entry_id>', methods=['GET', 'POST'])
@login_required
def modify_history(entry_id):
    entry = SuiviJournalier.query.get_or_404(entry_id)
    if current_user.role != "admin" and entry.utilisateur != current_user.id:
        flash("Droits insuffisants pour modifier cette entrée.", "danger")
        return redirect(url_for('index', active_tab='history'))

    if request.method == 'POST':
get("nombre_panneaux", type=int) if request.form.get("nombre_panneaux") else None
                data_to_save["nombre_rail"] = request.form.get("nombre_rail", type=int) if request.form.get("nombre_rail") else None
            
            data_to_save["equipe"] = request.form.get("equipe_avancement")
            data_to_save["onduleur_details_avancement"] = request.form.get("onduleur_avancement")
            data_to_save["heure_de_travail"] = request.form.get("heure_travail_avancement")
            # nom_du_chantier for avancement is handled by the common check above

        elif section == "fin":
            active_tab_after_submit = "fin"
            # nom_du_chantier for fin is handled by the common check above
            data_to_save["fin_zone"] = request.form.getlist("fin_zone[]")[0] if        try:
            for column in SuiviJournalier.__table__.columns:
                col_name = column.name
                if col_name in request.form:
                    if col_name in ['id', 'date', 'utilisateur', 'chantier_type']:
                        continue
                    
                    value = request.form. request.form.getlist("fin_zone[]") else None
            data_to_save["fin_string"] = request.form.getlist("fin_string[]")[0] if request.form.getlist("fin_string[]") else None
            data_to_save["fin_tension_dc"] = request.form.getlist("fin_tension_dc[]")[0] if request.form.getlist("fin_tension_dc[]") else None
            data_to_save["fin_courant_dc"] = request.form.getlist("fin_courant_dc[]")[0] if request.form.getlistget(col_name)
                    if col_name in ["shelter_nombre", "nombre_panneaux", "nombre_rail", "onduleur_nombre"]:
                        value = int(value) if value and value.strip() else None
                    setattr(entry, col_name, value)
            
            if entry.chantier_type in ['centrale-sol', 'ombriere']:
                if 'interconnexion' in request.form:
                    entry.interconnexion = request.form.get('interconnexion')
            elif entry.chantier_type == 'toiture':
                if 'nombre_panneaux' in("fin_courant_dc[]") else None
            data_to_save["fin_tension_ac"] = request.form.getlist("fin_tension_ac[]")[0] if request.form.getlist("fin_tension_ac[]") else None
            data_to_save["fin_puissance"] = request.form.getlist("fin_puissance[]")[0] if request.form.getlist("fin_puissance[]") else None
            data_to_save["fin_date"] = request.form.getlist("fin_date[]")[0] if request.form.getlist("fin_date[]") request.form:
                    entry.nombre_panneaux = request.form.get('nombre_panneaux', type=int) if request.form.get('nombre_panneaux') else None
                if 'nombre_rail' in request.form:
                    entry.nombre_rail = request.form.get('nombre_rail', type=int) if request.form.get('nombre_rail') else None

            delete_ids_str = request.form.get('delete_images', '')
            if delete_ids_str:
                delete_ids = [int(img_id) for img_id in delete_ids_str.split(',') if img_id.strip().isdigit()]
                for img_id_to_delete in delete_ids else None
            data_to_save["fin_technicien"] = request.form.getlist("fin_technicien[]")[0] if request.form.getlist("fin_technicien[]") else None
            data_to_save["fin_status"] = request.form.getlist("fin_status[]")[0] if request.form.getlist("fin_status[]") else None

        entry =:
                    img_to_delete = SuiviJournalierImage.query.get(img_id_to_delete)
                    if img_to_delete and img_to_delete.suivi_id == entry.id:
                        db.session.delete(img_to_delete)
            
            photos = request SuiviJournalier(**data_to_save)
        db.session.add(entry)
        db.session.flush()

        if section == "equipements": # Only equipements form has photo upload currently
            photos = request.files.getlist('photo_chantier[]')
            for photo in photos:
                if photo.files.getlist('photo_chantier[]')
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
            return redirect(url_for(' and photo.filename:
                    img = SuiviJournalierImage(
                        suivi_id=entry.id,
                        filename=photo.filename,
                        content_type=photo.content_type,
                        index', active_tab='history'))
        except Exception as e:
            db.session.rollback()
            app.logger.error(f"Error modifying history entry {entry_id}: {str(e)}")
            flash(f"Erreur lors de la modification : {str(e)}", "danger")
            
data=photo.read()
                    )
                    db.session.add(img)
        
        db.session.commit()
        flash("Entrée enregistrée avec succès.", "success")

    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error in suivi_    return render_template('modify_history.html', entry=entry)

@app.route('/delete-history/<int:entry_id>', methods=['POST'])
@login_required
def delete_history(entry_id):
    if current_user.role != "admin":
        flash("Accès refusé :journalier: {str(e)}")
        flash(f"❌ Erreur Serveur lors de l'enregistrement: {str(e)}", "danger")
    
    return redirect(url_for('index', active_tab=active_tab_after_submit))

@app.route('/modify-history/<int:entry Administrateur seulement.", "danger")
        return redirect(url_for('index'))
    try:
        entry_to_delete = SuiviJournalier.query.get_or_404(entry_id)
        db.session.delete(entry_to_delete)
        db.session.commit()_id>', methods=['GET', 'POST'])
@login_required
def modify_history(entry_id):
    entry = SuiviJournalier.query.get_or_404(entry_id)
    if current_user.role != "admin" and entry.utilisateur != current_user.id:
        flash("Droits insuffisants pour modifier cette entrée.", "danger")
        return redirect(url_for('index', active_tab='
        flash("Entrée supprimée avec succès.", "success")
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error deleting history entry {entry_id}: {str(e)}")
        flash(f"Erreur lors de la suppression de l'entrée: {str(e)}", "danger")
    return redirect(url_for('index', active_tab='history'))

@app.route('/image/<int:image_id>')
@login_required
def get_imagehistory'))

    if request.method == 'POST':
        try:
            for column in SuiviJournalier.__table__.columns:
                col_name = column.name
                if col_name in request.form: 
                    if col_name in ['id', 'date', 'utilisateur', 'chantier_type']:
                        continue
                    
                    value = request.form.get(col_name)
                    if col_name in(image_id):
    image = SuiviJournalierImage.query.get_or_404(image_id)
    if current_user.role != 'admin' and (not image.suivi or image.suivi.utilisateur != current_user.id):
        abort(403)
    return send_file(BytesIO(image.data), mimetype=image.content_type)

def _get_filtered_rows():
    base_query = SuiviJournalier.query
    filter_utilisateur_req = request.args.get('filter_utilisateur')
    filter_nom_chantier_req = request.args. ["shelter_nombre", "nombre_panneaux", "nombre_rail", "onduleur_nombre"]:
                        value = int(value) if value and value.strip() else None
                    setattr(entry, col_name, value)
            
            if entry.chantier_type in ['centrale-sol', 'ombriere']:
                if 'interconnexion' in request.form:
                    entry.interconnexion = request.form.get('interconnexion')
            elif entry.chantier_type == 'toiture':
                ifget('filter_nom_chantier')

    if current_user.role != "admin":
        base_query = base_query.filter(SuiviJournalier.utilisateur == current_user.id)
    elif filter_utilisateur_req:
        base_query = base_query.filter(SuiviJournalier.utilisateur == filter_utilisateur_req)
    
    if filter_nom_chantier_req:
        base_query = base_query.filter(SuiviJournalier.nom_du_chantier == filter_nom_chantier_req)
        
    return base_query.order_by(SuiviJournalier 'nombre_panneaux' in request.form:
                    entry.nombre_panneaux = request.form.get('nombre_panneaux', type=int) if request.form.get('nombre_panneaux') else None
                if 'nombre_rail' in request.form:
                    entry.nombre_rail = request.form.get('nombre_rail', type=int) if request.form.get('nombre_rail') else None

            delete_ids_str = request.form.get('delete_images', '')
            if delete_ids_str:
                delete_ids = [int(img_id) for img_id.date.desc()).all()

@app.route('/telecharger-historique')
@login_required
def telecharger_historique():
    rows = _get_filtered_rows()
    fieldnames = [col.name for col in SuiviJournalier.__table__.columns if col.name not in ['id']] + ['images_filenames']
    
    csv_buffer = StringIO()
    writer = csv.writer(csv_buffer, delimiter=';')
    writer.writerow(fieldnames)

    for row in rows:
        row_data = []
        for field in fieldnames:
            if field == 'images_filenames':
                photo_filenames = ";".join([img.filename for img in row.images])
                row_data. in delete_ids_str.split(',') if img_id.strip().isdigit()]
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
                        content_type=append(photo_filenames)
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
    filename_parts.append("historique_suiviphoto.content_type,
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
            
    return render_template('modify_history.html', entry=entry)

@app.route('/delete-history/<int:entry_id>', methods=['POST'])
@login_required
def delete_history(entry_id):
    if current_user.role != "admin":
        flash("Accès refusé : Administrateur seulement.", "danger")
        return redirect(url_for.csv")
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
('index'))
    try:
        entry_to_delete = SuiviJournalier.query.get_or_404(entry_id)
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
    image = SuiviJournalierImage.query.get_or_404(image_id)
    if current_user.role != 'admin' and (not image.suivi or image.suivi.utilisateur != current_user.id):
        abort(403)
    return send_file(BytesIO(image.data), mimetype=image.    small_bold_style = ParagraphStyle('smallBoldText', parent=styles['Normal'], fontSize=3.5, fontName='Helvetica-Bold')

    title_style = styles['h1']
    title_style.alignment = 1
    filter_utilisateur_req = request.args.get('filter_utilisateur')
    filter_nom_chantier_req = request.args.get('filter_nom_chantier')
    title_text = "Historique des Suivi Journaliers"
    if filter_utilisateur_req or filter_nom_chantier_req:
        title_text += " (Filtré)"
        if filter_utilisateur_req: title_text += f" - Utilisateur: {filter_utilisateur_req}"
        if filter_nom_chantier_req: title_text += f" - Chantier: {filter_nom_chantier_req}"
    elements.append(Paragraph(title_text, title_style))
    elements.append(Spacer(1, 0.15*inch))

    pdf_fieldnames = [
        "date", "util", "nom_chantier", "type_chantier",
        "equipe",content_type)

def _get_filtered_rows():
    base_query = SuiviJournalier.query
    filter_utilisateur_req = request.args.get('filter_utilisateur')
    filter_nom_chantier_req = request.args.get('filter_nom_chantier')

    if current_user.role != "admin":
        base_query = base_query.filter(SuiviJournalier.utilisateur == current_user.id)
    elif filter_utilisateur_req:
        base_query = base_query.filter(SuiviJournalier.utilisateur == filter_utilisateur_req)
    
    if filter_nom_chantier_req:
        base_query = base_query.filter(SuiviJournalier.nom_du_chantier == filter_nom_chantier_req)
        
    return base_query.order_by(SuiviJournalier.date.desc()).all()

@app.route('/telecharger-historique')
@login_required
def telecharger_historique():
    rows = _get_filtered_rows()
    fieldnames = [col.name for col in SuiviJournalier.__table__.columns if col.name not in [' "onduleur_avanc", "heure_travail",
        "equip_type", "equip_ref", "equip_etat",
        "cables_dc", "cables_ac", "cables_terre",
        "nb_onduleur_recept", "nb_shelter_recept",
        "interconnexion", "nb_panneaux", "nb_rail",
        "problems", "fin_stat", "img_count"
    ]
    
    pdf_headers = {
        "date": "Date", "util": "Util.", "nom_chantier": "Nom Chant.", "type_chantier": "Type C.",
        "equipe": "Équipe", "onduleur_avanc": "Ondul.(Av)", "heure_travail": "H Trav.",
        "equip_type": "Type Éq.", "equip_ref": "Réf. Éq.", "equip_etat": "État Éq.",
        "cables_dc": "DC Tiré", "cables_ac": "AC Tiré", "cables_terre": "Terre T.",
        "nb_onduleur_recept": "id']] + ['images_filenames']
    
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

@app.route('/telecharger-historNb Ond.(R)", "nb_shelter_recept": "Nb Shel.(R)",
        "interconnexion": "Interco.", "nb_panneaux": "Nb Pan.", "nb_rail": "Nb Rail",
        "problems": "Problèmes", "fin_stat": "Stat. Fin", "img_count": "Imgs"
    }

    header_paragraphs = [Paragraph(f"<b>{pdf_headers.get(fn, fn.replace('_', ' ').title())}</b>", small_bold_style) for fn in pdf_fieldnames]
    data_for_table = [header_paragraphs]

    for row in rows:
        row_data_paragraphs = []
        for field_key in pdf_fieldnames:
            cell_content_str = ""
            actual_attr = ""
            if field_key == 'img_count': cell_content_str = str(len(row.images))
            elif field_key == 'util': actual_attr = "utilisateur"
            elif field_key == 'nom_chantier': actual_attr = "nom_du_chantier"
            elif field_key == 'type_chantier': actual_attr = "chantier_type"
            elif field_key == 'equipe': actual_attr = "equipe"
            ique-pdf')
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
    
    smallelif field_key == 'onduleur_avanc': actual_attr = "onduleur_details_avancement"
            elif field_key == 'heure_travail': actual_attr = "heure_de_travail"
            elif field_key == 'equip_type': actual_attr = "equipement_type"
            elif field_key == 'equip_ref': actual_attr = "equipement_reference"
            elif field_key == 'equip_etat': actual_attr = "equipement_etat"
            elif field_key == 'cables_dc': actual_attr = "cables_dctires"
            elif field_key == 'cables_ac': actual_attr = "cables_actires"
            elif field_key == 'cables_terre': actual_attr = "cables_terretires"
_body_style = ParagraphStyle('smallBodyText', parent=styles['Normal'], fontSize=3.5) 
    small_bold_style = ParagraphStyle('smallBoldText', parent=styles['Normal'], fontSize=3.5, fontName='Helvetica-Bold')

    title_style = styles['h1']
    title_style.alignment = 1
    filter_utilisateur_req = request.args.get('filter_utilisateur')
    filter_nom_chantier_req = request.args.get('filter_nom_chantier')
    title_text = "Historique des Suivi Journaliers"
    if filter_utilisateur_req or filter_nom_chantier_req:
        title_text += " (Filtré)"
        if filter_utilisateur_req: title_text += f" - Utilisateur: {filter_utilisateur_req}"
        if filter_nom_chantier_req: title_text += f" - Chantier: {filter_nom_chantier_req}"
    elements.append(Paragraph(title_text, title_style))
    elements.append(Spacer(1, 0.15*inch))

    pdf_fieldnames = [
        "date", "util", "nom_chantier", "type_chantier",
            elif field_key == 'nb_onduleur_recept': actual_attr = "onduleur_nombre"
            elif field_key == 'nb_shelter_recept': actual_attr = "shelter_nombre"
            elif field_key == 'interconnexion':
                if row.chantier_type in ['centrale-sol', 'ombriere']: actual_attr = "interconnexion"
                else: cell_content_str = "-"
            elif field_key == 'nb_panneaux':
                if row.chantier_type == 'toiture': actual_attr = "nombre_panneaux"
                else: cell_content_str = "-"
            elif field_key == 'nb_rail':
                if row.chantier_type == 'toiture': actual_attr = "nombre_rail"
                else: cell_content_str = "-"
            elif field_key == 'problems': actual_attr = "problems"
            elif field_key == 'fin_stat': actual_attr = "fin_status"
        "equipe", "onduleur_avanc", "heure_travail", 
        "equip_type", "equip_ref", "equip_etat",
        "cables_dc", "cables_ac", "cables_terre",
        "nb_onduleur_recept", "nb_shelter_recept",
        "interconnexion", "nb_panneaux", "nb_rail",
        "problems", "fin_stat", "img_count"
    ]
    
    pdf_headers = {
        "date": "Date", "util": "Util.", "nom_chantier": "Nom Chant.", "type_chantier": "Type C.",
        "equipe": "Équipe", "onduleur_avanc": "Ondul.(Av)", "heure_travail": "H Trav.", 
        "equip_type": "Type Éq.", "equip_ref": "Réf. Éq.", "equip_etat": "État Éq.",
        "cables_dc": "DC Tiré", "cables_ac": "AC Tiré", "cables_terre": "Terre T.",
        "nb_onduleur_re            elif field_key == 'date': actual_attr = "date"

            if actual_attr and hasattr(row, actual_attr):
                 val = getattr(row, actual_attr, None)
                 cell_content_str = str(val) if val is not None else ""
            
            max_len = 10
            if len(cell_content_str) > max_len:
                cell_content_str = cell_content_str[:max_len-3] + "..."
            row_data_paragraphs.append(Paragraph(cell_content_str, small_body_style))
        data_for_table.append(row_data_paragraphs)

    if len(data_for_table) > 1:
        col_widths = [
            0.5*inch, 0.35*inch, 0.5*inch, 0.4*inch,
            0.5*inch, 0.6*inch, 0.4*inch,
            0.4*inch, 0.4*inch,cept": "Nb Ond.(R)", "nb_shelter_recept": "Nb Shel.(R)",
        "interconnexion": "Interco.", "nb_panneaux": "Nb Pan.", "nb_rail": "Nb Rail",
        "problems": "Problèmes", "fin_stat": "Stat. Fin", "img_count": "Imgs"
    }

    header_paragraphs = [Paragraph(f"<b>{pdf_headers.get(fn, fn.replace('_', ' ').title())}</b>", small_bold_style) for fn in pdf_fieldnames]
    data_for_table = [header_paragraphs]

    for row in rows:
        row_data_paragraphs = []
        for field_key in pdf_fieldnames:
            cell_content_str = ""
            actual_attr = ""
            if field_key == 'img_count': cell_content_str = str(len(row.images)) 0.35*inch,
            0.35*inch, 0.35*inch, 0.35*inch,
            0.4*inch, 0.4*inch,
            0.5*inch, 0.35*inch, 0.35*inch,
            0.8*inch, 0.4*inch, 0.3*inch
        ]
        

            elif field_key == 'util': actual_attr = "utilisateur"
            elif field_key == 'nom_chantier': actual_attr = "nom_du_chantier"
            elif field_key == 'type_chantier': actual_attr = "chantier_type"
            elif field_key == 'equipe': actual_attr = "equipe"
            elif field_key == 'onduleur_avanc': actual_attr = "onduleur_details_avancement"
            elif field_key == 'heure_travail': actual_attr = "heure_de_travail"
            elif field_key == 'equip_type':        table = Table(data_for_table, colWidths=col_widths, repeatRows=1)
        table_style = TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.darkslategray), ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'), ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'), ('FONTSIZE', (0, 0), (-1, 0), 3.5),
            ('BOTTOMPADDING', (0 actual_attr = "equipement_type"
            elif field_key == 'equip_ref': actual_attr = "equipement_reference"
            elif field_key == 'equip_etat': actual_attr = "equipement_etat"
            elif field_key == 'cables_dc': actual_attr = "cables_dctires"
            elif field_key == 'cables_ac': actual_attr = "cables_actires"
            elif field_key == 'cables_terre': actual_attr = "cables_terretires"
            elif field_key == 'nb_onduleur_recept': actual_attr = "onduleur_nombre" 
            elif field_key == 'nb_shelter_recept':, 0), (-1, 0), 2), ('TOPPADDING', (0, 0), (-1, 0), 2),
            ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey), ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('FONTSIZE', (0, 1), (-1, -1), 3.5),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
            ('LEFTPADDING', (0,0), (-1,-1), 1), ('RIGHTPADDING', (0,0), (-1,-1), 1),
            ('TOPPADDING', (0 actual_attr = "shelter_nombre"   
            elif field_key == 'interconnexion':
                if row.chantier_type in ['centrale-sol', 'ombriere']: actual_attr = "interconnexion"
                else: cell_content_str = "-"
            elif field_key == 'nb_panneaux':
                if row.chantier_type == 'toiture': actual_attr = "nombre_panneaux"
                else: cell_content_str = "-"
            elif field_key == 'nb_rail':
                if row.chantier_type == 'toiture': actual_attr = "nombre_rail"
                else: cell_content_str = "-"
            elif field_key == 'problems': actual_,1), (-1,-1), 1), ('BOTTOMPADDING', (0,1), (-1,-1), 1),
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

    return send_file(pdf_buffer, mimetype='application/pdf', as_attachment=True, download_name=pdfattr = "problems"
            elif field_key == 'fin_stat': actual_attr = "fin_status"
            elif field_key == 'date': actual_attr = "date"

            if actual_attr and hasattr(row, actual_attr):
                 val = getattr(row, actual_attr, None)
                 cell_content_str = str(val) if val is not None else ""
            
            max_len = 10 
            if len(cell_content_str) > max_len:
                cell_content_str = cell_content_str[:max_len-3] + "..."
            row_data_paragraphs.append(Paragraph(cell_content_str, small_body_style))
        data_for_table.append(row_data_paragraphs)

    if len(data_for_table) > _download_filename)

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
        role =1:
        col_widths = [
            0.5*inch, 0.35*inch, 0.5*inch, 0.4*inch, 
            0.5*inch, 0.6*inch, 0.4*inch,            
            0.4*inch, 0.4*inch, 0.35*inch,          
            0.35*inch, 0.35*inch, 0.35*inch,        
            0.4*inch, 0.4*inch,                     
            0.5*inch, 0.35*inch, 0.35*inch,         
            0.8*inch, 0.4*inch, 0.3*inch            
        ] 
        
        table = Table(data_for_table, colWidths=col_ request.form.get('role', 'user')

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
widths, repeatRows=1)
        table_style = TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.darkslategray), ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'), ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'), ('FONTSIZE', (0, 0), (-1, 0), 3.5),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 2), ('TOPPADDING', (0, 0), (-1, 0), 2),
            ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey), ('TEXTCOLOR', (0, 1), (-1, -        else:
            flash("❌ Action invalide ou champs manquants.", "danger")
        return redirect(url_for('admin_panel'))

    users = DBUser.query.all()
    return render_template('admin.html', utilisateurs=users, current_user=current_user)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 10000)), debug=False)
