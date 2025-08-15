import unittest
from icalendar import Calendar

from email_assistant.email_processor import EmailPresistence
from email_assistant.main import DB_FILE

class TestEmailCalender(unittest.TestCase):
    def setUp(self) -> None:
        self.emailPresistence = EmailPresistence(DB_FILE, "")
        self.emailPresistence.connect()
        return super().setUp()
    
    def tearDown(self) -> None:
        self.emailPresistence.close()
        return super().tearDown()

    def test_email_calender(self):
        email =self.emailPresistence.get_email_by_uid(3328)
        self.assertIsNotNone(email)
        if email is not None:
            # print(email.content)
            cal = Calendar.from_ical(email.content)
            # print(cal)
            for component in cal.walk():
                if component.name == "VEVENT":
                    print(component.get('summary'))
                    print(component.get('dtstart').dt)
                    print(component.get('dtend').dt)
                    print(component.get('location'))
                    print(component.get('description'))
                    print("="*30)


