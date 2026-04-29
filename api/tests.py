from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from .models import Company, KBEntry, QueryLog


class TeamBoardAPITests(APITestCase):
    def setUp(self):
        KBEntry.objects.create(
            question='What is select_related in Django ORM?',
            answer='select_related performs a SQL JOIN and fetches related objects.',
            category=KBEntry.Category.DATABASE,
        )
        KBEntry.objects.create(
            question='How does transaction.atomic() work?',
            answer='transaction atomic rolls back all writes if an exception happens.',
            category=KBEntry.Category.DATABASE,
        )

    def register(self, username='acmecorp'):
        return self.client.post(
            reverse('register'),
            {
                'username': username,
                'password': 'securepass123',
                'company_name': 'Acme Corp',
                'email': f'{username}@example.com',
            },
            format='json',
        )

    def test_register_creates_company_and_returns_token(self):
        response = self.register()
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('access', response.data)
        self.assertIn('api_key', response.data)
        company = User.objects.get(username='acmecorp').company
        self.assertEqual(company.company_name, 'Acme Corp')
        self.assertEqual(company.role, Company.Role.CLIENT)
        self.assertTrue(company.api_key)

    def test_duplicate_username_returns_400(self):
        self.register()
        response = self.register()
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_returns_token_company_name_and_api_key(self):
        self.register()
        response = self.client.post(reverse('login'), {'username': 'acmecorp', 'password': 'securepass123'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertEqual(response.data['company_name'], 'Acme Corp')
        self.assertTrue(response.data['api_key'])

    def test_invalid_login_returns_401(self):
        response = self.client.post(reverse('login'), {'username': 'bad', 'password': 'wrong'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_kb_query_requires_token(self):
        response = self.client.post(reverse('kb-query'), {'search': 'select_related'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_kb_query_returns_results_and_logs_query(self):
        token = self.register().data['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        response = self.client.post(reverse('kb-query'), {'search': 'select_related'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(QueryLog.objects.count(), 1)

    def test_kb_query_blank_search_returns_400(self):
        token = self.register().data['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        response = self.client.post(reverse('kb-query'), {'search': '   '}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_zero_results_still_logs(self):
        token = self.register().data['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        response = self.client.post(reverse('kb-query'), {'search': 'no-such-term'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['count'], 0)
        self.assertEqual(response.data['results'], [])
        self.assertEqual(QueryLog.objects.count(), 1)

    def test_client_cannot_access_admin_usage_summary(self):
        token = self.register().data['access']
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        response = self.client.get(reverse('usage-summary'))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_access_usage_summary(self):
        token = self.register().data['access']
        company = User.objects.get(username='acmecorp').company
        company.role = Company.Role.ADMIN
        company.save(update_fields=['role'])
        QueryLog.objects.create(company=company, search_term='select_related', results_count=1)
        QueryLog.objects.create(company=company, search_term='select_related', results_count=1)
        QueryLog.objects.create(company=company, search_term='transaction atomic', results_count=1)

        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {token}')
        response = self.client.get(reverse('usage-summary'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['total_queries'], 3)
        self.assertEqual(response.data['active_companies'], 1)
        self.assertEqual(response.data['top_search_terms'][0]['search_term'], 'select_related')
        self.assertEqual(response.data['top_search_terms'][0]['count'], 2)
