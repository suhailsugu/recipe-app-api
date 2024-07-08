"""
Test Case for Models
"""


from django.test import TestCase
from django.contrib.auth import get_user_model
from decimal import Decimal
from core import models

def create_users(email="user@example.com",password='testpass123'):
    return get_user_model().objects.create_user(email,password)



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

    #Recipe Section
    def test_create_recipe(self):
        user = get_user_model().objects.create_user('test@example.com','testpass123')

        recipe = models.Recipe.objects.create(user=user,title='Sample recipe name',
                                              time_minutes=5,price=Decimal('5.50'),description='Sample recipe description')

        self.assertEqual(str(recipe),recipe.title)


    def test_create_tags(self):
        user = create_users()

        tag = models.Tag.objects.create(user=user,name='Tag1')

        self.assertEqual(str(tag),tag.name)







