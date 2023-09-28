import json,requests,random,string
from functools import wraps
from flask import render_template,request,abort,redirect,flash,make_response,session,url_for
from werkzeug.security import generate_password_hash, check_password_hash

# local imports follows below
from bookapp import app,csrf,mail,Message
from bookapp.models import *
from bookapp.forms import *




# creating a decorator to be checking login
def login_required(f):
    @wraps(f) #this ensures that the details(meta data) about the original function f, that is being decorated id still available. for tha reason, we from functools import wraps
    def login_check(*args, **kwargs):
        if session.get("userloggedin") != None:
            return f(*args, **kwargs)
        else:
            flash("Access Denied")
            return redirect('/login')
    return login_check
# To use login_required, place it after the route decorator over any route that needs authentication


def generate_string(howmany):#call this function as renerate_string(10)
    x = random.sample(string.digits,howmany)
    return ''.join(x)


@app.route("/landing")
@login_required
def landing_page():
    refno = session.get("trxno")
    transaction_deets = db.session.query(Donation).filter(Donation.don_refno==refno).first()
    url="https://api.paystack.co/transaction/verify/" +transaction_deets.don_refno
    headers = {"Content-Type": "application/json","Authorization":"Bearer sk_test_7056bf4a73fba68635f48106f022172f378e30af"}
    response = requests.get(url,headers=headers)
    rspjson = json.loads(response.text)
    # return rspjson #retieve the details and update your database
    if rspjson["status"] == True:
        paystatus = rspjson["data"]["gateway_response"]
        transaction_deets.don_status = "Paid"
        db.session.commit()
        return redirect("/dashboard")#paysatck page will load
    else:
        # flash("Please complete the form again")
        flash("Payment failed")
        return redirect("/reports")



@app.route("/initialize/paystack",methods=["POST","GET"])
@login_required
def initialize_paystack():
    userid = session["userloggedin"]
    deets = db.session.query(User).get(userid)
    # transaction details
    refno = session.get("trxno")
    transaction_details = db.session.query(Donation).filter(Donation.don_refno==refno).first()
    # make a curl request to the paystack endpoint
    url="https://api.paystack.co/transaction/initialize"
    headers = {"Content-Type": "application/json","Authorization":"Bearer sk_test_7056bf4a73fba68635f48106f022172f378e30af"}
    data={ 
        "email": deets.user_email, 
        "amount": transaction_details.don_amt,
        "reference":refno
        }
    response = requests.post(url,headers=headers,data=json.dumps(data))
    # #extract json fro the response coming from paysatck
    rspjson = response.json()
    # return rspjson
    if rspjson["status"] == True:
        redirectURL = rspjson["data"]["authorization_url"]
        return redirect(redirectURL)#paysatck page will load
    else:
        flash("Please complete the form again")
        return redirect("/donate")

@app.route("/donate/",methods=["POST","GET"])
@login_required
def donation():
    donate = DonationForm()
    if request.method == "GET":
        deets = db.session.query(User).get(session["userloggedin"])
        return render_template("user/donation_form.html",donate=donate,deets=deets)
    else:
        if donate.validate_on_submit():
            #retrieve formmdata
            #insert into db
            #generate a transaction reference
            #redirect to a confirmation page
            amt = float(donate.amount.data) * 100
            donor = donate.fullname.data
            email = donate.email.data
            ref = "BW" + str(generate_string(8))
            don = Donation(don_amt=amt,don_userid=session["userloggedin"],don_email=email,don_fullname=donor,don_status="pending",don_refno=ref)
            db.session.add(don)
            db.session.commit()
            #save the reference no in session
            session["trxno"] = ref
            #redirect to a confirmation page
            return redirect("/confirm_donation")
        else:
            deets = db.session.query(User).get(session["userloggedin"])
            return render_template("user/donation_form.html",donate=donate,deets=deets)


@app.route("/confirm_donation")
@login_required
def confirm_donation():
    """We want to display the details of the transaction saved from previous page"""
    deets = db.session.query(User).get(session["userloggedin"])
    if session.get("trxno") == None: #means the are visiting here directly
        flash("Please complete this form",category="error")
        return redirect("/donate/")
    else:
        donation_deets = Donation.query.filter(Donation.don_refno==session["trxno"]).first()
        return render_template("user/donation_confirmation.html",donation_deets=donation_deets,deets=deets)



@app.route("/sendmail")
def send_email():
    file=open('requirement.txt')
    msg= Message(subject="Adding Heading to Email From BookWorm",sender="From BookWorm Website",recipients=["teniakintokunbo@gmail.com"],body="<h1>Thank you for contacting us</h1>")
    msg.html="""<h1>Welcome Home!</h1>
    <img src="https://images.pexels.com/photos/214574/pexels-photo-214574.jpeg?auto=compress&cs=tinysrgb&w=600"><hr>"""
    msg.attach("saved_as.txt","application/text",file.read())
    mail.send(msg)
    return "done"



# send mail
# @app.route("/sendmail")
# def send_mail():
#     msg = Message(subject="Testing Mail",recipients=["eshanwise@gmail.com"],body="Thank you for contacting us",sender="From Bookworm Website")
#     mail.send(msg)
#     return "done"



# myreviews route
@app.route("/ajaxopt/",methods=["GET",'POST'])
def ajax_options():
    cform=ContactForm()
    if request.method == 'GET':
        return render_template('user/ajax_options.html',cform=cform)
    else:
        email = request.form.get("email")
        return f"Thank you ,your email has been submitted {email}"

# myreviews route
@app.route("/myreviews")
def myreviews():
    id = session["userloggedin"]
    userdeets = db.session.query(User).get(id)
    return render_template('user/myreview.html',userdeets=userdeets)



@app.route('/submit_review/', methods=["POST"])
@login_required
def submit_review():
    title = request.form.get("title")
    content = request.form.get("content")
    userid = session['userloggedin']
    bookid = request.form.get("bookid")
    query = Reviews(rev_title=title,rev_text=content,rev_userid=userid,rev_bookid=bookid)
    db.session.add(query)
    db.session.commit()

    retstr = f"""<article class="blog-post">
        <h5 class="blog-post-title">{title}</h5>
        <p class="blog-post-meta">Reviewed by me <a href="#">{query.reviewby.user_fullname}</a></p>

        <p>{content}</p>
        <hr> 
      </article>"""
    return retstr



@app.route("/dependent/")
def dependent_dropdown():
    state = db.session.query(State).all()
    return render_template('user/show_states.html',state=state)

@app.route("/lga/<stateid>/")
def load_lgas(stateid):
    records = db.session.query(Lga).filter(Lga.state_id==stateid).all()
    str2return = "<select class='form-control mt-3' >"
    for r in records:
        optstr = "<option>" + r.lga_name + "</option>"
        str2return = str2return + optstr
    str2return=str2return + optstr + "</select>"

    return str2return

@app.route('/checkavailability/',methods=["POST","GET"])
def checkusername():
    email = request.args.get('email')
    chk =db.session.query(User).filter(User.user_email ==email).first()
    if chk:
        return "Email not available"
    else:
        return "Email available"


@app.route('/submission/')
def ajax_submission():

    user = request.args.get('fullname')
    if user != '' and user != None:
        return f"Thank you {user} for completing the form"
        """This route will be visited by ajax silentlty"""
    else:
        return "Please complete the form"
    

# ajax
@app.route('/contact/')
def ajax_contact():
    data = "I am a string coming from the data base"
    return render_template("user/ajax_text.html",data=data)


@app.route("/favourite/")
def favourite_topics():
    bootcamp = {"name": "Precious", "Topics": ["OOP", "CSS", "MVC"]}
    category = []
    cats = db.session.query(Category).all()
    for c in cats:
        category.append(c.cat_name)

        #or we use comprehension category=[c.cat_name for c in cats] 
        
    return json.dumps(category)



@app.route('/profile/',methods = ["POST","GET"])
@login_required
def edit_profile():
    id = session.get('userloggedin')
    userdeets = db.session.query(User).get(id)
    pform = ProfileForm()
    if request.method == "GET":
        return render_template('user/edit_profile.html',userdeets=userdeets,pform=pform)
    else:
        pform.validate_on_submit()
        userprofile = request.form.get('fullname')
        userdeets.user_fullname = userprofile
        db.session.commit()
        flash('Profile Updated')
        return redirect('/dashboard')



# profile pix
@app.route("/changedp/",methods=["POST","GET"])
@login_required
def changedp():
    id = session.get("userloggedin")
    userdeets = db.session.query(User).get(id)
    dpform =DpForm()
    if request.method == "GET":
        return render_template("user/changedp.html",dpform=dpform,userdeets=userdeets)
    else:#form is being submitted
        if dpform.validate_on_submit():
            pix = request.files.get('dp')
            filename = pix.filename
            pix.save(app.config['USER_PROFILE_PATH'] + filename)
            userdeets.user_pix = filename
            db.session.commit()
            flash('Profile Picture Updated',category='info')
            return redirect(url_for('dashboard'))
        else:
            return render_template("user/changedp.html", dpform=dpform,userdeets=userdeets)

@app.route("/viewall/")
def view_all():
    books = db.session.query(Book).filter(Book.book_status==1).all()
    return render_template("user/viewall.html",books=books)


@app.route("/dashboard")
def dashboard():
    if session.get("userloggedin") != None:
        id = session.get('userloggedin')
        userdeets = User.query.get(id)
        return render_template("user/dashboard.html",userdeets=userdeets)
    else:
        flash("You need to login o access this page")
        return redirect("/login")


# logout
@app.route("/logout")
def logout():
    if session.get("userloggedin")!=None:
        session.pop('userloggedin',None)
    return redirect('/login')

# login
@app.route("/login/", methods=["POST","GET"])
def login():
    if request.method == "GET":
        return render_template("user/loginpage.html")
    else:
        Email = request.form.get("email")
        pwd = request.form.get("pwd")
        deets = db.session.query(User).filter(User.user_email==Email).first()
        if deets != None:
            hashed_pwd = deets.user_pwd
            if check_password_hash(hashed_pwd,pwd) ==True:
                session['userloggedin']=deets.user_id
                return redirect("/dashboard")
            else:
                flash("Invalid credentials, try again")
                return redirect("/login")
        else:   
            flash("Invalid credentials, try again")
            return redirect("/login")

# Create account
@app.route("/register/", methods=["POST","GET"])
def register():
    regform = RegForm()
    if request.method == "GET":
        return render_template('user/signup.html', regform=regform)
    else:
        if regform.validate_on_submit():
            name = request.form.get("fullname")
            email = request.form.get("usermail")
            pwd = request.form.get("pwd")
            hash_pwd = generate_password_hash(pwd)
            send = User(user_fullname=name,user_email=email,user_pwd=hash_pwd)
            db.session.add(send)
            db.session.commit()
            flash("An account has been created for you. Please login",category='success')
            return redirect("/login")
        else:
            return render_template("user/signup.html",regform=regform)



# View book details
@app.route("/user/details/<id>")
def book_details(id):
    books = Book.query.get_or_404(id)
    return render_template("user/reviews.html", books=books)


# home page
@app.route("/")
def home_page():
    books = db.session.query(Book).filter(Book.book_status == '1').limit(4).all()
    # connect to the endpoint http://127.0.0.1:1995/api/v1.0/listall to collect data of book
    # pas it to th templates and display on the template
    try:
        response = requests.get('http://127.0.0.1:1995/api/v1.0/listall/')
        # import requests
        rsp = json.loads(response.text)#response.json
    except:
        rsp = None #if the server is unreacheable...
    return render_template("user/home_page.html",books=books,rsp=rsp)


@app.after_request
def after_request(response):
    # To solvem the problem of loggedout user's details being cached in the browser
    response.headers["cache-control"]="no-cache, no-store, must-validate"
    return response
