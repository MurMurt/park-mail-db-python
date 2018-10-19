class Vote:
    def __init__(self, nickname, voice, thread_id):
        self.nickname = nickname
        self.voice = voice
        self.thread_id = thread_id

    def query_vote_create(self):
        return "INSERT INTO vote (thread_id, nickname, voice) " \
               "VALUES ({thread_id}, '{nickname}', {voice}) " \
               "ON CONFLICT ON CONSTRAINT unique_votes " \
               "DO UPDATE SET voice = {voice} " \
               "WHERE vote.thread_id = (SELECT id FROM thread " \
               "WHERE id = {thread_id}) AND vote.nickname = '{nickname}';".format(**self.__dict__)
