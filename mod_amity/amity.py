from __future__ import print_function

import os
import random

from mod_amity.models import Office, LivingSpace, Fellow, Staff, Constants
from mod_amity.util.db import DbUtil
from mod_amity.util.file import FileUtil as fileStorage


class Amity(object):
    """
    Amity is the main class
    inherited classes: Room and subclass
                        Person and subclass
    from models.py. It also creates and perform operations to manage allocations on the available rooms in amity
    """

    def __init__(self):
        self.living_spaces = {'available': [], 'total': []}
        self.offices = {'available': [], 'total': []}

        self.fellows = []
        self.staff = []
        self.ids = {'fellow': [0], 'staff': [0]}

        self.allocated_staff = []
        self.allocated_fellows = []

    def create_office(self, name):
        if self.get_rooms(name) is not None:
            raise ValueError("Room with same name exists")
        self.offices["total"].append(Office(name))
        self.check_room_availability()

    def create_living_space(self, name):
        if self.get_rooms(name) is not None:
            raise ValueError("Room with same name exists")
        self.living_spaces["total"].append(LivingSpace(name))
        self.check_room_availability()

    def add_person(self, name, role, accommodation=None):

        if role == Constants.STAFF.upper():
            return self.create_staff(name)
        elif role == Constants.FELLOW.upper():
            if accommodation:
                return self.create_fellow(name, accommodation)
            else:
                return self.create_fellow(name)

    def create_fellow(self, name, accommodation='N'):
        fellow = Fellow(name, accommodation=accommodation, id=self.generate_fellow_id())
        self.fellows.append(fellow)
        self.allocate_person(fellow)

        return fellow

    def create_staff(self, name):
        staff = Staff(name, id=self.generate_staff_id())
        self.staff.append(staff)
        self.allocate_person(staff)

        return staff

    def allocate_person(self, person):
        """
        assign space to fellow/staff as requested from the available rooms, as follows
            Staff: Office
            Fellow: Office, Living Space(if requested)
        :param person: created person instance
        :return: person object with allocations, if any
        """
        office = random.choice(self.offices["available"]) if len(self.offices["available"]) > 0 else None

        if office:
            office.allocate_space(person)
            person.assign_office(office.name)

        if person.role is Constants.FELLOW:
            if person.accommodation == 'Y':
                living_space = random.choice(self.living_spaces["available"]) \
                    if len(self.living_spaces["available"]) > 0 else None
                if living_space:
                    living_space.allocate_space(person)
                    person.assign_living_space(living_space.name)

        self.check_person_allocation(person)
        self.check_room_availability()

        return person

    def get_unallocated_persons(self):
        """
        gets persons not fully allocated spaces
        :return: dict with  fellows and staff
        """
        return {'staff': list(set(self.staff).symmetric_difference(set(self.allocated_staff))),
                'fellows': list(set(self.fellows).symmetric_difference(set(self.allocated_fellows)))}

    def get_rooms(self, room_name=None):
        """
        gets all offices and living spaces in the allocation pool
        :param room_name: (optional) filter the result by name
        :return: dict of all living_spaces and offices
        """
        offices = self.offices["total"]
        living_spaces = self.living_spaces["total"]
        rooms = offices + living_spaces
        if room_name is not None:
            for room in rooms:
                if room.name == room_name:
                    return room
        else:
            return {'living_spaces': living_spaces, 'offices': offices}

    def generate_staff_id(self):
        """
        generate unique ids for staff
        :return: staff id i.e ST001
        """
        staff_id = self.ids["staff"][0] + 1
        self.ids["staff"][0] = staff_id
        return "ST{0}".format(str(staff_id).rjust(3, '0'))

    def generate_fellow_id(self):
        """
        generate unique ids for fellow
        :return: staff id i.e FL001
        """
        staff_id = self.ids["fellow"][0] + 1
        self.ids["fellow"][0] = staff_id
        return "FL{0}".format(str(staff_id).rjust(3, '0'))

    def check_person_allocation(self, person):
        """
        checks if fellow/staff is fully allocated and add to allocated list
        :param person: an instance of fellow or staff
        :return:
        """
        if person.role == Constants.STAFF:
            if person.office is not None:
                self.allocated_staff.append(person)

        elif person.role == Constants.FELLOW:
            if person.living_space is not None and person.office is not None:
                self.allocated_fellows.append(person)

    def find_person_by_name(self, name):
        """
        Search combined list of fellows and staff for partial match of name
        :param name:
        :return: List of person object matching name
        """
        match = []
        for person in (self.fellows + self.staff):
            if name in person.name:
                match.append(person)
        return match

    def find_person_by_id(self, person_id):
        """
        get staff/fellow matching the id
        :param person_id:
        :return: Fellow/staff object on matching search
        """
        for person in (self.fellows + self.staff):
            if person.id == person_id:
                return person

    def relocate_person(self, person_id, room_name):
        """
        relocate allocated person from current position to new office
        :param person_id: unique id for Staff/fellow
        :param room_name: room to move to
        :return: dict with person and new room
        """

        person = self.find_person_by_id(person_id)
        new_room = self.get_rooms(room_name)

        if not new_room:
            raise ValueError("cannot find room named {}".format(room_name))

        if not person:
            raise ValueError("Cannot Find person with id " + person_id)

        if new_room.is_full():
            raise ValueError("{} is full. Cannot relocate person".format(room_name))

        if new_room.type == Constants.LIVING_SPACE and person.role == Constants.STAFF:
            raise ValueError("Cannot relocate staff member to Living Space")

        old_room = None

        if new_room.type == Constants.OFFICE:
            old_room = self.get_rooms(person.office)
        elif new_room.type == Constants.LIVING_SPACE and person.role == Constants.FELLOW:
            old_room = self.get_rooms(person.living_space)

        # check new room is same types as new room
        if not old_room:
            raise ValueError("{} not currently allocated {} ".format(person.id, new_room.type))

        if not old_room.type == new_room.type:
            raise ValueError("can only relocate to rooms of same type")

        for occupant in old_room.occupants:
            if occupant.id == person_id:
                old_room.occupants.remove(occupant)
                new_room.allocate_space(occupant)

                if new_room.type == Constants.OFFICE:
                    occupant.office = new_room.name
                elif new_room.type == Constants.LIVING_SPACE:
                    occupant.living_space = new_room.name
                break
        self.check_room_availability()

        return {'person': person.id, 'new_room': new_room.name, 'old_room': old_room.name}

    def check_room_availability(self):
        """
        check for state of room occupants and moves rooms to available as needed
        """
        self.offices["available"] = []
        self.living_spaces["available"] = []
        for office in self.offices["total"]:
            if not office.is_full():
                self.offices["available"].append(office)
        for living_space in self.living_spaces["total"]:
            if not living_space.is_full():
                self.living_spaces["available"].append(living_space)

    def load_people(self, file_name):

        people = []

        for person in fileStorage.read_from_file(file_name):
            name = " {} {}".format(person[0], person[1])
            role = person[2].upper()

            accommodation = person[3] if len(person) > 3 else None

            people.append(self.add_person(name, role, accommodation))

        return people

    def save_state(self, db_path):

        if os.path.exists(db_path):
            print("deleting previous state database")
            os.remove(db_path)

        db_util = DbUtil(db_path)

        rooms = self.living_spaces["total"] + self.offices["total"]

        return db_util.save_to_db(rooms=rooms, people={'fellows': self.fellows, 'staff': self.staff})

    def load_state(self, db_path):

        if not os.path.exists(db_path):
            raise ValueError("cannot open db at {} ".format(db_path))

        db_util = DbUtil(db_path)

        save_state = db_util.load_state()

        if save_state:

            self.ids = save_state['current_ids']
            self.living_spaces['total'] = save_state['living_spaces']
            self.offices['total'] = save_state['offices']

            self.fellows = save_state['fellows']
            self.staff = save_state['staff']

            for person in (self.fellows + self.staff):
                self.check_person_allocation(person)

            self.check_room_availability()

            return True

        return False
