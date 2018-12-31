class Post:
    def __init__(self):
        pass

    @staticmethod
    def query_create_post(thread_id, params):
        query = "INSERT INTO post (author, message, thread_id, parent_id, path) VALUES "
        for post in params:
            parent = post.get('parent', False)
            post_values_query = ''
            post_values_query += "('{author}', '{message}', ".format(author=post['author'],
                                                                     message=post['message'])
            if parent:
                post_values_query += "(SELECT thread_id FROM post WHERE id = {parent} AND " \
                                     "thread_id = {thread_id}), {parent}, " \
                                     "(SELECT path || id FROM post" \
                                     " WHERE id = {parent} AND thread_id = {thread_id}) ), ".format(parent=parent,
                                                                                                    thread_id=thread_id)
            else:
                post_values_query += "{}, NULL, NULL ), ".format(thread_id)

            query += post_values_query

        query = query[:-2] + " RETURNING id, created, thread_id"
        return query

    @staticmethod
    def query_get_posts(thread_id, since, sort, decs, limit):
        query = "SELECT (SELECT forum FROM thread WHERE id = {thread_id}), " \
                "author, created, id, message, " \
                "CASE WHEN parent_id = id THEN NULL ELSE parent_id END as parent, thread_id as thread " \
                "FROM post WHERE thread_id = {thread_id} ".format(
            thread_id=thread_id)

        if since and decs == 'true':
            query += "AND id < {since} ".format(since=since)

        elif since and decs != 'true':
            query += "AND id > {since} ".format(since=since)

        if sort == 'flat':

            query += "ORDER BY created "
            if decs == 'true':
                query += "DESC, id DESC "
            else:
                query += ", id "

            if limit:
                query += "LIMIT {}".format(limit)

        elif sort == 'tree':
            query = "SELECT p.author, p.created, (SELECT forum FROM thread WHERE id = {thread_id})," \
                    " p.id, p.message, p.parent_id as parent, p.thread_id as thread FROM post p ".format(
                thread_id=thread_id)

            if since and decs == 'true':
                query += " JOIN post ON post.id = {since} WHERE p.path || p.id < post.path || post.id ".format(
                    since=since)

            elif since and decs != 'true':
                query += " JOIN post ON post.id = {since} WHERE p.path || p.id > post.path || post.id ".format(
                    since=since)

            if since:
                query += " AND p.thread_id = {thread_id} ORDER BY p.path || p.id ".format(thread_id=thread_id)

            else:
                query += " WHERE p.thread_id = {thread_id} ORDER BY p.path || p.id ".format(thread_id=thread_id)

            if decs == 'true':
                query += " DESC "

            if limit:
                query += " LIMIT {}".format(limit)

        elif sort == 'parent_tree':
            query = "SELECT ch.id, ch.thread_id as thread, ch.parent_id, ch.path, ch.created, ch.message, ch.author, ch.parent_id as parent, " \
                    "(SELECT forum FROM thread WHERE id = {thread_id}) " \
                    "FROM (SELECT * from post WHERE parent_id IS NULL AND " \
                    "thread_id = {thread_id} ".format(thread_id=thread_id)

            if since:
                query += "AND id "
                if decs == 'true':
                    query += "<"
                else:
                    query += ">"

                query += " (SELECT parent_id FROM post WHERE id = {}) ".format(since)

            query += " ORDER BY id "
            if decs == 'true':
                query += "DESC "
            if limit:
                query += "LIMIT {}".format(limit)
            query += ") parents JOIN post ch ON parents.id = ch.id OR ch.path [1] = parents.id " \
                     "ORDER BY parents.id "

            if decs == 'true':
                query += "DESC "

            query += ", ch.path || ch.id ASC "

        return query

    @staticmethod
    def query_get_post_details(post_id):
        query = '''SELECT u.about, u.email, u.fullname, u.nickname,
                        (SELECT count(*) FROM post JOIN thread ON post.thread_id = thread.id WHERE thread.forum = f.slug ) as posts,
                        f.slug,
                        (SELECT count(*) FROM thread WHERE thread.forum = f.slug) as threads, f.title as f_title, f.user_nick as f_nick,
                        p.author, p.created as post_created , f.slug as f_slug, p.id as post_id, p.is_edited, p.message as post_message, p.parent_id as parent, p.thread_id,
                        t.author as t_author, t.created as t_created, f.slug as forum, t.id, t.message as t_message, t.slug as t_slug, t.title as t_title, t.id as t_id, t.votes  as votes
                    FROM post p
                        JOIN users u on p.author = u.nickname
                        JOIN thread t on p.thread_id = t.id
                        JOIN forum f on t.forum = f.slug
                    WHERE p.id = {}'''.format(post_id)
        return query
