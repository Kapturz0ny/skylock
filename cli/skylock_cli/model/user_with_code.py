from skylock_cli.model import user_with_email

class UserWithCode(user_with_email.UserWithEmail):
    code: str