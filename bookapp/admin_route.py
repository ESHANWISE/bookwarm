import random,os,string
from flask import render_template,request,abort,redirect,flash,make_response,session,url_for

# local imports follows below
from bookapp import app,csrf
from bookapp.models import db,Admin,Book,Category
from bookapp.forms import *

# re.sub("pattern","replacement", string, count_replacement)
# to replace space with _: re.sub(" ","_",filename)

# patter = pattern to be replaced
# replacement = what to replace with
# string = file peth or where action will take place


def generate_string(howmany):#call this function as renerate_string(10)
    x = random.sample(string.ascii_lowercase,howmany)
    return ''.join(x)


# Edit books
@app.route("/admin/edit/<int:id>/", methods=["POST","GET"])
def edit_books(id):
    if session.get("adminuser") == None or session.get("role") != "admin":#means he is not logged in
        return redirect(url_for("admin_login"))
    else:
        if request.method == "GET":
            edit = db.session.query(Book).get_or_404(id)
            cats = db.session.query(Category).all()
    # or  edit = db.session.query(Book).filter(Book.book_id==id).first_or_404()
            return render_template("/admin/edit_book.html",edit=edit,cats=cats)
        else:
            book_2update =Book.query.get(id)
            current_filename = book_2update.book_cover
            # Retriev form data here ...

            # you should do validations for each of these fields before sending to db
            book_2update.book_title = request.form.get("title")
            book_2update.book_category = request.form.get("category")
            book_2update.book_status = request.form.get("status")
            book_2update.book_desc = request.form.get("description")
            book_2update.book_publication = request.form.get("yearpub")
            # check if file was selected for upload

            
            cover = request.files.get("cover")
            if cover.filename != "":
                # let the file name remain the same on the db
                name,ext = os.path.splitext(cover.filename)
                if ext.lower() in ['.jpg','.png','.jpeg']:
                    newfilename = generate_string(10) + ext
                    cover.save("bookapp/static/uploads/" + newfilename)
                    book_2update.book_cover = newfilename
                else:
                    flash("The extension of the book cover wasn't included")
            db.session.commit()
            flash("Book details was updated")
            return redirect('/admin/books')

@app.route('/admin/display/<id>/')
def display(id):
    display = db.session.query(Book).filter(Book.book_cover).get(id)
    return render_template("admin/allbooks.html",display=display)

# delete book
@app.route("/admin/delete/<id>/")
def book_delete(id):
    book = db.session.query(Book).get_or_404(id)
    # lets get the name of the file attached to this book
    filename = book.book_cover
    # first delet the file before deleting the book becaues
    #  if reverse is the case, we wont know the file name that the book cover was deleted from
    if filename != None and filename != 'default.png' and os.path.isfile("bookapp/static/uploads/"):
        os.remove("bookapp/static/uploads/" + filename)#import os at the top
    # To delete
    db.session.delete(book)
    db.session.commit()
    flash("Book has been deleted!")
    return redirect(url_for('all_books'))


# All books route
@app.route("/admin/addbook/",methods=["POST","GET"])
def addbook():
    if session.get("adminuser") == None or session.get("role") != "admin":#means he is not logged in
        return redirect(url_for("admin_login"))
    else:
        if request.method == "GET":
            cats = db.session.query(Category).all()
            return render_template("admin/addbook.html",cats=cats)
        else:
             # retrieve files
            allowed = ["jpg","png"]
            filesobj = request.files['cover']
            filename= filesobj.filename
            newname = "default.png"#this is the default  cover 
            # here we are checking if the user did not upload any image in the fields. the chk is on file name is on filaname because if there is a file there must be a name
            if filename == '':#No file was uploaded
                flash("Book cover not included",category="error")
            else:#file was selected
                pieces =filename.split('.')
                exist = pieces[-1].lower()
                if exist in allowed:
                    newname = str(int(random.random()*10000000000)) +filename#this is to help us make the image name as unique as possible to avoid clash of names
                    filesobj.save("bookapp/static/uploads/" + newname)
                else:
                    flash("File extention type not allowed, file was not uploaded", category='error')
# if we was to make book cover compulsory we will just pput a redirect back to the addbook page and drop a flash messsage to tell them to upload a file
            
           
            title = request.form.get("title")
            category = request.form.get("category")
            status = request.form.get("status")
            description = request.form.get("description")
            yearpub = request.form.get("yearpub")   
            # insert into db
            bk = Book(book_title=title,book_desc=description,book_publication=yearpub,book_catid=category,book_status=status,book_cover=newname)
            db.session.add(bk)
            db.session.commit()
            if bk.book_id:
                flash("Book has been addded")
            else:
                flash("Please try again")
    
    return redirect(url_for('all_books'))


# All books route
@app.route("/admin/books/")
def all_books():
    if session.get("adminuser") == None or session.get("role") != "admin":#means he is not logged in
        return redirect(url_for("admin_login"))
    else:
        books = db.session.query(Book).all()# or you use Book.Query.all()
        return render_template("admin/allbooks.html",books=books)


# login validation so that people wont just visit the admin dashboard directly
@app.route("/admin/")
def admin_page():
    if session.get("adminuser") == None or session.get("role") != "admin":#means he is not logged in
        return render_template("admin/login.html")
    else:
        return redirect(url_for("admin_dashboard"))
    
# login
@app.route("/admin/login/",methods=["POST","GET"])
def admin_login():
    if request.method == "GET":
        return render_template("admin/login.html")
    else:
        # retrieve infor from admin login form
        username= request.form.get("username")
        pwd = request.form.get("pwd")
        # check if it is in db
        check = db.session.query(Admin).filter(Admin.admin_username==username,Admin.admin_pwd==pwd).first()
        # if it is in db save in session and redirect to dashboard
        if check:#it is in db,save session
            session['adminuser']=check.admin_id
            session['role']='admin'
            return redirect(url_for('admin_dashboard'))
        else:#if not, save message in flash,redirect back to login again
            flash('Invalid Login Details',category='error')
            return redirect(url_for("admin_login"))

# logout
@app.route("/admin/logout")
def admin_logout():
    if session.get("adminuser") != None: #he is still logged in
        session.pop("adminuser",None)
        session.pop("role",None)
        flash("You have been logged out", category="info")
        return redirect(url_for("admin_login"))
    else:#she is logged out already
        return redirect(url_for("admin_login"))

#   dashboard
@app.route("/admin/dasboard")
def admin_dashboard():
    if session.get("adminuser") == None or session.get("role") != "admin":#means he is not logged in
        return redirect(url_for("admin_login"))
    else:
        return render_template("admin/dashboard.html")
      


@app.after_request
def after_request(response):
    # To solvem the problem of loggedout user's details being cached in the browser
    response.headers["cache-control"]="no-cache, no-store, must-validate"
    return response
