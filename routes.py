from flask import jsonify, redirect, request
from model import app, db, User,Following,follow_requests,Poster,Comment
from auth import isAuthenticated
from flask_cors import CORS
from sqlalchemy.sql import text, desc
import jwt

cors = CORS(app, resources={r"/*": {"origins": "*"}})
# api -1 


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
            #print('exist ',user)
            token = gettoken(user.id)
            return jsonify({'email':email, 'userid':user.id, 'status':1, 'authtoken':token})
        
        user = User(name=name,email=email, image_url = image)
        db.session.add(user)
        db.session.commit()
        #print(user)
        token = gettoken(user.id)
        return jsonify({'email':email, 'userid':user.id, 'status':1,'authtoken':token})
    return jsonify({'status':0,'message':'insufficient data'})

# api -2
@app.route('/api/user/public/profile/<int:id>')
def public_profile(id):
    user = User.query.filter_by(id= id).first()
    if user: 
        return jsonify({'status':1, 'userDetails' : user.basicDetails() })
    return  jsonify({'status':0, 'meessage':'user not found'})

# api -3
@app.route('/api/user/private/profile/<int:id>')
@isAuthenticated
def private_details(client, id):
    follows = User.query.filter_by(id= id).first()
    if follows:
        if follows.id == client.id:
            return jsonify({'status':1, 'userDetails' :  client.profile(), 'isUser':1, 'isFollowing':0, 'reqStatus':0})
        following_obj  = Following.query.filter_by(user = client).filter_by(follow = follows).first()
        if following_obj: 
            details = follows.profile()
            details['isFollowing'] = 1
            return jsonify({'status':1, 'userDetails' :  details, 'isFollowing':1, 'reqStatus':0 ,'isUser':0})
        req_obj = follow_requests.query.filter_by(req_by=client).filter_by(req_to=follows).first()
        if req_obj:
            return  jsonify({'status':1, 'meessage':f"{client.name} doesn't follows {follows.name}" ,'userDetails':follows.profile(), 'isFollowing':0, 'reqStatus':1,'isUser':0})
        return  jsonify({'status':1, 'meessage':f"{client.name} doesn't follows {follows.name}" ,'userDetails':follows.profile(), 'isFollowing':0, 'reqStatus':0,'isUser':0})
    return jsonify({'status':0, 'meessage':'user not found'})

@app.route('/api/user/show-follow-requests')
@isAuthenticated
def showFollowRequests(client):
    list_of_resquests = client.followRequest()
    print('resuest by user ')
    print(list_of_resquests)
    return jsonify({'status':1,'results':list_of_resquests})
    #return {'results':1}
    

# api -10
@app.route('/api/user/request-to-follow/<int:id>')
@isAuthenticated
def connection_request(client,id):
    user2 = User.query.filter_by(id=id).first()
    if(user2):
        if(Following.query.filter_by(user=client).filter_by(follow=user2).first() or
           follow_requests.query.filter_by(req_by=client).filter_by(req_to=user2).first()):
            return jsonify({'status':0, 'message':'user is already have connection'})
        req = follow_requests(req_by = client, req_to=user2)
        db.session.add(req)
        db.session.commit()
        return jsonify({'status':1,'message':'request successfully'})
    return jsonify({'status':0,'message':'invalid user details'})

#api -11
@app.route('/api/user/follow-requests-accept/<int:id>')
@isAuthenticated
def followRequestsAccept(client,id):
    user2= User.query.filter_by(id=id).first()
    if user2:
        dq = follow_requests.query.filter_by(req_by=user2).filter_by(req_to=client).first()
        if dq:
            aq = Following(user = user2, follow = client)
            db.session.add(aq)
            db.session.delete(dq)
            db.session.commit()
            return jsonify({'status':1})
        return jsonify({'status':0,'message':f'request not found from id: {id}'})
    return jsonify({'status':0,'message':'invalid user id..!'})

#api -12
@app.route('/api/user/follow-requests-delete/<int:id>')
@isAuthenticated
def followRequestsDelete(client,id):
    user2= User.query.filter_by(id=id).first()
    if user2:
        dq = follow_requests.query.filter_by(req_by=client).filter_by(req_to=user2).first()
        if dq:
            db.session.delete(dq)
            db.session.commit()
            return jsonify({'status':1})
        #except
        #db.session.rollback()
        return jsonify({'status':0,'message':f'request not found from id: {id}'})
    return jsonify({'status':0,'message':'invalid user id..!'})

@app.route('/api/user/unfollow/<int:id>')
@isAuthenticated
def unfollow(client,id):
    follow_to = User.query.filter_by(id=id).first() 
    if follow_to:
        follow_obj = Following.query.filter_by(user = client).filter_by(follow = follow_to).first()
        if follow_obj:
            db.session.delete(follow_obj)
            db.session.commit()
            return jsonify({'status':1})
        return jsonify({'status':0,'message':f'{client.name} already not follows {follow_to.name}'})
    return jsonify({'status':0,'message':'following id is invalid'})

@app.route('/api/poster/<int:postid>')
def getPosterDetails(postid):
    poster = Poster.query.filter_by(id=postid).first()
    if(poster):
        return jsonify({'status':1,'results':poster.details()})
    return jsonify({'status':0, 'message':'invalid post id..!'})

@app.route('/api/poster/create',methods=['GET','POST'])
@isAuthenticated
def createPost(client):
    if request.method == 'GET':
        desc = request.args.get('desc')
        image = "None" #request.args.get('imageurl')
        newpost = Poster(desc = desc, image = image, user = client)
        db.session.add(newpost)
        db.session.commit()
        return jsonify({'status':1,'results':newpost.details()})
    return jsonify({'status':0})

@app.route('/api/poster/like/<int:postid>')
@isAuthenticated
def likePost(client,postid):
    poster = Poster.query.filter_by(id=postid).first()
    if poster:
        if client in poster.likes:
            poster.likes.pop(poster.likes.index(client))
            db.session.commit()
            return jsonify({'status':1,'results':poster.details(),'isUserLike':0})
        poster.likes.append(client)
        db.session.commit()
        return jsonify({'status':1,'results':poster.details(),'isUserLike':1})
    return jsonify({'status':0})  

@app.route('/api/poster/comment/<int:postid>',methods=['GET','POST'])
@isAuthenticated
def commentPost(client,postid):
    if request.method=='GET':
        desc = request.args.get('desc')
        poster = Poster.query.filter_by(id=postid).first()
        if poster:  
            cmt = Comment(desc = desc, user = client)
            poster.comments.append(cmt)
            db.session.commit()
            return jsonify({'status':1,'results':poster.details()})
        return jsonify({'status':0,'message':'post not found'})
    return jsonify({'status':0, 'message':'invalid request method..!'})  

@app.route('/api/poster/delete/<int:postid>')
@isAuthenticated
def deletePost(client, postid):
    poster = Poster.query.filter_by(id=postid).first()
    if poster and poster.user.id == client.id:
        db.session.delete(poster)
        db.session.commit()
        return jsonify({'status':1,'results':client.posters()})
    return jsonify({'status':0,'message':"user don't have access to delete the post"})
        

@app.route('/api/search/<string:substr>')
def search(substr):
    filter_by_name = User.query.filter(User.name.like(f"%{substr}%")).all()
    filted_ids = [i.id for i in filter_by_name]
    filter_by_email = User.query.filter(User.email.like(f"%{substr}%")).filter(User.id.notin_(filted_ids)).all()
    results = [person.basicDetails() for person in filter_by_name] + [person.basicDetails() for person in filter_by_email]
    return jsonify({'status':1,'results':results})

# api - not completed
@app.route('/api/user/timeline')
@isAuthenticated
def timeline(client):
    followings = client.followingDetails()
    postList = Poster.query.filter(Poster.posted_by.in_(followings)).all()
    results = []
    for i in postList:
        details = i.details()
        details['posted_by']['following'] = False
        if details['posted_by']['user_id'] in followings:
            details['posted_by']['following'] = True
        results.append(details)
    return jsonify({'status':1,'results':results})

@app.route('/api/suggetion')
@isAuthenticated
def suggetions(client):
    followings = client.followingDetails()
    followings.append(client.id)
    print('following ',followings)
    alreadyRequested = follow_requests.query.filter_by(req_by=client).all()
    reqIds = [i.req_to_id for i in alreadyRequested]
    usersobj = User.query.filter(User.id.notin_(followings)).all()
    results = [ ]
    for i in usersobj:
        data = i.basicDetails()
        if i.id in reqIds: 
            data['reqStatus'] = 1
        else: 
            data['reqStatus'] = 0
        
        results.append(data)
    return jsonify({'status':1,'results': results})
    
        
    
if __name__=="__main__":
    app.run(debug=True)
        
    
    
