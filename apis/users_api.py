from flask import Blueprint, jsonify, request, abort
from data import db_session
from data.users import User

users_api = Blueprint(
    "users_api",
    __name__,
    url_prefix="/api/users"
)


def user_to_dict(user):
    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "about": user.about
    }


@users_api.get("/")
def get_users():
    db_sess = db_session.create_session()
    users = db_sess.query(User).all()

    return jsonify([user_to_dict(u) for u in users])


@users_api.get("/<int:user_id>")
def get_user(user_id):
    db_sess = db_session.create_session()
    user = db_sess.get(User, user_id)

    if not user:
        abort(404)

    return jsonify(user_to_dict(user))


@users_api.post("/")
def create_user():
    data = request.json

    db_sess = db_session.create_session()

    user = User(
        name=data["name"],
        email=data["email"],
        about=data.get("about")
    )

    user.set_password(data["password"])

    db_sess.add(user)
    db_sess.commit()

    return jsonify({"status": "ok", "id": user.id})


@users_api.delete("/<int:user_id>")
def delete_user(user_id):
    db_sess = db_session.create_session()

    user = db_sess.get(User, user_id)

    if not user:
        abort(404)

    db_sess.delete(user)
    db_sess.commit()

    return jsonify({"status": "deleted"})