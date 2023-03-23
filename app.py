from flask import Flask,jsonify,request
from flask_sqlalchemy import SQLAlchemy
import datetime
import jwt
from flask_cors import CORS
#import auth 

app = Flask(__name__)
app.app_context().push()
cors = CORS(app, resources={r"/api/*": {"origins": "*"}})

app.config['SQLALCHEMY_DATABASE_URI']='sqlite:///db.sqlite3'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS']=False
app.config['SECRET_KEY']  = 'jashdjlknk287e89hdTYH8&@RtfgHBNLu8pomxfqm7t676328hd'

db = SQLAlchemy(app)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(50),unique =True)
    name = db.Column(db.String(50))
    image_url = db.Column(db.String)
    private = db.Column(db.Boolean,unique=False, default=False)
    post = db.relationship('Poster',foreign_keys="Poster.posted_by", back_populates = 'user')
    follows = db.relationship('Following', foreign_keys="Following.user_id" ,back_populates="user")
    follow_req = db.relationship('follow_requests',foreign_keys="follow_requests.req_to_id",back_populates='req_to')
    comments =  db.relationship('Comment',foreign_keys='Comment.comment_by',back_populates ='user')
    
    def profile(self):
        return {'user_id':self.id, 
                'name':self.name, 
                'email':self.email,
                'image_url':self.image_url, 
                'following':self.followingDetails(),
                'post':self.posters(),
                'follower':self.followerDetails()}
    
    def basicDetails(self):
        return {
            'user_id':self.id, 
            'name':self.name, 
            'email':self.email,
            'image_url':self.image_url}
        
    
    def followingDetails(self):
        followings = [i.id for i in self.follows]
        return followings
    
    def followerDetails(self):
        followers = Following.query.filter_by(follow_id = self.id)
        followerList = [i.user.id for i in followers]
        return followerList
    
    def posters(self):
        posts =[i.details() for i in self.post]
        return posts
    
    def followRequest(self):
        req = [i.basicDetails() for i in self.follow_req]
        return req
        
    
    
class Following(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    follow_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    user = db.relationship('User',foreign_keys=user_id,back_populates="follows")
    follow = db.relationship('User',foreign_keys=follow_id)
    
    def details(self):
        return self.follow.basicDetails()

    
class follow_requests(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    req_by_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    req_to_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    req_by = db.relationship('User',foreign_keys=req_by_id)
    req_to = db.relationship('User',foreign_keys=req_to_id,back_populates='follow_req')
    
    def details(self):
        return self.req_by.basicDetails()
    


post_comment = db.Table('post_comment',
                        db.Column('post_id',db.Integer,db.ForeignKey('poster.id')),
                        db.Column('comment_id',db.Integer,db.ForeignKey('comment.id'))
    )

post_like = db.Table('post_like',
                    db.Column('post_id',db.Integer,db.ForeignKey('poster.id')),
                    db.Column('user_id',db.Integer,db.ForeignKey('user.id'))
    )

class Poster(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    desc = db.Column(db.String(2000),nullable=True)
    image = db.Column(db.String,nullable=True)
    posted_by = db.Column(db.Integer,db.ForeignKey('user.id'))
    date = db.Column(db.Date,default=datetime.date.today())
    comments = db.relationship('Comment',secondary=post_comment,backref="post")
    likes = db.relationship('User',secondary=post_like,backref="like_post")
    user = db.relationship('User',foreign_keys=posted_by,back_populates="post")
    
    def details(self):
        liker = self.likeDetails()
        return {'post_id':self.id, 
                'desc':self.desc,
                'image':self.image,
                'posted_by':self.user.basicDetails(),
                'date':self.date,'likes':len(liker),
                'Like_by':liker,
                'comments':self.commentDetails()}
    
    def likeDetails(self):
        likes =[i.basicDetails() for i in self.likes]
        return likes
    
    def commentDetails(self):
        comment_details =[i.details() for i in self.comments ]
        return comment_details


class Comment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    desc = db.Column(db.String(500))
    date = db.Column(db.Date,default=datetime.date.today())
    comment_by = db.Column(db.Integer,db.ForeignKey('user.id'))
    user = db.relationship('User',back_populates="comments")
    
    def details(self):
        return {
            'comment_id':self.id, 
            'body':self.desc,
            'comment_by':self.user.basicDetails(),
            'date':self.date}
    
    
def isAuthenticated(fn):
    def wrapper(*args, **kwargs):
        token = None
        #print('execute')
        if 'token' in request.headers:
            header= dict(request.headers)
            #print('\n\n---------token------------\n\n')
            #print(header['Token'])
            token=header['Token']
        if not token:
            return jsonify({'message':'Token is messing'}),401
        #try:
        data = jwt.decode(token, app.config['SECRET_KEY'], algorithms='HS256')
        print('data ', data)
        current_user = User.query.filter_by(id = int(data['user_id'])).first()
        print(current_user)
        if(current_user):
            return fn(current_user, *args, **kwargs)
        else:
            return jsonify({'message':'user not found !!'}),401
        #except:
        #    return jsonify({'message':'token is invalid !!'}),401
    wrapper.__name__ = fn.__name__
    return wrapper
    
#def gettoken(id):
#    token = jwt.encode({'user_id':id},app.config['SECRET_KEY'],algorithm='HS256')
#    return token
       
@app.route('/api/suggetions')
@isAuthenticated
def suggetions(user):
    print('\n\n',user.followingDetails())
    req = db.session.query(User).filter(User.id.notin_(user.followingDetails()))
    print(type(req))
    return jsonify({'req':'req'}) 
    
@app.route('/')
def home():
    return "home"


    
@app.route('/api/user/profile/<int:id>')
def get_user_profile(id):
    print(request.headers.__getitem__)
    u1 = User.query.filter_by(id=id).first()
    response =jsonify({'details':u1.profile()})
    response.headers.add('Access-Control-Allow-Origin', '*')
    print(u1)
    return response

@app.route('/follower/<int:id>')
def get_followers(id):
    u1 = User.query.filter_by(id=id).first()
    return jsonify({'details':u1.followers()})

@app.route('/post/<int:id>')
def get_post(id):
    post = Poster.query.filter_by(id=id).first()
    return jsonify({'details':post.details()})

@app.route('/post')
def get_post_list():
    post = Poster.query.all()
    post_dtl =[]
    for i in post:
        post_dtl.append(i.details())
    return post_dtl

@app.route('/user')
def get_user():
    user = User.query.all()
    user_lis=[]
    for i in user:
        user_lis.append(i.basicDetails())
    return jsonify({'details':user_lis})

@app.route('/user/<int:id>/request')
def follow_req_list(id):
    user = User.query.filter_by(id=id).first()
    return {"requested_by":user.followRequest()}

@app.route('/api/user/timeline',methods=['GET','POST'])
@isAuthenticated
def user_timeline(user):
    postList = Poster.query.all()
    results = [i.details() for i in postList]
    print("posters  ",results)
    return jsonify({'status':1,'results':results})
    

@app.route('/api/login',methods=['GET','POST'])
def login():
    if request.method=='GET':
        email = request.args.get('email')
        image = request.args.get('image')
        name = request.args.get('name')

        user = User.query.filter_by(email = email).first()
        
        def gettoken(id):
            token = jwt.encode({'user_id':id},app.config['SECRET_KEY'],algorithm='HS256')
            return token
        
        if(user):
            print('exist ',user)
            token = gettoken(user.id)
            return jsonify({'email':email, 'userid':user.id, 'status':1, 'authtoken':token})
        
        user = User(name=name,email=email, image_url = image)
        db.session.add(user)
        db.session.commit()
        print(user)
        token = gettoken(user.id)
        return jsonify({'email':email, 'userid':user.id, 'status':1,'authtoken':token})
    return jsonify({'status':0,'message':'insufficient data'})


if __name__ =="__main__":
    app.run(debug=True,port=5000)
    
    
# u1 = User(email="bhavin123@gmail.com",name= "Bhavin",image_url="u1.jpg")
# u2 = User(email="sonu123@gmail.com",name= "sonu",image_url="u2.jpg")
# from app import db, User, Following,Poster, Comment
# p1.likes.append(u2)


### follow request
# from app import follow_requests
# r1 = follow_requests(req_by=u1,req_to=u2)
# db.session.add(r1)
# db.session.commit()
# u2.follow_req
#
### make friend
# f1 = Following(user = u2,follow=u1)
# db.session.add(f1)
# db.session.commit()
#
### query add comment
# c2 = Comment(desc="c2 c2",comment_by=u2.id)
# p1.comments.append(c2)
# db.session.add(c2)
# db.session.commit()
#
### filter
# u1.post[0].comments
# u1.post[0].likes
# User.query.filter_by(id = u1.post[0].comments[0].comment_by).first().name