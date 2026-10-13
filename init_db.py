from app import create_app, db
from sqlalchemy import text

app = create_app()
with app.app_context():
    db.create_all()

    # Add created_at to customer_profiles if it doesn't exist (schema migration)
    with db.engine.connect() as conn:
        cols = [row[1] for row in conn.execute(text("PRAGMA table_info(customer_profiles)"))]
        if 'created_at' not in cols:
            conn.execute(text(
                "ALTER TABLE customer_profiles ADD COLUMN created_at DATETIME DEFAULT CURRENT_TIMESTAMP"
            ))
            conn.commit()
            print("Added created_at column to customer_profiles")

    print('Database initialised successfully')
