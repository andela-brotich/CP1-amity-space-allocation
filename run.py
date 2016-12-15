#!/usr/bin/env python2

"""
Usage:
    amity create_room <room_name>...
    amity add_person <first_name> <last_name> (Fellow|Staff) [<wants_accomodation>]
    amity reallocate_person <person_name> <new_room_name>
    amity remove_person <person_identifier>
    amity load_people <filename>
    amity print_allocations [-o <filename>]
    amity print_unallocated [-o <filename>]
    amity print_room <room_name>
    amity save_state [--db=sqlite_database]
    amity load_state <sqlite_database>
    amity (-i | --interactive)
    amity (-h | --help)
Options:
    -o, --output  Save to a txt file
    -i, --interactive  Interactive Mode
    -h, --help  Show this screen and exit.
"""

import sys
import os
import cmd
from docopt import docopt, DocoptExit

from mod_amity.amity import Amity


def docopt_cmd(func):
    """
    This decorator is used to simplify the try/except block and pass the result
    of the docopt parsing to the called action.
    """

    def fn(self, arg):
        try:
            opt = docopt(fn.__doc__, arg)

        except DocoptExit as e:
            # The DocoptExit is thrown when the args do not match.
            # We print a message to the user and the usage block.

            print('Invalid Command!')
            print(e)
            return

        except SystemExit:
            # The SystemExit exception prints the usage for --help
            # We do not need to do the print here.

            return

        return func(self, opt)

    fn.__name__ = func.__name__
    fn.__doc__ = func.__doc__
    fn.__dict__.update(func.__dict__)
    return fn


amity = Amity()


class AmityRun(cmd.Cmd):
    intro = 'Welcome to Amity' \
            + ' (type help for a list of commands.)'
    prompt = '(Amity) '
    file = None

    @docopt_cmd
    def do_add_person(self, args):
        """Usage:
        add_person <first_name> <last_name> <role> [<wants_accommodation>]"""
        name = "{} {}".format(args["<first_name>"], args["<last_name>"])
        role = args["<role>"].upper()

        if role not in ["FELLOW", "STAFF"]:
            print ("Invalid: role should STAFF or FELLOW")
            return

        if role == "STAFF":
            staff = amity.create_staff(name)
            print ("{} created successfully".format(staff.role))
            print ("    ID:   {}".format(staff.id))
            print ("    Name: {}".format(staff.name))
            print (" ")

            if staff.office:
                print ("allocated Office {} ".format(staff.office))
            else:
                print ("No vacant Office to allocate")

        if role == "FELLOW":
            wants_accommodation = args["<wants_accommodation>"].upper() if args["<wants_accommodation>"] else 'N'

            if wants_accommodation not in ["Y", "N"]:
                print ("Invalid: wants_accommodation values are 'Y' or 'N'")
                return

            fellow = amity.create_fellow(name, accommodation='N')

            print ("{} created successfully".format(fellow.role))
            print ("    ID:   {}".format(fellow.id))
            print ("    Name: {}".format(fellow.name))
            print (" ")

            if fellow.office:
                print ("allocated Office {} ".format(fellow.office))
            else:
                print ("No vacant Office to allocate")
            if fellow.living_space:
                print ("allocated Living Space {} ".format(fellow.living_space))
            else:
                print ("No vacant Living Space to allocate")



    def do_clear(self, arg):
        """Clears screen>"""

        os.system('clear')

    def do_quit(self, arg):
        """Quits out of Interactive Mode."""

        print('Good Bye!')
        exit()


opt = docopt(__doc__, sys.argv[1:])

if opt['--interactive']:
    AmityRun().cmdloop()
