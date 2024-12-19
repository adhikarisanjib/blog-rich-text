from django import forms
from django.contrib.auth import authenticate, password_validation, get_user_model
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _

from .widgets import CustomFileInput


User = get_user_model()


class LoginForm(forms.Form):
    email = forms.EmailField(max_length=255, widget=forms.EmailInput(attrs={"class": "w-full my-2 p-2 bg-gray-100 dark:bg-gray-900 rounded-md border"}))
    password = forms.CharField(max_length=255, widget=forms.PasswordInput(attrs={"class": "w-full my-2 p-2 bg-gray-100 dark:bg-gray-900 rounded-md border"}))

    def clean_email(self):
        email = self.cleaned_data["email"]
        return email.lower()

    def is_valid(self):
        super().is_valid()
        email = self.cleaned_data["email"]
        password = self.cleaned_data["password"]
        user = authenticate(email=email, password=password)
        if user:
            return True
        return False


class RegistrationForm(forms.ModelForm):
    email = forms.EmailField(max_length=127, widget=forms.EmailInput(attrs={"class": "w-full my-2 p-2 bg-gray-100 dark:bg-gray-900 rounded-md border"}))
    password1 = forms.CharField(
        label="Password",
        max_length=255,
        widget=forms.PasswordInput(attrs={"class": "w-full my-2 p-2 bg-gray-100 dark:bg-gray-900 rounded-md border"}),
        help_text=mark_safe(
            """
            <span class="text-sm">Your password can’t be too similar to your other personal information.</span><br>
            <span class="text-sm">Your password must contain at least 8 characters.</span><br>
            <span class="text-sm">Your password can’t be a commonly used password.</span><br>
            <span class="text-sm">Your password can’t be entirely numeric.</span><br>
            """
        ),
    )
    password2 = forms.CharField(
        label="Confirm Password",
        max_length=255,
        widget=forms.PasswordInput(attrs={"class": "w-full my-2 p-2 bg-gray-100 dark:bg-gray-900 rounded-md border"}),
        help_text="Enter the same password as before, for verification.",
    )

    class Meta:
        model = User
        fields = ("avatar", "email", "name", "password1", "password2")
        widgets = {
            "avatar": CustomFileInput(attrs={"class": "w-full my-2 p-2 bg-gray-100 dark:bg-gray-900 rounded-md border"}),
            "name": forms.TextInput(attrs={"class": "w-full my-2 p-2 bg-gray-100 dark:bg-gray-900 rounded-md border"}),
        }

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("The two passwords didnt match.")
        return password2

    def _post_clean(self):
        super()._post_clean()
        # Validate the password after self.instance is updated with form data by super().
        password = self.cleaned_data.get("password2")
        if password:
            try:
                password_validation.validate_password(password, self.instance)
            except forms.ValidationError as error:
                self.add_error("password2", error)

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user


class UserUpdateForm(forms.ModelForm):
    avatar = forms.FileField(widget=CustomFileInput(attrs={"class": "text-black dark:text-white"}))

    class Meta:
        model = User
        fields = ("avatar", "email", "name", "contact_number")
        widgets = {
            "email": forms.EmailInput(attrs={"class": "w-full my-2 p-2 bg-gray-100 dark:bg-gray-900 rounded-md border"}),
            "name": forms.TextInput(attrs={"class": "w-full my-2 p-2 bg-gray-100 dark:bg-gray-900 rounded-md border"}),
            "contact_number": forms.TextInput(attrs={"type": "tel", "class": "w-full my-2 p-2 bg-gray-100 dark:bg-gray-900 rounded-md border"}),
        }

    def save(self, commit=True):
        # Set is_email_verified = False if user changes their email
        instance = super(UserUpdateForm, self).save(commit=False)
        if instance.pk:
            old_instance = User.objects.get(pk=instance.pk)
            if old_instance.email != instance.email:
                instance.is_email_verified = False
        if commit:
            instance.save()
        return instance


class PasswordChangeForm(forms.Form):
    old_password = forms.CharField(
        label=_("Old password"),
        strip=False,
        widget=forms.PasswordInput(attrs={
            "autocomplete": "current-password", 
            "autofocus": True,
            "class": "w-full my-2 p-2 bg-gray-100 dark:bg-gray-900 rounded-md border"
            }
        ),
    )
    new_password1 = forms.CharField(
        label=_("New password"),
        strip=False,
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password", "class": "w-full my-2 p-2 bg-gray-100 dark:bg-gray-900 rounded-md border"}),
    )
    new_password2 = forms.CharField(
        label=_("New password confirmation"),
        strip=False,
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password", "class": "w-full my-2 p-2 bg-gray-100 dark:bg-gray-900 rounded-md border"}),
    )

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def clean_old_password(self):
        """
        Validate that the old_password field is correct.
        """
        old_password = self.cleaned_data["old_password"]
        if not self.user.check_password(old_password):
            raise forms.ValidationError("Incorrect current password.")
        return old_password

    def clean_new_password1(self):
        password = self.cleaned_data.get("new_password1")
        if len(password) <= 8:
            raise forms.ValidationError("Password too short. Must be at least 8 characters.")
        if not password.isalnum():
            raise forms.ValidationError("Password must contain at least one number.")
        # if password.islower():
        #     raise forms.ValidationError("Password must contain at least one uppercase letter.")

    def clean_new_password2(self):
        password1 = self.cleaned_data.get("new_password1")
        password2 = self.cleaned_data.get("new_password2")
        if password1 and password2:
            if password1 != password2:
                raise forms.ValidationError("The two passwords didnt match.")
        password_validation.validate_password(password2, self.user)
        return password2

    def save(self, commit=True):
        password = self.cleaned_data["new_password1"]
        self.user.set_password(password)
        if commit:
            self.user.save()
        return self.user


class PasswordResetRequestForm(forms.Form):
    email = forms.EmailField(max_length=127, widget=forms.EmailInput(attrs={"class": "w-full my-2 p-2 bg-gray-100 dark:bg-gray-900 rounded-md border"}))

    def clean_email(self):
        email = self.cleaned_data["email"]
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            user = None
        if not user:
            raise forms.ValidationError("Email not registered in our database.")


class PasswordResetForm(forms.Form):
    password1 = forms.CharField(
        label=_("New password"),
        strip=False,
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password", "class": "w-full my-2 p-2 bg-gray-100 dark:bg-gray-900 rounded-md border"}),
    )
    password2 = forms.CharField(
        label=_("New password confirmation"),
        strip=False,
        widget=forms.PasswordInput(attrs={"autocomplete": "new-password", "class": "w-full my-2 p-2 bg-gray-100 dark:bg-gray-900 rounded-md border"}),
    )

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2:
            if password1 != password2:
                raise forms.ValidationError("The two passwords didnt match.")
        password_validation.validate_password(password2, self.user)
        return password2

    def save(self, commit=True):
        password = self.cleaned_data["password1"]
        self.user.set_password(password)
        if commit:
            self.user.save()
        return self.user
    