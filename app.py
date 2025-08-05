from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
import os
from datetime import date, datetime
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps

app = Flask(__name__)
app.secret_key = 'your_strong_random_secret_key_here' # IMPORTANT: Change this to a strong, random key in production

# Configure your database connection
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root:123456@localhost/application_web'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# --- SQLAlchemy Models ---
class Evenement(db.Model):
    __tablename__ = 'Événement'
    id_événement = db.Column(db.Integer, primary_key=True, autoincrement=True)
    titre = db.Column(db.String(255), nullable=False)
    date_début = db.Column(db.Date, nullable=False)
    date_fin = db.Column(db.Date, nullable=False)
    lieu = db.Column(db.String(255), nullable=False)
    description_courte = db.Column(db.Text)
    sponsort = db.Column(db.Text)
    logo = db.Column(db.Text)
    clients = db.relationship('Client', backref='event', lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Evenement {self.titre}>"

class Client(db.Model):
    __tablename__ = 'Client'
    id_client = db.Column(db.Integer, primary_key=True, autoincrement=True)
    nom = db.Column(db.String(255), nullable=False)
    prénom = db.Column(db.String(255), nullable=False)
    status = db.Column(db.String(255))
    email = db.Column(db.String(255), nullable=False)
    tel = db.Column(db.Integer)
    date_naissance = db.Column(db.Date)
    genre = db.Column(db.String(50))
    date_creation = db.Column(db.Date, default=datetime.utcnow)
    date_modification = db.Column(db.Date, default=datetime.utcnow, onupdate=datetime.utcnow)
    id_événement = db.Column(db.Integer, db.ForeignKey('Événement.id_événement'), nullable=False)

    def __repr__(self):
        return f"<Client {self.nom} {self.prénom}>"

class Utilisateur(db.Model):
    __tablename__ = 'Utilisateurs'

    id_utilisateur = db.Column(db.Integer, primary_key=True, autoincrement=True)
    email = db.Column(db.String(255), nullable=False, unique=True)
    mot_de_passe = db.Column(db.String(255), nullable=False)
    nom = db.Column(db.String(255))
    prénom = db.Column(db.String(255))
    cin = db.Column(db.Integer)
    téléphone = db.Column(db.Integer)
    status = db.Column(db.String(255))
    role = db.Column(db.String(255))
    date_creation = db.Column(db.Date, default=datetime.utcnow)
    date_modification = db.Column(db.Date, default=datetime.utcnow, onupdate=datetime.utcnow)


    def set_password(self, password):
        self.mot_de_passe = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.mot_de_passe, password)

    def __repr__(self):
        return f"<Utilisateur {self.email}>"

# --- Decorator to protect routes ---
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('Veuillez vous connecter pour accéder à cette page.', 'warning')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# --- Route for the main entry point ---
@app.route('/')
def index():
    return render_template('login.html')

# --- Admin Login Route ---
@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        session.pop('user_id', None)
        session.pop('user_email', None)
        flash('Votre session précédente est terminée. Veuillez vous reconnecter.', 'info')

    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = Utilisateur.query.filter_by(email=email).first()

        if user:
            if user and user.check_password(password):
                if user.status == 'Active':
                    session['user_id'] = user.id_utilisateur
                    session['user_email'] = user.email
                    session['user_role'] = user.role
                    "flash('Connecté avec succès!', 'success')" # normalement nzidha fel page admin
                    return redirect(url_for('admin_dashboard'))
                else:
                    flash('Votre compte est inactif. Veuillez contacter l\'administrateur.', 'danger')
            else:
                flash('Mot de passe ou adresse mail incorrect.', 'danger')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('user_email', None)
    session.pop('user_role', None)
    flash('Vous avez été déconnecté.', 'info')
    return redirect(url_for('login'))

# --- Client Registration and Badge Generation Routes ---
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        nom = request.form['nom']
        prenom = request.form['prenom']
        email = request.form['email']
        telephone = request.form.get('tel')
        date_naissance_str = request.form.get('date_naissance')
        event_id = request.form['event_id']
        genre = request.form.get('genre')
        status = request.form.get('status')

        date_naissance = None
        if date_naissance_str:
            try:
                date_naissance = datetime.strptime(date_naissance_str, '%Y-%m-%d').date()
            except ValueError:
                flash("Format date invalide pour la date de naissance.", 'danger')
                events = Evenement.query.order_by(Evenement.date_début.asc()).all()
                return render_template('register_form.html', events=events)

        try:
            existing_client = Client.query.filter_by(email=email).first()

            if existing_client:
                existing_client.nom = nom
                existing_client.prénom = prenom
                existing_client.tel = telephone
                existing_client.date_naissance = date_naissance
                existing_client.genre = genre
                existing_client.status = status
                existing_client.id_événement = event_id
                flash("Votre inscription a été mise à jour !", 'success')
                db.session.commit()
                return redirect(url_for('generate_badge', client_id=existing_client.id_client))
            else:
                new_client = Client(
                    nom=nom,
                    prénom=prenom,
                    email=email,
                    tel=telephone,
                    date_naissance=date_naissance,
                    genre=genre,
                    status=status,
                    id_événement=event_id
                )
                db.session.add(new_client)
                db.session.commit()
                flash("Inscription réussie!", 'success')
                return redirect(url_for('generate_badge', client_id=new_client.id_client))

        except IntegrityError as e:
            db.session.rollback()
            flash("An account with this email already exists or another database integrity issue occurred.", 'warning')
            print(f"Integrity Error: {e}")
            events = Evenement.query.order_by(Evenement.date_début.asc()).all()
            return render_template('register_form.html', events=events)
        except SQLAlchemyError as e:
            db.session.rollback()
            flash(f"Erreur lors de l'inscription: {e}", 'danger')
            print(f"SQLAlchemy Error: {e}")
            events = Evenement.query.order_by(Evenement.date_début.asc()).all()
            return render_template('register_form.html', events=events) 

    else:
        try:
            events = Evenement.query.order_by(Evenement.date_début.asc()).all()
            return render_template('register_form.html', events=events)
        except SQLAlchemyError as e:
            flash(f"Erreur lors de la récupération des événements pour le formulaire d'inscription: {e}", 'danger')
            print(f"SQLAlchemy Error: {e}")
            return render_template('error.html')


@app.route('/badge/<int:client_id>')
def generate_badge(client_id):

    try:
        client = Client.query.get_or_404(client_id)
        event = client.event

        event_date_formatted = f"{event.date_début.strftime('%Y-%m-%d')} - {event.date_fin.strftime('%Y-%m-%d')}"

        return render_template(
            'badge.html',
            client_id=client.id_client,
            client_nom=client.nom,
            client_prenom=client.prénom,
            client_status=client.status,
            event_title=event.titre,
            event_date=event_date_formatted,
            event_lieu=event.lieu,
            event_logo_url=event.logo,
            event_sponsort=event.sponsort,
        )
    except SQLAlchemyError as e:
        flash(f"Erreur géneration de la badge: {e}", 'danger')
        print(f"SQLAlchemy Error: {e}")
        return render_template('error.html')
    except Exception as e:
        flash(f"Une erreur inattendue s'est produite: {e}", 'danger')
        print(f"General Error: {e}")
        return render_template('error.html')

# --- Admin Routes (protected) ---

@app.route('/admin')
@login_required
def admin_dashboard():
    user_id = session.get('user_id')
    if user_id:
        user = Utilisateur.query.get(user_id)
        if user:
            if user.role == 'Admin':
                return render_template('admin.html')
            elif user.role == 'Agent De Saisie':
                return render_template('agent_de_saisie.html')
            elif user.role == 'Responsable Marketing':
                return render_template('responsable.html')
            else:
                flash('Le role de votre compte n a pas accès à un tableau de bord.', 'danger')
                return redirect(url_for('login'))
        else:
            flash('Utilisateur introuvable. Veuillez vous reconnecter.', 'danger')
            return redirect(url_for('login'))
    else:
        flash('Session expirée. Veuillez vous reconnecter.', 'danger')
        return redirect(url_for('login'))

@app.route('/admin/events')
@login_required
def events():
    try:
        events = Evenement.query.order_by(Evenement.date_début.desc()).all()
        return render_template('gestion_event.html', events=events)
    except SQLAlchemyError as e:
        flash(f"Erreur chargement des événements: {e}", 'danger')
        print(f"SQLAlchemy Error: {e}")
        return render_template('error.html')

@app.route('/admin/clients')
@login_required
def manage_clients():
    try:
        all_clients = Client.query.order_by(Client.date_creation.desc()).all()
        return render_template('clients.html', clients=all_clients)
    except SQLAlchemyError as e:
        flash(f"Erreur chargement des clients: {e}", 'danger')
        print(f"SQLAlchemy Error: {e}")
        return render_template('error.html')

@app.route('/admin/events/<int:event_id>/clients')
@login_required
def view_event_clients(event_id):
    try:
        event = Evenement.query.get_or_404(event_id)
        clients = event.clients
        return render_template('event_clients.html', event=event, clients=clients)
    except SQLAlchemyError as e:
        flash(f"Erreur chargements de la liste des clients pour chaque événement {event_id}: {e}", 'danger')
        print(f"SQLAlchemy Error: {e}")
        return render_template('error.html')
    except Exception as e:
        flash(f"Une erreur inattendue s'est produite: {e}", 'danger')
        print(f"General Error: {e}")
        return render_template('error.html')

@app.route('/admin/events/<int:event_id>/add_client', methods=['GET', 'POST'])
@login_required
def add_client_to_event(event_id):
    event = Evenement.query.get_or_404(event_id)
    if request.method == 'POST':
        nom = request.form['nom']
        prenom = request.form['prenom']
        email = request.form['email']
        telephone = request.form.get('tel')
        date_naissance_str = request.form.get('date_naissance')
        genre = request.form.get('genre')
        status = request.form.get('status')

        date_naissance = None
        if date_naissance_str:
            try:
                date_naissance = datetime.strptime(date_naissance_str, '%Y-%m-%d').date()
            except ValueError:
                flash("Format de date de naissance non valide. Veuillez utiliser AAAA-MM-JJ.", 'danger')
                return render_template('add_edit_client.html', form_title=f"Add Client to {event.titre}", client=None, event=event)

        try:
            new_client = Client(
                nom=nom,
                prénom=prenom,
                email=email,
                tel=telephone,
                date_naissance=date_naissance,
                genre=genre,
                status=status,
                id_événement=event.id_événement
            )
            db.session.add(new_client)
            db.session.commit()
            flash("Client ajouté avec succès!", 'success')
            return redirect(url_for('generate_badge', client_id=new_client.id_client))
        except SQLAlchemyError as e:
            db.session.rollback()
            flash(f"Erreur ajout du client: {e}", 'danger')
            print(f"SQLAlchemy Error: {e}")
            return render_template('add_edit_client.html', form_title=f"Add Client to {event.titre}", client=None, event=event)
    else:
        return render_template('add_edit_client.html', form_title=f"Ajouter un client à {event.titre}", client=None, event=event)
    

@app.route('/admin/clients/<int:client_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_client(client_id):
    client = Client.query.get_or_404(client_id)
    event = client.event

    next_url = request.args.get('next')

    if request.method == 'POST':
        nom = request.form['nom']
        prenom = request.form['prenom']
        email = request.form['email']
        telephone = request.form.get('tel')
        date_naissance_str = request.form.get('date_naissance')
        genre = request.form.get('genre')
        status = request.form.get('status')

        date_naissance = None
        if date_naissance_str:
            try:
                date_naissance = datetime.strptime(date_naissance_str, '%Y-%m-%d').date()
            except ValueError:
                flash("Format de date de naissance non valide. Veuillez utiliser AAAA-MM-JJ.", 'danger')
                return render_template('add_edit_client.html', form_title=f"Edit Client for {event.titre}", client=client, event=event)

        try:
            client.nom = nom
            client.prénom = prenom
            client.email = email
            client.tel = telephone
            client.date_naissance = date_naissance
            client.genre = genre
            client.status = status
            db.session.commit()
            flash("Client modifié avec succés !", 'success')
            return redirect(url_for('generate_badge', client_id=client.id_client))
        except IntegrityError as e:
            db.session.rollback()
            flash("Compte existant !", 'warning')
            print(f"Integrity Error: {e}")
            return render_template('add_edit_client.html', form_title=f"Edit Client for {event.titre}", client=client, event=event)
        except SQLAlchemyError as e:
            db.session.rollback()
            flash(f"Erreur modification du client: {e}", 'danger')
            print(f"SQLAlchemy Error: {e}")
            return render_template('add_edit_client.html', form_title=f"Edit Client for {event.titre}", client=client, event=event)
    else:
        return render_template('add_edit_client.html', form_title=f"Modifier le client pour {event.titre}", client=client, event=event, next_url=next_url)

@app.route('/admin/clients/<int:client_id>/delete', methods=['GET'])
@login_required
def delete_client(client_id):
    try:
        client_to_delete = Client.query.get_or_404(client_id)
        event_id = client_to_delete.id_événement
        db.session.delete(client_to_delete)
        db.session.commit()
        flash("Client supprimé avec succés!", 'success')
    except SQLAlchemyError as e:
        db.session.rollback()
        flash(f"Erreur supression client: {e}", 'danger')
        print(f"SQLAlchemy Error: {e}")
    except Exception as e:
        db.session.rollback()
        flash(f"Une erreur inattendue s'est produite durant la supression: {e}", 'danger')
        print(f"General Error during deletion: {e}")

    next_url = request.args.get('next')
    if next_url:
        return redirect(next_url)
    else:
        return redirect(url_for('view_event_clients', event_id=event_id))
    

@app.route('/admin/details_client/<int:client_id>')
@login_required
def details_client(client_id):
    client = Client.query.get_or_404(client_id)
    return render_template('details.client.html', client=client)    

# --- NEW: User (Account) Management Routes ---

@app.route('/admin/accounts')
@login_required
def manage_accounts():
    try:
        users = Utilisateur.query.order_by(Utilisateur.email.asc()).all()
        return render_template('admin_accounts.html', users=users)
    except SQLAlchemyError as e:
        flash(f"Erreur chargement des comptes utilisateurs: {e}", 'danger')
        print(f"SQLAlchemy Error: {e}")
        return render_template('error.html')

@app.route('/admin/accounts/add', methods=['GET', 'POST'])
@login_required
def add_user():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        nom = request.form.get('nom')
        prenom = request.form.get('prenom')
        cin = request.form.get('cin')
        telephone = request.form.get('telephone')
        status = request.form.get('status')
        role = request.form.get('role')

        if not password:
            flash("Un mot de passe est requis pour le nouvel utilisateur.", 'danger')
            return render_template('add_edit_user.html', form_title="Ajouter un utilisateur", user=None)

        try:
            new_user = Utilisateur(
                email=email,
                nom=nom,
                prénom=prenom,
                cin=cin,
                téléphone=telephone,
                status=status,
                role=role,
            )
            new_user.set_password(password) # Hash the password
            db.session.add(new_user)
            db.session.commit()
            flash("Utilisateur ajouté avec succès!", 'success')
            return redirect(url_for('manage_accounts'))
        except IntegrityError:
            db.session.rollback()
            flash("Un compte avec cet e-mail existe déjà.", 'danger')
            return render_template('add_edit_user.html', form_title="Ajouter un utilisateur", user=None)
        except SQLAlchemyError as e:
            db.session.rollback()
            flash(f"Erreur ajout d'un compte utilisateur: {e}", 'danger')
            print(f"SQLAlchemy Error: {e}")
            return render_template('add_edit_user.html', form_title="Ajouter un utilisateur", user=None)
    else:
        return render_template('add_edit_user.html', form_title="Ajouter un utilisateur", user=None)

@app.route('/admin/accounts/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_user(user_id):
    user = Utilisateur.query.get_or_404(user_id)
    if request.method == 'POST':
        email = request.form['email']
        password = request.form.get('password') # Password is optional for edit
        nom = request.form.get('nom')
        prenom = request.form.get('prenom')
        cin = request.form.get('cin')
        telephone = request.form.get('telephone')
        status = request.form.get('status')
        role = request.form.get('role')

        try:
            user.email = email
            user.nom = nom
            user.prénom = prenom
            user.cin = cin
            user.téléphone = telephone
            user.status = status
            user.role = role
            if password: # Only update password if a new one is provided
                user.set_password(password)
            db.session.commit()
            flash("L'utilisateur a été mis à jour avec succès!", 'success')
            return redirect(url_for('manage_accounts'))
        except IntegrityError:
            db.session.rollback()
            flash("Un compte avec cet e-mail existe déjà.", 'danger')
            return render_template('add_edit_user.html', form_title="Modifier l'utilisateur", user=user)
        except SQLAlchemyError as e:
            db.session.rollback()
            flash(f"Erreur mis à jour au compte: {e}", 'danger')
            print(f"SQLAlchemy Error: {e}")
            return render_template('add_edit_user.html', form_title="Modifier l'utilisateur", user=user)
    else:
        return render_template('add_edit_user.html', form_title="Modifier l'utilisateur", user=user)
    
@app.route('/admin/accounts/<int:user_id>/details', methods=['GET'])
@login_required
def details_user(user_id):
    try:
        user = Utilisateur.query.get_or_404(user_id)
        return render_template('user.details.html', user=user)
    except SQLAlchemyError as e:
        flash(f"Erreur lors du chargement des détails de l'utilisateur : {e}", 'danger')
        print(f"SQLAlchemy Error: {e}")
        return redirect(url_for('manage_accounts'))
    except Exception as e:
        flash(f"Une erreur inattendue s'est produite : {e}", 'danger')
        print(f"General Error: {e}")
        return redirect(url_for('manage_accounts'))
        

@app.route('/admin/accounts/<int:user_id>/delete', methods=['GET'])
@login_required
def delete_user(user_id):
    """Deletes an administrative user."""
    try:
        user_to_delete = Utilisateur.query.get_or_404(user_id)
        db.session.delete(user_to_delete)
        db.session.commit()
        flash("L'utilisateur a été supprimé avec succès!", 'success')
    except SQLAlchemyError as e:
        db.session.rollback()
        flash(f"Erreur supression du compte utlisateur: {e}", 'danger')
        print(f"SQLAlchemy Error: {e}")
    except Exception as e:
        db.session.rollback()
        flash(f"Une erreur inattendue s'est produite durant la supression: {e}", 'danger')
        print(f"General Error during deletion: {e}")
    return redirect(url_for('manage_accounts'))


@app.route('/admin/add_event', methods=['GET', 'POST'])
@login_required
def add_event():
    if request.method == 'POST':
        titre = request.form['titre']
        date_debut_str = request.form['date_debut']
        date_fin_str = request.form['date_fin']
        lieu = request.form['lieu']
        description_courte = request.form['description_courte']
        sponsort = request.form.get('sponsort')
        logo = request.form.get('logo')

        try:
            date_debut = datetime.strptime(date_debut_str, '%Y-%m-%d').date()
            date_fin = datetime.strptime(date_fin_str, '%Y-%m-%d').date()
        except ValueError:
            flash("Format de date non valide pour les dates d'événements. Veuillez utiliser AAAA-MM-JJ.", 'danger')
            return render_template('add_edit_event.html', form_title="Add New Event", event=None)

        try:
            new_event = Evenement(
                titre=titre,
                date_début=date_debut,
                date_fin=date_fin,
                lieu=lieu,
                description_courte=description_courte,
                sponsort=sponsort,
                logo=logo
            )
            db.session.add(new_event)
            db.session.commit()
            flash("Événement ajouté avec succès!", 'success')
            return redirect(url_for('events'))
        except SQLAlchemyError as e:
            db.session.rollback()
            flash(f"Erreur ajout événement: {e}", 'danger')
            print(f"SQLAlchemy Error: {e}")
            return render_template('add_edit_event.html', form_title="Add New Event", event=None)
    else:
        return render_template('add_edit_event.html', form_title="Add New Event", event=None)

@app.route('/admin/edit_event/<int:event_id>', methods=['GET', 'POST'])
@login_required
def edit_event(event_id):
    event = Evenement.query.get_or_404(event_id)

    if request.method == 'POST':
        titre = request.form['titre']
        date_debut_str = request.form['date_debut']
        date_fin_str = request.form['date_fin']
        lieu = request.form['lieu']
        description_courte = request.form['description_courte']
        sponsort = request.form.get('sponsort')
        logo = request.form.get('logo')

        try:
            date_debut = datetime.strptime(date_debut_str, '%Y-%m-%d').date()
            date_fin = datetime.strptime(date_fin_str, '%Y-%m-%d').date()
        except ValueError:
            flash("Format de date non valide pour les dates d'événements. Veuillez utiliser AAAA-MM-JJ.", 'danger')
            return render_template('add_edit_event.html', form_title="Edit Event", event=event)

        try:
            event.titre = titre
            event.date_début = date_debut
            event.date_fin = date_fin
            event.lieu = lieu
            event.description_courte = description_courte
            event.sponsort = sponsort
            event.logo = logo

            db.session.commit()
            flash("Événement mis à jour avec succès !", 'success')
            return redirect(url_for('events'))
        except SQLAlchemyError as e:
            db.session.rollback()
            flash(f"Erreur mis à jour de l'événement: {e}", 'danger')
            print(f"SQLAlchemy Error: {e}")
            return render_template('add_edit_event.html', form_title="Edit Event", event=event)
    else:
        return render_template('add_edit_event.html', form_title="Edit Event", event=event)

@app.route('/admin/delete_event/<int:event_id>', methods=['GET'])
@login_required
def delete_event(event_id):
    try:
        event_to_delete = Evenement.query.get_or_404(event_id)
        db.session.delete(event_to_delete)
        db.session.commit()
        flash("L'événement et les clients associés ont été supprimés avec succès!", 'success')
    except SQLAlchemyError as e:
        db.session.rollback()
        flash(f"Erreur supression de l'événement: {e}", 'danger')
        print(f"SQLAlchemy Error: {e}")
    except Exception as e:
        db.session.rollback()
        flash(f"Une erreur inattedue s'est produite durant la supression: {e}", 'danger')
        print(f"General Error during deletion: {e}")
    return redirect(url_for('events'))

@app.route('/admin/details_event/<int:event_id>')
@login_required
def details_event(event_id):
    event = Evenement.query.get_or_404(event_id)
    return render_template('details.event.html', event=event)

# --- Running the app ---
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
