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
                   "VALUES ({slug}, (SELECT slug FROM forum WHERE slug = '{forum}'), '{author}', '{title}', '{message}') " \
                   "RETURNING id;".format(**self.__dict__)

        return "INSERT INTO thread (slug, forum, author, title, message, created) " \
               "VALUES ({slug}, (SELECT slug FROM forum WHERE slug = '{forum}'), '{author}', '{title}', '{message}', '{created}') " \
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

    @staticmethod
    def query_get_thread_id(slug):
        return "SELECT id, forum FROM thread WHERE slug = '{}'".format(slug)

    @staticmethod
    def query_get_thread_forum(id):
        return "SELECT forum FROM thread WHERE id = {}".format(id)

    @staticmethod
    def query_get_thread_by_id(id):
        return "SELECT * FROM thread WHERE id = {};".format(id)

    @staticmethod
    def query_get_thread_by_slug(slug):
        return "SELECT * FROM thread WHERE slug = '{}' ;".format(slug)

    @staticmethod
    def query_update_thread(id, message, title):
        if not message:
            return "UPDATE thread SET title = '{title}' " \
                   "WHERE id = '{id}' ;".format(id=id, title=title)
        if not title:
            return "UPDATE thread SET message = '{message}'" \
                   "WHERE id = '{id}' ;".format(id=id, message=message)
        return "UPDATE thread SET message = '{message}', title = '{title}' " \
               "WHERE id = '{id}' ;".format(id=id, message=message, title=title)
