Group 4

# Instructions:

### 1. **Install Dependencies:**
Input or copy & paste into python terminal: *pip install -r requirements.txt*

### 2. **Pre-populate Database**
Toggle python shell by typing in terminal: *python manage.py shell*

In shell input:
```
from django.contrib.auth.models import User

user = User.objects.create_user(username="new_user", password="secure_pass123") *change username and pass to whatever you want.
print(user.password)  # Outputs a hashed password to verify if hashed.

*also make one for Admin where username is admin and password is admin
```

next assign roles RBAC
```
from django.contrib.auth.models import Group, User

admin_group = Group.objects.create(name="Admin") * Optionnal code line, Create group if non-existent
user = User.objects.get(username="admin_user") *Select user to add
user.groups.add(admin_group) *add selected user to group
```

exit shell using: *exit()*
### 3. **Migrate Changes**
In terminal type:
```python
python manage.py migrate
python manage.py makemigrations
```
### 4. **Run server**
Run server using: *python manage.py runserver_plus --cert-file cert.pem --key-file key.pem*
