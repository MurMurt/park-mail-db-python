class Post:
    def __init__(self):
        pass

    @staticmethod
    def query_create_post(thread_id, list_of_params):
        query = "INSERT INTO post (author, message, thread_id) VALUES "
        for post in list_of_params:
            post_values_query = "('{author}', '{message}', {thread_id} ".format(**post, thread_id=thread_id)
            created = post.get('created', False)
            if created:
                post_values_query += ", '{}'), ".format(created)
            else:
                post_values_query += "), "

            query += post_values_query

        query = query[:-2] + " RETURNING id, created, thread_id"

        return query

