from app import flask_app, db

# db.drop_all()
db.create_all()

if __name__ == '__main__':
    flask_app.run(debug=True)