class User:
    def __init__(self, fullname, nickname, email, about):
        self.fullname = fullname
        self.nickname = nickname
        self.email = email
        self.about = about

    def query_create_user(self):
        return "INSERT INTO users (nickname, fullname, email, about) " \
               "VALUES ('{}', '{}', '{}', '{}')". \
            format(
            self.nickname, self.fullname, self.email, self.about
        )

    def query_get_same_users(self):
        return "SELECT nickname, fullname, email, about " \
               "FROM users " \
               "WHERE nickname = '{}' " \
               "UNION " \
               "SELECT nickname, fullname, email, about " \
               "FROM users " \
               "WHERE email = '{}';".format(self.nickname, self.email)


    @staticmethod
    def query_update_user(**kwargs):
        user = {"fullname": "NULL",
                "email": "NULL",
                "about": "NULL",
                "nickname": "NULL",
                }
        for key, val in kwargs.items():
            user[key] = "'%s'" % val

        return "UPDATE users SET " \
               "fullname = COALESCE( {fullname}, fullname), " \
               "email = COALESCE( {email}, email), " \
               "about = COALESCE( {about}, about) " \
               "WHERE nickname = {nickname}".format(**user)

    @staticmethod
    def query_get_user(nickname):
        return "SELECT nickname, fullname, email, about FROM users " \
               "WHERE nickname = '{}';".format(nickname)

    def get_data(self):
        return self.__dict__
