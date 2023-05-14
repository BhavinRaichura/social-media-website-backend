from flask import jsonify, redirect, request,Flask
#from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy

import jwt
import datetime

app = Flask(__name__)
app.app_context().push()
#cors = CORS(app, resources={r"/api/*": {"origins": "*"}})

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
                'following':self.followingAllDetails(),
                'post':self.posters(),
                'follower':self.followerAllDetails()}
    
    def basicDetails(self):
        return {
            'user_id':self.id, 
            'name':self.name, 
            'email':self.email,
            'image_url':self.image_url}
        
    
    def followingDetails(self):
        followings = [i.follow_id for i in self.follows]
        return followings
    
    def followerDetails(self):
        followers = Following.query.filter_by(follow_id = self.id)
        followerList = [i.user.id for i in followers]
        return followerList
    
    def followingAllDetails(self):
        
        followings = [i.follow.basicDetails() for i in self.follows]
        return followings
    
    def followerAllDetails(self):
        followers = Following.query.filter_by(follow_id = self.id)
        followerList = [i.user.basicDetails() for i in followers]
        return followerList
    
    def posters(self):
        posts =[i.details() for i in self.post]
        return posts
    
    def followRequest(self):
        print('\n\nrequest ---' )
        print(f'\n dekho {self.follow_req}')
        req = [i.req_by.basicDetails() for i in self.follow_req]
        print(req)
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
                'date':(str(self.date))[:16],
                'likes':len(liker),
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