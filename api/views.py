from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.db import IntegrityError, transaction
from django.db.models import Count, Q
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from .models import KBEntry, QueryLog
from .permissions import IsAdminUser


def build_access_token(user):
    refresh = RefreshToken.for_user(user)
    return str(refresh.access_token)


class RegisterView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        username = str(request.data.get('username', '')).strip()
        password = str(request.data.get('password', '')).strip()
        company_name = str(request.data.get('company_name', '')).strip()
        email = str(request.data.get('email', '')).strip()

        errors = {}
        if not username:
            errors['username'] = 'This field is required.'
        if not password:
            errors['password'] = 'This field is required.'
        if not company_name:
            errors['company_name'] = 'This field is required.'
        if not email:
            errors['email'] = 'This field is required.'
        if User.objects.filter(username=username).exists():
            errors['username'] = 'Username already exists.'
        if errors:
            return Response({'errors': errors}, status=status.HTTP_400_BAD_REQUEST)

        try:
            with transaction.atomic():
                user = User.objects.create_user(
                    username=username,
                    password=password,
                    email=email,
                )
                company = user.company
                company.company_name = company_name
                company.save(update_fields=['company_name'])
        except IntegrityError:
            return Response(
                {'error': 'Username already exists.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(
            {
                'username': user.username,
                'company_name': company.company_name,
                'api_key': company.api_key,
                'access': build_access_token(user),
            },
            status=status.HTTP_201_CREATED,
        )


class LoginView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        username = str(request.data.get('username', '')).strip()
        password = str(request.data.get('password', '')).strip()

        user = authenticate(request, username=username, password=password)
        if user is None:
            return Response(
                {'error': 'Invalid username or password.'},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        try:
            company = user.company
        except Exception:
            return Response(
                {'error': 'Company profile was not found for this user.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return Response(
            {
                'access': build_access_token(user),
                'company_name': company.company_name,
                'api_key': company.api_key,
            },
            status=status.HTTP_200_OK,
        )


class KBQueryView(APIView):
    def post(self, request):
        search_term = str(request.data.get('search', '')).strip()
        if not search_term:
            return Response(
                {'error': 'The search field is required and cannot be blank.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            company = request.user.company
        except Exception:
            return Response(
                {'error': 'Authenticated user does not have a company profile.'},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        with transaction.atomic():
            entries = list(
                KBEntry.objects.filter(
                    Q(question__icontains=search_term) | Q(answer__icontains=search_term)
                ).order_by('id')
            )
            results_count = len(entries)
            QueryLog.objects.create(
                company=company,
                search_term=search_term,
                results_count=results_count,
            )

        results = [
            {
                'id': str(entry.id),
                'question': entry.question,
                'answer': entry.answer,
                'category': entry.category,
            }
            for entry in entries
        ]
        return Response(
            {'search': search_term, 'count': results_count, 'results': results},
            status=status.HTTP_200_OK,
        )


class UsageSummaryView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        total_queries = QueryLog.objects.aggregate(total=Count('id'))['total'] or 0
        active_companies = QueryLog.objects.values('company').distinct().count()
        top_search_terms = list(
            QueryLog.objects.values('search_term')
            .annotate(count=Count('id'))
            .order_by('-count', 'search_term')[:5]
        )

        return Response(
            {
                'total_queries': total_queries,
                'active_companies': active_companies,
                'top_search_terms': top_search_terms,
            },
            status=status.HTTP_200_OK,
        )
