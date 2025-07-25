import os
from dataclasses import dataclass

class Auth:
    def __init__(self):
        self.id = ''
        self.secret = ''
    
    def login(self, id, secret):
        self.id = id
        self.secret = secret

    def logout(self):
        self.id = ''
        self.secret = ''

    def authenticate(self):
        return (( self.id == os.getenv("AUTH_ID")) 
                and (self.secret == os.getenv("AUTH_SECRET"))) 

@dataclass
class Login: id:str; secret:str