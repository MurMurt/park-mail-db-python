class Forum:
    def __init__(self, slug, title, user):
        self.slug = slug
        self.title = title
        self.user = user
        self.posts = 0
        self.threads = 0

    def get_data(self):
        return self.__dict__

    def query_create_forum(self):
        return "INSERT INTO forum (slug, title, user_nick) " \
               "VALUES ('{}', '{}', '{}')".format(self.slug, self.title, self.user)

    @staticmethod
    def query_get_forum(slug):
        return "SELECT slug, title, user_nick FROM forum " \
        "WHERE slug = '{}';".format(slug)
