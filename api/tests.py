from django.test import TestCase
from rest_framework.test import APITestCase
from django.urls import reverse
from .models import User

# Create your tests here.

class UserAuthTests(APITestCase):
    def test_register(self):
        url = reverse('register')
        data = {
            'email': 'testuser@example.com',
            'first_name': 'Test',
            'last_name': 'User',
            'password': 'testpassword123'
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['email'], data['email'])

    def test_login_success(self):
        user = User.objects.create_user(email='testlogin@example.com', password='testpass', first_name='A', last_name='B')
        url = reverse('login')
        data = {'email': 'testlogin@example.com', 'password': 'testpass'}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['email'], user.email)

    def test_login_fail(self):
        url = reverse('login')
        data = {'email': 'notfound@example.com', 'password': 'wrongpass'}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 400)
