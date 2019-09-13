# Application Web pour enregistrer un client 

from flask import Flask, request, render_template, flash,  redirect, url_for, session
import hashlib, uuid, os
from werkzeug.utils import secure_filename


# Connexion avec la base de données Msql en localhost BdDemo

UPLOAD_FOLDER = '/mnt/c/Users'
ALLOWED_EXTENSIONS = set(['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'])
import mysql.connector as MS
connection = MS.connect(user='root', password='root', host='127.0.0.1', buffered=True)
cursor = connection.cursor()

utiliser_bd = "USE BdDemo"
cursor.execute(utiliser_bd)
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['IMAGES_PATH'] = UPLOAD_FOLDER

app.config.update(
    DEBUG=True,
    SECRET_KEY='secret_xxx'
)

# la premier route par defaut qui méne vers la racine

@app.route('/')
def index():
    if "e_mail" in session:
        return redirect(url_for('mes_informations'))
    else:
        return render_template("/se_connecter.html")

# on récupére les informations de la page enregister_client pour les passer dans des variables et les insérer dans la base de donnée.		
		
@app.route("/enregistrer_client", methods=["GET", "POST"])
def enregistrer_client():

    error = None

    provinces = ["Province", "Dakar", " Baol", "Casa", "Touba", "Mbacke", "Fatick", "Darou", "Salam", "Moukhety", "Saloum", "Bambey", "Pikine", "Tamba", "Ndar"]

    if "e_mail" in session:
        return redirect(url_for('mes_informations'))

    if request.method == "GET":
        return render_template("enregistrer_client.html", provinces = provinces )

    if request.method == "POST":

        # """Informations Client"""

        id_client = str(uuid.uuid4())
        prenom = request.form["prenom"]
        nom = request.form["nom"]
        e_mail = request.form["e_mail"]
        mot_de_passe = request.form["mot_de_passe"]
        mot_de_passe_hash = hashlib.sha256(str(mot_de_passe).encode("utf-8")).hexdigest()
        description = request.form["description"]

        # """Informations Adresse Client"""

        id_adresse = str(uuid.uuid4())
        numero_appartement = request.form["numero_appartement"]
        numero_rue = request.form["numero_rue"]
        nom_rue = request.form["nom_rue"]
        ville = request.form["ville"]
        province = request.form["province"]
        code_postal = request.form["code_postal"]


        # """verifier si l'e-mail n'est pas deja utilise par un client"""

        req_client_existant = "SELECT * FROM Client WHERE Email = '%s' "
        cursor.execute(req_client_existant % e_mail)
        resultat_req_client_existant = cursor.fetchall()
        print(resultat_req_client_existant)

        # '''Si on a déjà un e-mail avec cette adresse, on dit que le mail est déjà utilisé'''

        if len(resultat_req_client_existant) > 0:
            error = 'Cette adresse courriel est deja utilisee, veuillez utiliser une autre adresse'
            return render_template("enregistrer_client.html", provinces=provinces, error = error)



        #"""Sinon on enregistre les informations du client dans la BD"""

        else:

            req_enregister_client = "INSERT INTO Client (IdClient, Prenom, Nom, Email, MotDePasseHash, Description)VALUES(%s,%s,%s,%s,%s,%s)"
            cursor.execute(req_enregister_client, (id_client, prenom, nom, e_mail, mot_de_passe_hash, description))
            connection.commit()

            req_enregister_adresse = "INSERT INTO Adresse (IdAdresse,NumeroAppartement, NumeroDeRue,NomDeRue, Ville, Province, CodePostal, IdClient) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)"
            cursor.execute(req_enregister_adresse, (id_adresse,numero_appartement, numero_rue,nom_rue,ville,province,code_postal,id_client))
            connection.commit()
            session["e_mail"] = request.form["e_mail"]

            # """Inserer image par defaut"""

            requete_inserer_image = "INSERT INTO Image (IdImage, Nom, IdClient) VALUES ('%s','%s','%s')"
            id_image = str(uuid.uuid4())
            nom = "default.jpg"
            cursor.execute(requete_inserer_image % (id_image, nom, id_client))
            connection.commit()


            return redirect(url_for('mes_informations'))
			
	
#si la connexion est bon, on redirige l’utilisateur vers la page de ses informations Sinon, on lui demande de mettre la bonne combinaison
@app.route("/se_connecter", methods=["GET", "POST"])
def se_connecter():
    error = None

    if request.method == "POST":
        e_mail = request.form["e_mail"]

        mot_de_passe = request.form["mot_de_passe"]
        mot_de_passe_hash = hashlib.sha256(str(mot_de_passe).encode("utf-8")).hexdigest()

        req_connection_client = "SELECT * FROM Client where Email = '%s' AND MotDePasseHash = '%s' "
        cursor.execute(req_connection_client % (e_mail, mot_de_passe_hash))
        resultat_connection_client = cursor.fetchall()

        if len(resultat_connection_client) == 0:
            session['e_mail'] = None
            error = "Cette adresse courriel ou ce mot de passe ne sont pas valides, veuillez reessayer"
            return render_template("se_connecter.html", error=error)


        else:
            session["e_mail"] = request.form["e_mail"]
            return redirect(url_for('mes_informations'))

    elif request.method == "GET":
        return render_template("se_connecter.html")
		

#On arrive finalement à la dernière route de la page d’information

@app.route("/mes_informations", methods=["GET", "POST"])
def mes_informations():
    if request.method == "GET" and  "e_mail" in session:
        e_mail = session["e_mail"]
        requette_avoir_id_client = "SELECT IdClient FROM Client WHERE Email = '%s'"
        cursor.execute(requette_avoir_id_client % e_mail)

        id_client = cursor.fetchone()

        requete_information_client = "SELECT C.Prenom, C.Nom, C.Email, A.NumeroAppartement, A.NumeroDeRue, A.NomDeRue, A.Ville, A.Province, A.CodePostal, C.Description " \
                                     "FROM Client as C , Adresse as A WHERE C.IdClient = A.IdClient AND C.Email = '%s'"
        cursor.execute(requete_information_client % e_mail)
        resultat_requete_information_client = cursor.fetchall()
        requete_image = "select Image.Nom FROM Image where Image.IdClient = '%s'"
        cursor.execute(requete_image % id_client)
        nom_image = cursor.fetchone()
        nom_image = nom_image [0]
        lieu_image = os.path.join(app.config['UPLOAD_FOLDER'], nom_image)
        lieu_image = str(lieu_image)
        print(lieu_image)

        print(resultat_requete_information_client)
        return render_template("/mes_informations.html",
                               resultat_requete_information_client=resultat_requete_information_client, lieu_image= lieu_image)

    if request.method == "POST":
        e_mail = session["e_mail"]

        # """Photo client"""
        requette_avoir_id_client = "SELECT IdClient FROM Client WHERE Email = '%s'"
        cursor.execute(requette_avoir_id_client % e_mail)
        id_client =cursor.fetchone()
        image = request.files["image"]
        id_image = str(uuid.uuid4())
        nom = secure_filename(image.filename)
        image.save(os.path.join(app.config['UPLOAD_FOLDER'], nom))

        requete_inserer_image = "INSERT INTO Image (IdImage, Nom, IdClient) VALUES ('%s','%s','%s')"
        cursor.execute(requete_inserer_image %(id_image, nom, id_client[0]))
        connection.commit()
        flash("Votre image est enregistree")

        return redirect(url_for('mes_informations'))
    else :
        return redirect(url_for('se_connecter'))
		
# cette route permet de ce deconnecter
@app.route("/se_deconnecter")
def se_deconnecter ():
    session.pop("e_mail", None)
    flash('Vous etes maintenant deconnecte')
    return redirect(url_for('se_connecter'))

if __name__ == '__main__':
   app.run(host='0.0.0.0')