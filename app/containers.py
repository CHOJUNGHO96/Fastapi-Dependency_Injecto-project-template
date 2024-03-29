from celery import Celery
from dependency_injector import containers, providers
from fastapi.requests import Request

from app.apis.v1.auth.login.containers import Container as LoginContainer
from app.apis.v1.auth.refresh_token.containers import Container as RefreshTokenContainer
from app.apis.v1.auth.registration.containers import Container as RegistrationContainer
from app.apis.v1.news.list.containers import Container as NewsListContainer
from app.celery_task.container import Container as CeleryContainer
from app.common.config import get_config
from app.database.conn import Database
from app.database.redis_manger import init_redis_pool
from app.util.logger import LogAdapter


class Container(containers.DeclarativeContainer):
    wiring_config = containers.WiringConfiguration(
        packages=[
            "app.database.redis_manger",
        ],
    )

    # config 의존성 주입
    config = providers.Configuration()
    config.from_dict(get_config().dict())
    conf = config()

    # logging 의존성 주입
    logging = providers.Singleton(LogAdapter, request=Request, response=None, error=None)

    # db 의존성 주입
    db = providers.Singleton(Database, conf=config)

    # Redis 의존성 주입
    redis = providers.Resource(init_redis_pool, conf=config)

    # celery 인스턴스 의존성 주입
    celery_app = providers.Singleton(
        Celery,
        broker=f"redis://:{conf['REDIS_PASSWORD']}@{conf['REDIS_HOST']}:{conf['REDIS_PORT']}/0",
        imports=["app.celery_task.base"],
    )

    # api 의존성 주입
    login_service = providers.Container(LoginContainer, db=db, config=config, redis=redis)
    registration_service = providers.Container(RegistrationContainer, db=db, config=config)
    refresh_token_service = providers.Container(RefreshTokenContainer, db=db, config=config, redis=redis)
    news_list_service = providers.Container(NewsListContainer, db=db)

    # Celery 의존성 주입
    celery_news_crawling = providers.Container(CeleryContainer, db=db, celery_app=celery_app)
