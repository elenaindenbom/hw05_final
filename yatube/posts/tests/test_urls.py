from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase, Client
from posts.models import Group, Post
from http import HTTPStatus

User = get_user_model()


class StaticURLTests(TestCase):
    def setUp(self):
        self.guest_client = Client()

    def test_homepage(self):
        response = self.guest_client.get('/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def tearDown(self):
        cache.clear()


class PostsURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.guest_client = Client()
        cls.user = User.objects.create_user(username='HasNoName')
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)
        cls.author = User.objects.create_user(username='author')
        cls.authorized_client_author = Client()
        cls.authorized_client_author.force_login(cls.author)
        Group.objects.create(
            slug='test-slug'
        )
        Post.objects.create(
            author=cls.author
        )

    def tearDown(self):
        cache.clear()

    def test_public_pages_url_exists_at_desired_location(self):
        """Общедоступные страницы доступны любому пользователю."""
        urls = [
            '/',
            '/group/test-slug/',
            '/profile/HasNoName/',
            '/posts/1/',
        ]
        for url in urls:
            with self.subTest(url=url):
                response = self.guest_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_create_list_url_exists_at_desired_location(self):
        """Страница /create/ доступна авторизованному пользователю."""
        response = self.authorized_client.get('/create/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_comments_and_follows_available(self):
        """Комментарии и подписки доступны авторизованному пользователю."""
        urls = [
            '/posts/1/comment/',
            '/profile/author/follow/',
            '/profile/author/unfollow/',
        ]
        for url in urls:
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.FOUND)

    def test_url_redirect_anonymous_on_auth_login(self):
        """Страницы по адресу /create/ и 'posts/<int:post_id>/comment/'
        перенаправит анонимного пользователя на страницу логина.
        """
        url_redirect_names = {
            '/create/': '/auth/login/?next=/create/',
            '/posts/1/comment/': '/auth/login/?next=/posts/1/comment/'
        }
        for address, redirect_addres in url_redirect_names.items():
            with self.subTest(address=address):
                response = self.guest_client.get(address, follow=True)
                self.assertRedirects(
                    response, redirect_addres
                )

    def test_post_edit_list_url_exists_at_desired_location(self):
        """Страница posts/<int:post_id>/edit/ доступна автору поста"""
        response = self.authorized_client_author.get('/posts/1/edit/')
        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_post_edit_list_url_redirect_not_author_on_posts_post_id(self):
        """Страница по адресу /posts/<int:post_id>/edit/ перенаправляет
        пользователя, не являющегося автором поста, на страницу поста.
        """
        response = self.authorized_client.get('/posts/1/edit/', follow=True)
        self.assertRedirects(response, '/posts/1/')

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        url_templates_names = {
            '/': 'posts/index.html',
            '/group/test-slug/': 'posts/group_list.html',
            '/profile/author/': 'posts/profile.html',
            '/posts/1/': 'posts/post_detail.html',
            '/create/': 'posts/create_post.html',
            '/posts/1/edit/': 'posts/create_post.html'
        }
        for address, template in url_templates_names.items():
            with self.subTest(address=address):
                response = self.authorized_client_author.get(address)
                self.assertTemplateUsed(response, template)

    def test_unexisting_page(self):
        response = self.guest_client.get('/unexisting_page/')
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
