from sqlalchemy import text


class UserDao:
    def __init__(self, database) -> None:
        self.database = database

    def insert_user(self, user: dict):
        return self.database.execute(
            text(
                """
insert into users (email, name, hashed_password, profile)
values(:email, :name, :password, :profile)
"""
            ),
            user,
        ).lastrowid
    
    def get_user_by_user_id(self, user_id):
        user = self.database.execute(text("""
select id, email, name, profile from users
where id = :user_id
"""), {'user_id': user_id}).fetchone()
        
        return {'id' : user['id'], 'email': user['email'], 'name': user['name'], 'profile' : user['profile']} if user else None


    def get_user_id_and_password(self, email: str):
        row = self.database.execute(
            text(
                """
select id, hashed_password from users
where email = :email
"""
            ),
            {"email": email},
        ).fetchone()

        return (
            {"id": row["id"], "hashed_password": row["hashed_password"]}
            if row
            else None
        )

    def insert_follow(self, user_id, followee):
        return self.database.execute(
            text(
                """
insert into users_follow_list (user_id, follow_user_id)
values (:user_id, :follow_user_id)
"""
            ),
            {"user_id": user_id, "follow_user_id": followee},
        ).rowcount

    def delete_follow(self, user_id, followee):
        return self.database.execute(
            text(
                """
delete from users_follow_list
where user_id = :user_id and follow_user_id = :follow_user_id
"""
            ),
            {"user_id": user_id, "follow_user_id": followee},
        ).rowcount
