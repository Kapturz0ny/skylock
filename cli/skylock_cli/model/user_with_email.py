from skylock_cli.model import user


class UserWithEmail(user.User):
    email: str
