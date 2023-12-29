from sqlalchemy import text


class TweetDao:
    def __init__(self, database) -> None:
        self.database = database

    def insert_tweet(self, user_id, tweet):
        return self.database.execute(
            text(
                """
insert into tweets (user_id, tweet) values(
    :user_id , :tweet
)
"""
            ),
            {"user_id": user_id, "tweet": tweet},
        ).rowcount

    def get_timeline(self, user_id):
        timeline = self.database.execute(
            text(
                """
select t.user_id, t.tweet
from tweets t 
left join users_follow_list ufl on ufl.user_id = :user_id
where t.user_id = :user_id
or t.user_id = ufl.follow_user_id
"""
            ),
            {"user_id": user_id},
        ).fetchall()

        return [
            {"user_id": tweet["user_id"], "tweet": tweet["tweet"]} for tweet in timeline
        ]
