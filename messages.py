class Message:

    '''
    This class is used to transmit any message to and from the server, to clients.
    The "id"-argument tells the program what type of message it is.
    For regular char msg, set id="msg"
    For sending an updated userlist, set id="updusr"
    '''
    def __init__(self, id: str, date: str, owner: str, message):
        self.id = id
        self.date = date
        self.owner = owner
        self.message = message




