from django.contrib.auth.tokens import PasswordResetTokenGenerator


class AccountActivationTokenGenerator(PasswordResetTokenGenerator):
    def _make_hash_value(self, user, timestamp):
        super()._make_hash_value(user, timestamp)
        email_field = user.get_email_field_name()
        email = getattr(user, email_field, "") or ""
        return f"{user.pk} {user.password} {timestamp} {email}"


account_activation_token = AccountActivationTokenGenerator()
password_reset_token = AccountActivationTokenGenerator()
