from app import create_app, db
from app.models import User

app = create_app()

with app.app_context():
    email = input('Enter admin email: ')
    password = input('Enter admin password: ')
    
    # Check if user already exists
    existing_user = User.query.filter_by(email=email).first()
    if existing_user:
        print('Error: User with this email already exists.')
    else:
        admin = User(email=email, role='admin')
        admin.set_password(password)
        db.session.add(admin)
        db.session.commit()
        print('Admin user created successfully!')
