class EmailAlreadyExistsException(Exception):

    def __init__(self):

        super().__init__(
            "Email already registered"
        )


class UserNotFoundException(Exception):

    def __init__(self):

        super().__init__(
            "User not found"
        )