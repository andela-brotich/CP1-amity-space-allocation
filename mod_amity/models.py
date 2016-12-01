

class Role(object):
    STAFF = 0
    FELLOW = 1


class Person(object):
    role = None

    def __init__(self, name):
        self.name = name
        self.office = None

    def assign_office(self, office):
        self.office = office
        return True

    def get_role(self):
        return self.role


class Staff(Person):
    role = Role.STAFF


class Fellow(Person):
    pass
