from flask import request,jsonify
from model import app, db,User
import jwt


def isAuthenticated(fn):
    def wrapper(*args, **kwargs):
        token = None
        print('execute')
        if 'token' in request.headers:
            header= dict(request.headers)
            print('\n\n---------token------------\n\n')
            print(header['Token'])
            token=header['Token']
        if not token:
            return jsonify({'message':'Token is messing'}),401
        #try:
        data = jwt.decode(token, app.config['SECRET_KEY'], algorithms='HS256')
        print('data ', data)
        current_user = User.query.filter_by(id = data['user_id']).first()
        if(current_user):
            return fn(current_user, *args, **kwargs)
        else:
            return jsonify({'message':'user not found !!'}),401
        #except:
        #    return jsonify({'message':'token is invalid !!'}),401
    wrapper.__name__ = fn.__name__
    return wrapper