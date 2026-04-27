from flask import Blueprint, jsonify, request, abort
from data import db_session
from data.news import News

news_api = Blueprint(
    "news_api",
    __name__,
    url_prefix="/api/news"
)


def news_to_dict(news):
    return {
        "id": news.id,
        "title": news.title,
        "content": news.content,
        "user_id": news.user_id,
        "is_private": news.is_private
    }


@news_api.get("/")
def get_news():
    db_sess = db_session.create_session()
    news = db_sess.query(News).all()
    return jsonify([news_to_dict(n) for n in news])


@news_api.get("/<int:news_id>")
def get_one_news(news_id):
    db_sess = db_session.create_session()
    news = db_sess.get(News, news_id)

    if not news:
        abort(404)

    return jsonify(news_to_dict(news))


@news_api.post("/")
def create_news():
    data = request.get_json()
    db_sess = db_session.create_session()
    try:
        news = News(
            title=data["title"],
            content=data["content"],
            user_id=data["user_id"],
            is_private=data.get("is_private", False)
        )
    except Exception:
        return jsonify({"status": "error"})
    db_sess.add(news)
    db_sess.commit()

    return jsonify({"status": "ok", "id": news.id})


@news_api.delete("/<int:news_id>")
def delete_news(news_id):
    db_sess = db_session.create_session()
    news = db_sess.get(News, news_id)
    if not news:
        abort(404)
    db_sess.delete(news)
    db_sess.commit()

    return jsonify({"status": "deleted"})