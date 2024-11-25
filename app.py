from abc import ABC, abstractmethod
from collections import UserDict
from datetime import datetime, date, timedelta
import pickle


# Базовий клас для користувальницьких уявлень
class UserView(ABC):
    @abstractmethod
    def display_message(self, message):
        pass

    @abstractmethod
    def display_contact(self, record):
        pass

    @abstractmethod
    def display_all_contacts(self, book):
        pass


# Реалізація для консольного інтерфейсу
class ConsoleView(UserView):
    def display_message(self, message):
        print(message)

    def display_contact(self, record):
        print(record)

    def display_all_contacts(self, book):
        for record in book.data.values():
            print(record)

class Field:
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return str(self.value)


class Name(Field):
    def __init__(self, value):
        if not value:
            raise ValueError("Ім'я не може бути порожнім.")
        super().__init__(value)


class Phone(Field):
    def __init__(self, value):
        super().__init__(value)
        if not self._is_valid(value):
            raise ValueError("Номер телефону має = 10 цифрам.")

    def _is_valid(self, value):
        return value.isdigit() and len(value) == 10


class Birthday(Field):
    def __init__(self, value):
        try:
            super().__init__(value)
            value = datetime.strptime(value, "%d.%m.%Y")
        except ValueError:
            raise ValueError("Invalid date format. Use DD.MM.YYYY")


class Record:
    def __init__(self, name):
        self.name = Name(name)
        self.phones = []
        self.birthday = None

    def add_phone(self, phone):
        phone_1 = Phone(phone)
        self.phones.append(phone_1)

    def add_birthday(self, birthday):
        birthday_1 = Birthday(birthday)
        self.birthday = birthday_1

    def remove_phone(self, phone):
        if phone in [p.value for p in self.phones]:
            self.phones = [p for p in self.phones if p.value != phone]

    def edit_phone(self, old_phone, new_phone):
        if self.find_phone(old_phone):
            self.add_phone(new_phone)
            self.remove_phone(old_phone)
        else:
            raise ValueError

    def find_phone(self, phone):
        for phones in self.phones:
            if phones.value == phone:
                return phones
        return None

    def __str__(self):
        return f"Contact name: {self.name.value}, phones: {'; '.join(p.value for p in self.phones)}, birthday: {self.birthday}"


class AddressBook(UserDict):

    def add_record(self, record):
        if record.name.value in self.data:
            raise ValueError(f"Контакт з ім'ям {record.name.value} вже існує.")
        self.data[record.name.value] = record

    def find(self, name):
        return self.data.get(name)

    def delete(self, name):
        if name in self.data:
            self.data.pop(name)

    def string_to_date(self, date_string):
        return datetime.strptime(date_string, "%d.%m.%Y").date()

    def date_to_string(self, date):
        return date.strftime("%d.%m.%Y")

    def find_next_weekday(self, start_date, weekday):
        days_ahead = weekday - start_date.weekday()
        if days_ahead <= 0:
            days_ahead += 7
        return start_date + timedelta(days=days_ahead)

    def adjust_for_weekend(self, birthday):
        if birthday.weekday() >= 5:
            return self.find_next_weekday(birthday, 0)
        return birthday

    def get_upcoming_birthdays(self, days=7):
        upcoming_birthdays = []
        today = date.today()
        for user in self.data:
            birthday = self.data[user].birthday
            if birthday is None:
                continue
            else:
                birthday_1 = str(birthday)
                birthday_2 = self.string_to_date(birthday_1)
                birthday_this_year = birthday_2.replace(year=today.year)
                if birthday_this_year < today:
                    birthday_this_year = birthday_2.replace(year=today.year + 1)
                if 0 <= (birthday_this_year - today).days <= days:
                    birthday_this_year = self.adjust_for_weekend(birthday_this_year)
                    congratulation_date_str = self.date_to_string(birthday_this_year)
                    upcoming_birthdays.append({"name": self.data[user].name.value, "birthday": congratulation_date_str})
        return upcoming_birthdays

    def __str__(self):
        return "\n".join(str(record) for record in self.data.values())


def save_data(book, filename="addressbook.pkl"):
    with open(filename, "wb") as f:
        pickle.dump(book, f)


def load_data(filename="addressbook.pkl"):
    try:
        with open(filename, "rb") as f:
            return pickle.load(f)
    except FileNotFoundError:
        return AddressBook()  # Повернення нової адресної книги, якщо файл не знайдено


def input_error(func):
    def inner(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ValueError:
            return "Give me name and phone or phones please. Or phone number must = 10 digit. Or Invalid date format. Use DD.MM.YYYY"
        except KeyError:
            return "Such a name does not exist"
        except IndexError:
            return "Give me name please"

    return inner


@input_error
def parse_input(user_input):
    cmd, *args = user_input.split()
    cmd = cmd.strip().lower()
    return cmd, *args


@input_error
def add_contact(args, book: AddressBook):
    name, phone, *_ = args
    record = book.find(name)
    message = "Contact updated."
    if record is None:
        record = Record(name)
        book.add_record(record)
        message = "Contact added."
    if phone:
        record.add_phone(phone)
    return message


@input_error
def add_birthday(args, book: AddressBook):
    name, birthday, *_ = args
    record = book.find(name)
    message = "Birthday updated."
    if record is None:
        record = Record(name)
        book.add_record(record)
        message = "Contact added."
    if birthday:
        record.add_birthday(birthday)
    return message


@input_error
def show_birthday(args, book: AddressBook):
    name, *_ = args
    return book[name].birthday.__str__()


@input_error
def birthdays(args, book: AddressBook):
    return book.get_upcoming_birthdays()


@input_error
def change_contact(args, book: AddressBook):
    name, old_phone, new_phone, *_ = args
    record = book.find(name)
    if record:
        Phone(new_phone)
        record.remove_phone(old_phone)
        record.add_phone(new_phone)
    return "Contact updated."


@input_error
def show_phone(args, book: AddressBook):
    name, *_ = args
    return f"Contact name: {name}, phones: {'; '.join(p.value for p in book[name].phones)}"


@input_error
def show_all(args, book: AddressBook):
    args = args
    return book




# Основна функція змінюється для роботи з об'єктом UserView
def main():
    book = load_data()
    view = ConsoleView()  # Використовується консольний інтерфейс
    view.display_message("Welcome to the assistant bot!")

    while True:
        user_input = input("Enter a command: ")
        command, *args = parse_input(user_input)

        if command in ["close", "exit"]:
            view.display_message("Good bye!")
            save_data(book)
            break

        elif command == "hello":
            view.display_message("How can I help you?")

        elif command == "add":
            message = add_contact(args, book)
            view.display_message(message)

        elif command == "change":
            message = change_contact(args, book)
            view.display_message(message)

        elif command == "phone":
            message = show_phone(args, book)
            view.display_message(message)

        elif command == "all":
            view.display_all_contacts(book)

        elif command == "add-birthday":
            message = add_birthday(args, book)
            view.display_message(message)

        elif command == "show-birthday":
            message = show_birthday(args, book)
            view.display_message(message)

        elif command == "birthdays":
            birthdays_list = birthdays(args, book)
            if birthdays_list:
                for birthday in birthdays_list:
                    view.display_message(f"{birthday['name']} - {birthday['birthday']}")
            else:
                view.display_message("No upcoming birthdays.")

        else:
            view.display_message("Invalid command.")


if __name__ == "__main__":
    main()