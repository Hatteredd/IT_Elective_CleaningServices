# CleanHome PH

Standard-library-only Tkinter app.

## Run
```
python main.py
```

## First run
Create first admin via Create Admin Account screen. No accounts seeded. Customers sign up. Passwords hashed with PBKDF2-HMAC-SHA256.

## Password reset
```
python -m cleanhome.reset_password --list
python -m cleanhome.reset_password --email user@example.com
python -m cleanhome.reset_password --email user@example.com --generate
```

## Tests
```
python -m unittest discover -s cleanhome/tests -t .
python -m cleanhome.tests.ui.harness
```

## Config
Edit cleanhome/config.py and cleanhome/theme.py. Backup cleanhome.db while closed.
