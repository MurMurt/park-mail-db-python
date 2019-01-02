class Forum:
    def __init__(self, slug, title, user):
        self.slug = slug
        self.title = title
        self.user = user

    def get_data(self):
        return self.__dict__

    def query_create_forum(self):
        return "INSERT INTO forum (slug, title, user_nick) " \
               "VALUES ('{}', '{}', (SELECT  nickname  FROM users WHERE nickname = '{}'))".format(self.slug, self.title, self.user)

    @staticmethod
    def query_get_forum(slug):
        return "SELECT posts, slug, " \
               "threads, title, user_nick as user " \
               "FROM forum " \
               "WHERE slug = '{slug}';".format(slug=slug)
    #                "JOIN users u on f.user_nick = u.nickname " \

    @staticmethod
    def query_get_forum_slug(slug):
        return "SELECT f.slug, f.title, u.nickname as user FROM forum as f " \
               "JOIN users u on f.user_nick = u.nickname " \
               "WHERE slug = '{}';".format(slug)

    @staticmethod
    def query_get_users(slug, since, limit, desc):
        query = "SELECT u.nickname, u.fullname, u.email, u.about " \
                "FROM forum_user f_u " \
                "JOIN users u ON u.id = f_u.user_id " \
                "WHERE f_u.forum = '{slug}' ".format(slug=slug)

        if since:
            if desc == 'true':
                query += '''AND nickname < '{}' '''.format(since)
            else:
                query += '''AND nickname > '{}' '''.format(since)
        query += ''' ORDER BY nickname '''
        if desc == 'true':
            query += " DESC"

        if limit:
            query += " LIMIT {}".format(limit)

        return query
