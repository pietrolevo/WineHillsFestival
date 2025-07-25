# file: app.py         author: Pietro Alberto Levo          id: s311516 
# file di applicazione contenente il "main" dell applicazione, contiene le varie route e
# e chiama le funzioni definite nei file "DAO" performance.py, ticket.py e user.py .
# Completa le operazioni richieste dall'applicazione

from flask import Flask, render_template, request, redirect, url_for, flash
from werkzeug.security import check_password_hash
from flask_login import LoginManager, login_required, login_user, logout_user, current_user, UserMixin
from user import *
from performance import *
from ticket import *
from PIL import Image

IMG_WIDTH = 1280    # per ridimensionare con pillow 

app = Flask(__name__)
app.secret_key = 'secret_key' 

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# crea utente come oggetto 
class User(UserMixin):
    def __init__(self, id, email, role):
        self.id = id
        self.email = email
        self.role = role

    @staticmethod
    def get(user_id):
        usr = get_user_by_id(user_id)
        if usr:
            return User(usr["id"], usr["email"], usr["role"])
        return None

@login_manager.user_loader
def load_user(user_id):
    return User.get(int(user_id))


# pagina della home 
@app.route("/")
def home():
    day = request.args.get("day")
    stage = request.args.get("stage")
    genre = request.args.get("genre")
    
    organizer_id = None
    if current_user.is_authenticated and current_user.role == "organizzatore":
        organizer_id = current_user.id

    performances_list = get_filtered_performances(day, stage, genre, organizer_id)

    def day_order(day_str):
        mapping = {"venerdì": 1, "sabato": 2, "domenica": 3}
        return mapping.get(day_str.strip().lower(), 4)

    sorted_performances = sorted(
        performances_list,
        key=lambda perf: (day_order(perf["performance_day"]), perf["start_time"])
    )

    distinct_days = get_distinct_days()
    distinct_stages = get_distinct_stages()
    distinct_genres = get_distinct_genres()

    return render_template("home.html",
                           performances=sorted_performances,
                           days=distinct_days,
                           stages=distinct_stages,
                           genres=distinct_genres)


# pagina del login
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        usr = get_user_by_email(email)
        if usr and check_password_hash(usr["password"], password):
            user_obj = User(usr["id"], usr["email"], usr["role"])
            login_user(user_obj) 
            return redirect(url_for("home"))
        else:
            flash("Email o password errate", "login-error")
            return redirect(url_for("login"))
    return render_template("login.html")


# pagina del logout
@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Logout effettuato con successo.", "logout-success")
    return redirect(url_for("home"))


# pagina della registrazione
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        confirm_password = request.form["confirm_password"]
        role = request.form["role"]
        organizer_code = request.form.get("organizer_code", "")

        if password != confirm_password:
            flash("Le password non corrispondono. Riprova.", "register-error")
            return redirect(url_for("register"))
        
        if get_user_by_email(email):
            flash("Email già registrata. Usa un'altra email o accedi.", "register-error")
            return redirect(url_for("register"))

        SECURE_ORGANIZER_CODE = "DIRECTOR123"
        if role == "organizzatore" and organizer_code != SECURE_ORGANIZER_CODE:
            flash("Codice organizzatore errato. Contatta l'amministrazione per riceverlo.", "register-error")
            return redirect(url_for("register"))

        create_user(email, password, role)
        flash("Registrazione completata. Effettua il login.", "register-success")
        return redirect(url_for("login"))

    return render_template("register.html")


# pagina del profilo
@app.route("/profile")
@login_required
def profile():
    usr = get_user_by_id(current_user.id)
    
    ticket_info = None
    performances_for_organizer = None

    if usr and usr["role"] == "partecipante":
        ticket_info = get_ticket_by_user(usr["id"])
    elif usr and usr["role"] == "organizzatore":
        performances_for_organizer = get_performances_by_user(current_user.id)
        
        updated_performances_for_organizer = []
        for perf_item in performances_for_organizer:
            perf_dict = dict(perf_item)
            if perf_dict["published"] == 0: 
                conflict = check_overlapping_performance(
                    perf_dict["performance_day"],
                    perf_dict["start_time"],
                    perf_dict["duration"],
                    perf_dict["stage"]
                )
                perf_dict["non_pubblicabile"] = conflict
            else:
                perf_dict["non_pubblicabile"] = False 
            updated_performances_for_organizer.append(perf_dict)
        performances_for_organizer = updated_performances_for_organizer

    return render_template("profile.html", 
                           user={"email": usr["email"], "role": usr["role"]},
                           ticket=ticket_info, 
                           performances=performances_for_organizer)


# pagina della dashboard
@app.route("/dashboard")
@login_required
def dashboard():
    usr = get_user_by_id(current_user.id)
    if usr["role"] != "organizzatore":
        flash("Solo gli organizzatori possono accedere a questa sezione.", "dashboard-error")
        return redirect(url_for("home"))
    
    total_participants = get_total_participants()
    
    friday_count = count_tickets_for_day("venerdì")
    saturday_count = count_tickets_for_day("sabato")
    sunday_count = count_tickets_for_day("domenica")

    daily_pass_count = count_tickets_by_type("Giornaliero")
    two_day_pass_count = count_tickets_by_type("Pass 2 Giorni")
    full_pass_count = count_tickets_by_type("Full Pass")
    
    performances_list = get_organizer_dashboard_performances(current_user.id)
    
    updated_performances = []
    for perf in performances_list:
        perf_dict = dict(perf) 
        if perf_dict["published"] == 0: 
            conflict = check_overlapping_performance(
                perf_dict["performance_day"],
                perf_dict["start_time"],
                perf_dict["duration"],
                perf_dict["stage"]
            )
            perf_dict["non_pubblicabile"] = conflict
        else:
            perf_dict["non_pubblicabile"] = False 
        updated_performances.append(perf_dict)
    
    return render_template("dashboard.html",
                           friday=friday_count,
                           saturday=saturday_count,
                           sunday=sunday_count,
                           daily_pass=daily_pass_count,
                           two_day_pass=two_day_pass_count,
                           full_pass=full_pass_count,
                           performances=updated_performances,
                           total_participants=total_participants)


# pagina per aggiungere performance
@app.route("/add_performance", methods=["GET", "POST"])
@login_required
def add_performance():
    usr = get_user_by_id(current_user.id)
    if usr["role"] != "organizzatore":
        flash("Accesso non consentito. Solo gli organizzatori possono aggiungere performance.", "performance-error")
        return redirect(url_for("home"))
    
    if request.method == "POST":
        artist_name     = request.form["artist_name"]
        performance_day = request.form["performance_day"]
        start_time      = request.form["start_time"]
        duration        = int(request.form["duration"])
        description     = request.form["description"]
        stage           = request.form["stage"]
        genre           = request.form["genre"]
        image_path = ""

        post_image = request.files.get("performance_image")
        if post_image:
            img = Image.open(post_image)
            width, height = img.size
            new_height = height / width * IMG_WIDTH
            size = (IMG_WIDTH, new_height)
            img.thumbnail(size, Image.Resampling.LANCZOS)
            ext = post_image.filename.split(".")[-1]
            secondi = int(datetime.now().timestamp())
            filename = "@" + str(current_user.id) + "-" + str(secondi) + "." + ext
            img.save("static/" + filename)
            image_path = filename

        if artist_exists(artist_name):
            flash("Errore: L'artista è già presente nel programma.", "performance-error")
            return redirect(url_for("add_performance"))
        
        create_performance(
            artist_name, performance_day, start_time, duration,
            description, stage, genre, image_path,
            published=0, organizer_id=usr["id"]
        )
        flash("Performance aggiunta con successo come bozza.", "performance-success")
        return redirect(url_for("profile"))
    
    return render_template("add_performance.html")


@app.route("/performance/<int:performance_id>")
def performance_detail(performance_id):
    perf = get_performance_by_id(performance_id)
    if not perf:
        flash("Performance non trovata.", "performance-error")
        return redirect(url_for("home"))
    return render_template("performance_detail.html", performance=perf)


# pagina per modificare performance
@app.route("/edit_performance/<int:performance_id>", methods=["GET", "POST"])
@login_required
def edit_performance(performance_id):
    usr = get_user_by_id(current_user.id)
    if usr["role"] != "organizzatore":
        flash("Accesso non consentito. Solo gli organizzatori possono modificare performance.", "performance-error")
        return redirect(url_for("home"))
    
    perf = get_performance_by_id(performance_id)
    if not perf:
        flash("Performance non trovata.", "performance-error")
        return redirect(url_for("home"))
    
    if request.method == "POST":
        artist_name    = request.form["artist_name"]
        performance_day= request.form["performance_day"]
        start_time     = request.form["start_time"]
        duration       = int(request.form["duration"])
        description    = request.form["description"]
        stage          = request.form["stage"]
        genre          = request.form["genre"]
        image_path = dict(perf).get("image_path", "")

        post_image = request.files.get("performance_image")
        if post_image:
            img = Image.open(post_image)
            width, height = img.size
            new_height = height / width * IMG_WIDTH
            size = (IMG_WIDTH, new_height)
            img.thumbnail(size, Image.Resampling.LANCZOS)
            ext = post_image.filename.split(".")[-1]
            secondi = int(datetime.now().timestamp())
            filename = "@" + str(current_user.id) + "-" + str(secondi) + "." + ext
            img.save("static/" + filename)
            image_path = filename
        
        update_performance(performance_id, artist_name, performance_day,
                                         start_time, duration, description, stage, genre, image_path)
        flash("Performance aggiornata con successo.", "performance-success")
        return redirect(url_for("profile"))
    
    return render_template("edit_performance.html", performance=perf)


# pagina per pubblicare performance
@app.route("/publish_performance/<int:performance_id>")
@login_required
def publish_performance_route(performance_id):
    usr = get_user_by_id(current_user.id)
    if usr["role"] != "organizzatore":
        flash("Accesso non consentito.", "performance-error")
        return redirect(url_for("home"))
    
    perf = get_performance_by_id(performance_id)
    if not perf:
        flash("Performance non trovata.", "performance-error")
        return redirect(url_for("home"))
    
    if check_overlapping_performance(perf["performance_day"], perf["start_time"], perf["duration"], perf["stage"]):
        flash("Errore: La performance non può essere pubblicata perché si sovrappone a un evento già pubblicato.", "performance-error")
        return redirect(url_for("profile"))
    
    publish_performance(performance_id)
    flash("Performance pubblicata con successo.", "performance-success")
    return redirect(url_for("profile"))


# pagina per comprare biglietto
@app.route("/buy_ticket", methods=["GET", "POST"])
def buy_ticket():
    if request.method == "POST":
        if not current_user.is_authenticated:
            flash("Effettua il login per acquistare un biglietto.", "ticket-error")
            return redirect(url_for("login"))
        
        usr = get_user_by_id(current_user.id)
        if usr["role"] != "partecipante":
            flash("Solo i partecipanti possono acquistare biglietti.", "ticket-error")
            return redirect(url_for("home"))
        
        existing_ticket = get_ticket_by_user(usr["id"])
        if existing_ticket:
            flash("Hai già acquistato un biglietto per questo festival.", "info")
            return redirect(url_for("buy_ticket"))
        
        ticket_type = request.form.get("ticket_type")
        valid_days = ""

        day_selected = request.form.get("day")  
        pass2_selected = request.form.get("pass2_option")

        if ticket_type == "Full Pass":
            if day_selected or pass2_selected:
                flash("Non è possibile selezionare giorni per il Full Pass.", "ticket-error")
                return redirect(url_for("buy_ticket"))
            valid_days = "venerdì,sabato,domenica"

        elif ticket_type == "Giornaliero":
            if pass2_selected:
                flash("Se hai scelto Biglietto Giornaliero non puoi scegliere 2 giorni", "ticket-error")
                return redirect(url_for("buy_ticket"))
            if not day_selected:
                flash("Se hai scelto Biglietto Giornaliero, devi selezionare un giorno.", "ticket-error")
                return redirect(url_for("buy_ticket"))
            valid_days = day_selected

        elif ticket_type == "Pass 2 Giorni":
            if not pass2_selected:
                flash("Se hai scelto Pass 2 Giorni, devi selezionare un'opzione.", "ticket-error")
                return redirect(url_for("buy_ticket"))

            if day_selected: 
                flash("Non è possibile selezionare un giorno singolo con il Pass 2 Giorni.", "ticket-error")
                return redirect(url_for("buy_ticket"))

            valid_days = pass2_selected

        else:
            flash("Tipo di biglietto non valido.", "ticket-error")
            return redirect(url_for("buy_ticket"))

        
        days = [d.strip() for d in valid_days.split(",")]
        for day in days:
            count = count_tickets_for_day(day)
            if count >= 200:
                flash(f"La capacità per il giorno {day} è stata raggiunta.", "ticket-error")
                return redirect(url_for("buy_ticket"))
        
        create_ticket(usr["id"], ticket_type, valid_days)
        flash("Biglietto acquistato con successo.", "ticket-success")
        return redirect(url_for("profile"))

    ticket_info = None
    if current_user.is_authenticated:
        usr = get_user_by_id(current_user.id)
        if usr["role"] == "partecipante":
            ticket_info = get_ticket_by_user(usr["id"])
    return render_template("buy_ticket.html", ticket_info=ticket_info)


@app.route("/delete_performance/<int:performance_id>")
@login_required
def delete_performance_route(performance_id):
    usr = get_user_by_id(current_user.id)
    if usr["role"] != "organizzatore":
        flash("Accesso non consentito.", "performance-error")
        return redirect(url_for("home"))
    
    perf = get_performance_by_id(performance_id)
    if not perf:
        flash("Performance non trovata.", "performance-error")
        return redirect(url_for("home"))
    
    delete_performance(performance_id)
    flash("Performance eliminata con successo.", "performance-success")
    return redirect(url_for("profile"))

# pagina about
@app.route("/about")
def about():
    return render_template("about.html")

# pagina artisti
@app.route('/singers')
def artisti():
    performances = get_published_performances()  
    return render_template('singers.html', performances=performances)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=3000, debug=True)
