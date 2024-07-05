"""
Test Case for Models
"""


from django.test import TestCase
from django.contrib.auth import get_user_model



class ModelTest(TestCase):
    """Test Models"""

    def test_user_model(self):
        """Test creating a user with an email is sucessfull"""

        email = "test@example.com"
        password = "testpassword123"
        user = get_user_model().objects.create_user(email=email,password=password)

        self.assertEqual(user.email,email)
        self.assertTrue(user.check_password(password))

    def test_new_user_email_normalized(self):
        """Test Email Normalization"""

        sample_emails = [
            ['test1@EXAMPLE.com', 'test1@example.com'],
            ['Test2@Example.com', 'Test2@example.com'],
            ['TEST3@EXAMPLE.com', 'TEST3@example.com'],
            ['test4@example.COM', 'test4@example.com'],
        ]
        for email,expected in  sample_emails:
           user = get_user_model().objects.create_user(email=email)
           self.assertEqual(user.email,expected)

    def test_new_user_without_email_raises_error(self):
        """Test User creation email address will raise an value error"""

        with self.assertRaises(ValueError):
            get_user_model().objects.create_user('','test123')

    def test_create_superuser(self):
        """Test creating a superuser"""

        user = get_user_model().objects.create_superuser(
            'test1123@example.com',
            'test123'
        )

        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)




