import bcrypt
import jwt
from datetime import datetime, timedelta

class UserService:
    def __init__(self, user_dao, config) -> None:
        self.user_dao = user_dao
        self.config = config

    def create_new_user(self, new_user: dict):
        new_user["password"] = bcrypt.hashpw(
            new_user["password"].encode("utf-8"), bcrypt.gensalt()
        )

        new_user_id = self.user_dao.insert_user(new_user)

        return new_user_id
    
    def login(self, credential):
        email = credential['email']
        password = credential['password']
        user_credential = self.user_dao.get_user_id_and_password(email)

        authorized : bool = user_credential and \
            bcrypt.checkpw(password.encode('UTF-8'), user_credential['hashed_password'].encode('UTF-8'))
        
        return authorized

    def generate_access_token(self, user_id):
        payload = {
            'user_id': user_id,
            'exp': datetime.utcnow() + timedelta(seconds=60 * 60 * 12)
        }
        token = jwt.encode(payload, self.config['JWT_SECRET_KEY'], 'HS256')

        return token
    
    def follow(self, user_id, followee):
        return self.user_dao.insert_follow(user_id, followee)
    

    def unfollow(self, user_id, followee):
        return self.user_dao.delete_follow(user_id, followee)