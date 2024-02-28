from flask import Flask,render_template,request,url_for,flash,redirect,session,send_file
from flask_session import Session
import mysql.connector
from otp import genotp
from cmail import sendmail
import flask_excel as excel
from io import BytesIO
app=Flask(__name__)
app.config['SESSION_TYPE']='filesystem'
excel.init_excel(app)
Session(app)
# mydb=mysql.connector.connect(host="localhost",user="root",password="Sravya99@",db='prm')
app.secret_key='sravya99@codegnan'
user=os.environ.get('RDS_USERNAME')
db=os.environ.get('RDS_DB_NAME')
password=os.environ.get('RDS_PASSWORD')
host=os.environ.get('RDS_HOSTNAME')
port=os.environ.get('RDS_PORT')
with mysql.connector.connect(host=host,port=port,user=user,password=password,db=db) as conn:
    cursor=conn.cursor()
    cursor.execute('create table if not exists register(username varchar(50) NOT NULL,password varchar(15) DEFAULT NULL,email varchar(60) DEFAULT NULL,PRIMARY KEY (username),UNIQUE KEY email (email))')
    cursor.execute('create table if not exists notes(notes_id int NOT NULL AUTO_INCREMENT,title varchar(100) NOT NULL,content text NOT NULL,username varchar(50) NOT NULL,PRIMARY KEY (notes_id), KEY username (username),FOREIGN KEY (username) REFERENCES register (username))')
    cursor.execute('create table if not exists files files` (fid int NOT NULL AUTO_INCREMENT,extension varchar(10) DEFAULT NULL,filedata longblob,added_by varchar(50) DEFAULT NULL,PRIMARY KEY (fid),KEY added_by (added_by),CONSTRAINT files_ibfk_1 FOREIGN KEY (added_by) REFERENCES register (username))')
mydb=mysql.connector.connect(host=host,port=port,user=user,password=password,db=db)
@app.route('/')
def home():
     return render_template('title.html')
@app.route('/register',methods=['GET','POST'])
def register():
    if request.method=='POST':
        print(request.form)
        username=request.form['username']
        email=request.form['email']
        phonenumber=request.form['number']
        password=request.form['password']
        confirm=request.form['confirm']
        cursor=mydb.cursor(buffered=True)
        cursor.execute('select count(*) from register where username=%s',[username])
        count=cursor.fetchone()[0]
        cursor.execute('select count(*) from register where email=%s',[email])
        count2=cursor.fetchone()[0]
        cursor.close()
        print(count)
        print(count2)
        if count==0:
            if count2==0:
                otp=genotp()
                subject='Thanks for resgistering'
                body=f'use this otp register {otp}'
                sendmail(email,subject,body)
                flash('The otp has sent to your mail please verify it')
                return render_template('otp.html',username=username,password=password,email=email,otp=otp)
            else:
                flash('email already existed')
                return render_template('register.html')
        else:
            flash('username already existed')
            return render_template('register.html')
    return render_template('register.html')
@app.route('/otp/<username>/<password>/<email>/<otp>',methods=['GET','POST'])
def otp(username,password,email,otp):
    if request.method=='POST':
        otp1=request.form['otp']
        if otp==otp1:
            cursor=mydb.cursor(buffered=True)
            cursor.execute('insert into register(username,password,email) values(%s,%s,%s)',[username,password,email])
            mydb.commit()
            cursor.close()
            flash('Registration successfully done')
            return redirect(url_for('login'))
        else:
            return redirect(url_for('otp'))
    return render_template('otp.html')
@app.route('/login',methods=['GET','POST'])
def login():
    if session.get('user'):
        return redirect(url_for('homepage'))
    if request.method=='POST':
        username=request.form['username']
        password=request.form['password']
        cursor=mydb.cursor(buffered=True)
        cursor.execute('select count(*)  from register where username=%s and password=%s',[username,password])
        var1=cursor.fetchone()[0]
        cursor.close()
        if var1==1:
            session['user']=username
            return redirect(url_for('homepage'))
        else:
            return 'username or password was incorrect'
        
    return render_template('login.html')
@app.route('/logout')
def logout():
    if session.get('user'):
        session.pop('user')
        return redirect(url_for('login'))
    else:
        return redirect(url_for('login'))
@app.route('/homepage')
def homepage():
    if session.get('user'):
        return render_template('homepage.html')
    else:
        return redirect(url_for('index'))
@app.route('/addnotes',methods=['GET','POST'])
def addnote():
    if session.get('user'):
        if request.method=='POST':
            title=request.form['title']
            content=request.form['content']
            user=session.get('user')
            cursor=mydb.cursor(buffered=True)
            cursor.execute('insert into notes(title,content,username) values(%s,%s,%s)',[title,content,user])
            mydb.commit()
            cursor.close()
            flash('notes has been inserted successfully')
            return redirect(url_for('homepage'))
        return render_template('addnotes.html')
    return redirect(url_for('login'))
@app.route('/allnotes')
def allnotes():
    if session.get('user'):
        cursor=mydb.cursor(buffered=True)
        cursor.execute('select notes_id,title from notes where username=%s',[session.get('user')])
        data=cursor.fetchall()
        cursor.close()
        return render_template('table.html',data=data)
    return redirect(url_for('login'))
@app.route('/viewnotes/<notesid>')
def viewnotes(notesid):
    if session.get('user'):     
        cursor=mydb.cursor(buffered=True)
        cursor.execute('select title,content from notes where notes_id=%s',[notesid])
        data1=cursor.fetchall()
        cursor.close()
        return render_template('viewnotes.html',data1=data1)
    return redirect(url_for('login'))
@app.route('/update/<notesid>',methods=['GET','POST'])
def update(notesid):
    if session.get('user'):
        cursor=mydb.cursor(buffered=True)
        cursor.execute('select title,content from notes where notes_id=%s',[notesid])
        var1=cursor.fetchall()
        cursor.close()
        if request.method=='POST':
            title=request.form['title']
            content=request.form['content']
            cursor=mydb.cursor(buffered=True)
            cursor.execute('update notes set title=%s,content=%s where notes_id=%s',[title,content,notesid])
            mydb.commit()
            cursor.close()
            flash(f'notes with id {notesid} update successfully ')
            return redirect(url_for('allnotes'))
        return render_template('update.html',var1=var1)
    return redirect(url_for('login'))
@app.route('/delete/<notesid>')
def delete(notesid):
    if session.get('user'):
        cursor=mydb.cursor(buffered=True)
        cursor.execute('delete from notes where notes_id=%s',[notesid])
        mydb.commit()
        cursor.close()
        return redirect(url_for('allnotes'))
    return redirect(url_for('login'))
@app.route('/search',methods=['GET','POST'])
def search():
    if session.get('user'):
        if request.method=='POST':
            name=request.form['search']
            strg=['A-Za-z0-9']
            pattern=re.compile(f'^{strg}', re.IGNORECASE)
            if (pattern.match(name)):
                cursor=mydb.cursor(buffered=True)
                cursor.execute('select notes_id,title from notes where username=%s and title LIKE %s', [session.get('user'),name + '%'])
                data=cursor.fetchall()
                cursor.close()
                return render_template('homepage.html', items=data)
            else:
                flash('result not found')
                return redirect(url_for('homepage'))
    return redirect(url_for('login'))
@app.route('/gennotesdata')
def getdata():
    if session.get('user'):
        username=session.get('user')
        cursor=mydb.cursor(buffered=True)
        columns=['Title','Content']
        cursor.execute('select title,content from notes where username=%s',[username])
        data=cursor.fetchall()
        cursor.close()
        print(data)
        array_data=[list(i) for i in data]
        print(array_data)
        array_data.insert(0,columns)
        print(array_data)
        return excel.make_response_from_array(array_data,'xlsx',filename='getnotesdata')
    else:
        return redirect(url_for('login'))
@app.route('/fileup',methods=['GET','POST'])
def fileupload():
    if session.get('user'):
        if request.method=='POST':
            files=request.files.getlist('file')
            username=session.get('user')
            cursor=mydb.cursor(buffered=True)
            for file in files:
                file_ext=file.filename.split('.')[-1]
                file_data=file.read()
                cursor.execute('insert into files(extension,filedata,added_by) values(%s,%s,%s)',[file_ext,file_data,username])
                mydb.commit()
            cursor.close()
            flash('files upload successfully')
            return redirect(url_for('homepage'))
        return render_template('fileupload.html')
    else:
        return redirect(url_for('login'))
@app.route('/allfiles')
def allfiles():
    if session.get('user'):
        cursor=mydb.cursor(buffered=True)
        cursor.execute('select fid from files where added_by=%s',[session.get('user')])
        data=cursor.fetchall()

        cursor.close()
        return render_template('fileview.html',data=data)
    else:
        return redirect(url_for('login'))
@app.route('/viewfile/<fid>')
def viewfile(fid):
    if session.get('user'):
        cursor=mydb.cursor(buffered=True)
        cursor.execute('select extension,filedata from files where fid=%s',[fid])
        ext,bin_data=cursor.fetchone()
        bytes_data=BytesIO(bin_data)
        filename=f'attachment.{ext}'
        return send_file(bytes_data,download_name=filename,as_attachment=False)
    else:
        return redirect(url_for('login'))
@app.route('/downloadfile/<fid>')
def downloadfile(fid):
    if session.get('user'):
        cursor=mydb.cursor(buffered=True)
        cursor.execute('select extension,filedata from files where fid=%s',[fid])
        ext,bin_data=cursor.fetchone()
        bytes_data=BytesIO(bin_data)
        filename=f'attachment.{ext}'
        return send_file(bytes_data,download_name=filename,as_attachment=True)
    else:
        return redirect(url_for('login'))
@app.route('/delete_file/<fid>')
def delete_file(fid):
    if session.get('user'):
        cursor=mydb.cursor(buffered=True)
        cursor.execute('delete from files where fid=%s',[fid])
        mydb.commit()
        cursor.close()
        return redirect(url_for('allfiles'))
    return redirect(url_for('login'))
if __name__ == '__main__':
    app.run()