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
                                     "(SELECT path FROM post" \
                                     " WHERE id = {parent} ) ), ".format(parent=parent, thread_id=thread_id)
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
            query = "SELECT forum, author,created, id, message, CASE WHEN parent = id THEN NULL ELSE parent END, thread FROM (" \
                    "SELECT (SELECT forum FROM thread WHERE id = {thread_id}), " \
                    "author, created, id, message, " \
                    "parent_id as parent, thread_id as thread, " \
                    "path " \
                    "FROM post WHERE thread_id = {thread_id} ".format(
                thread_id=thread_id)
            if decs == 'true':
                query += "ORDER BY path DESC, id"
            else:
                query += "ORDER BY path, id "

            query += " ) as T "

            if since and decs == 'true':
                query += "WHERE path < (SELECT path from (SELECT id, path from post) as tt WHERE tt.id = {since}) ".format(
                    since=since)
            elif since and decs != 'true':
                query += "WHERE path > (SELECT path from (SELECT id, path from post) as tt WHERE tt.id = {since}) ".format(
                    since=since)

            if limit:
                query += " LIMIT {}".format(limit)

        elif sort == 'parent_tree':
            query = "SELECT forum, T.author, T.created, T.id, T.message, CASE WHEN parent = T.id THEN NULL ELSE parent END, thread FROM (" \
                    "SELECT (SELECT forum FROM thread WHERE id = {thread_id}), " \
                    "author, created, id, message, " \
                    "parent_id as parent, thread_id as thread, " \
                    "CASE WHEN path NOTNULL THEN path || ARRAY[id] ELSE ARRAY[id] END as path " \
                    "FROM post WHERE thread_id = {thread_id} ".format(thread_id=thread_id)

            if decs == 'true':
                query += "ORDER BY parent DESC, path, id "
            else:
                query += "ORDER BY path, id "

            query += " ) as T "

            if since:
                query += "join (SELECT id " \
                         "FROM (SELECT CASE WHEN path NOTNULL THEN path || ARRAY[id] ELSE ARRAY[id] END as paths, id, parent_id" \
                         " FROM post " \
                         "WHERE parent_id = id AND thread_id = {thread_id}) as I" \
                         " WHERE paths [ 1 ] {comparator} (SELECT CASE WHEN path NOTNULL THEN path [ 1 ] ELSE id END as path " \
                         "from post WHERE id = {since}) ".format(since=since, thread_id=thread_id,
                                                                 comparator='<' if decs == 'true' else '>')
            else:
                query += " join (SELECT * FROM post WHERE parent_id = id AND thread_id = {thread_id} ".format(
                    thread_id=thread_id)
            if limit and decs == 'true':
                query += " ORDER BY id desc LIMIT {}".format(limit)
            elif limit and decs != 'true':
                query += " ORDER BY id LIMIT {}".format(limit)
            query += " ) as S ON S.id = T.path[1]"

            if decs == 'true':
                query += "ORDER BY row_number() over (order by T.path [1] desc , T.path)"
            else:
                query += "ORDER BY row_number() over (order by T.path [1] , T.path)"

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
