class Forum:
    def __init__(self, slug, title, user):
        self.slug = slug
        self.title = title
        self.user = user

    def get_data(self):
        return self.__dict__

    def query_create_forum(self):
        return "INSERT INTO forum (slug, title, user_nick) " \
               "VALUES ('{}', '{}', '{}')".format(self.slug, self.title, self.user)

    @staticmethod
    def query_get_forum(slug):
        return "SELECT f.slug, f.title, u.nickname as user FROM forum as f " \
               "JOIN users u on f.user_nick = u.nickname " \
               "WHERE slug = '{}';".format(slug)
