class Thread:
    def __init__(self, author, forum, message, title, slug='NULL', created='NULL'):
        self.author = author
        self.created = created
        self.forum = forum
        self.message = message
        self.title = title
        self.slug = slug
        if self.slug != 'NULL':
            self.slug = "'{}'".format(self.slug)

    def get_data(self):
        return self.__dict__

    def query_create_thread(self):
        if self.created == 'NULL':
            return "INSERT INTO thread (slug, forum, author, title, message) " \
                   "VALUES ({slug}, '{forum}', '{author}', '{title}', '{message}') " \
                   "RETURNING id;".format(**self.__dict__)

        return "INSERT INTO thread (slug, forum, author, title, message, created) " \
               "VALUES ({slug}, '{forum}', '{author}', '{title}', '{message}', '{created}') " \
               "RETURNING id;".format(**self.__dict__)

    @staticmethod
    def query_get_threads(forum_slug, limit, desc, since):
        query = "SELECT thread.id, slug, created, title, message, author, forum " \
                "FROM thread " \
                "WHERE forum = '{slug}'".format(slug=forum_slug)
        if since:
            query += " AND created {1}= '{0}'".format(since, '<' if desc == 'true' else '>')

        query += " ORDER BY created"
        if desc == 'true':
            query += " DESC"
        if limit:
            query += " LIMIT {}".format(limit)

        query += ';'
        return query

        # "SELECT thread.id, slug, created, title, message, 0 AS votes, user_nick, forum_slug " \
        # "FROM thread " \
        # "WHERE forum_slug = '{slug}' " \
        # "ORDER BY created DESC " \
        # "LIMIT 10;"
