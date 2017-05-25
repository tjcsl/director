from django.contrib.auth.decorators import user_passes_test

superuser_required = user_passes_test(lambda u: not u.is_anonymous and u.is_superuser)
