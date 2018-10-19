class Post:
    def __init__(self):
        pass

    @staticmethod
    def query_create_post(thread_id, params):
        query = ''
        # if type(params) == list:
        #     has_parent = params[0].get(['parent'], False)
        has_parent = params[0].get('parent', False)
        # created = params[0].get('created', False)
        # print('TYPE', type(params[0]))
        print('PARENT ', has_parent)
        # if has_parent and has_parent != 0:
        if False:
            query = "INSERT INTO post (author, message, thread_id, path, parent_id) VALUES "
            for post in params:
                post_values_query = ''
                if created:
                    post_values_query = "('{author}', '{message}', " \
                                        "(SELECT thread_id FROM post WHERE id = {parent} AND thread_id = {thread_id})," \
                                        "(SELECT path || ARRAY[{parent}] FROM post WHERE id = {parent})," \
                                        " {parent}, '{created}', ), ".format(**post, thread_id=thread_id)

                else:
                    post_values_query += "('{author}', '{message}', " \
                                         "(SELECT thread_id FROM post WHERE id = {parent} AND thread_id = {thread_id})," \
                                         "(SELECT path || ARRAY[{parent}] FROM post WHERE id = {parent})," \
                                         " {parent}), ".format(**post, thread_id=thread_id)

                query += post_values_query

            query = query[:-2] + " RETURNING id, created, thread_id"


        else:

            query = "INSERT INTO post  VALUES "

            for post in params:
                has_parent = post.get('parent', False)
                post_values_query = ''
                post_values_query += "(nextval('post_id_seq'), '{author}', '{message}', {thread_id}, {parent_id} {path}), ".format(
                    author=post['author'], message=post['message'],
                    thread_id=thread_id, parent_id='NULL' if not has_parent else has_parent,
                    path="{}".format(
                        ", NULL" if not has_parent else ", (SELECT path FROM post WHERE id = {parent} )".format(
                            parent=has_parent)))
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
                query += "WHERE path > (SELECT path from (SELECT id, path from post) as tt WHERE tt.id = {since}) ".format(since=since)




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
                         "from post WHERE id = {since}) ".format(since=since, thread_id=thread_id, comparator='<' if decs == 'true' else '>')
            else:
                query += " join (SELECT * FROM post WHERE parent_id = id AND thread_id = {thread_id} ".format(thread_id=thread_id)
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
