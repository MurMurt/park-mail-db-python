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
        return "SELECT (SELECT count(*) FROM post JOIN thread ON post.thread_id = thread.id " \
               "WHERE thread.forum = '{slug}') as posts, slug, " \
               "(SELECT count(*) FROM thread WHERE thread.forum = '{slug}') as threads, title, (SELECT nickname FROM users WHERE nickname = forum.user_nick) as user " \
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
        query = '''SELECT * FROM (SELECT u.nickname, u.fullname, u.email, u.about
                FROM users u
                JOIN thread t ON u.nickname = t.author
                WHERE t.forum = '{slug}'
                UNION
                SELECT u.nickname, u.fullname, u.email, u.about
                FROM users u 
                JOIN post p ON u.nickname = p.author
                JOIN thread t ON t.id = p.thread_id WHERE t.forum = '{slug}') forum_users '''.format(slug=slug)

        if since:
            if desc == 'true':
                query += '''WHERE nickname COLLATE "ucs_basic" < '{}' COLLATE "ucs_basic"'''.format(since)
            else:
                query += '''WHERE nickname COLLATE "ucs_basic" > '{}' COLLATE "ucs_basic"'''.format(since)
        query += ''' ORDER BY nickname COLLATE "ucs_basic"'''
        if desc == 'true':
            query += " DESC"

        if limit:
            query += " LIMIT {}".format(limit)

        return query