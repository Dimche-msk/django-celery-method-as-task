import asyncio
import inspect
from typing import Tuple, Optional, Any
from celery import shared_task
from functools import wraps
from asgiref.sync import async_to_sync, sync_to_async
from celery.bin.result import result
import logging
logger = logging.getLogger(__name__)


def worker_task(func)-> Tuple[Any, Optional[str]]:
    """
    Декоратор, который оборачивает метод модели и запускает его в Celery task
    ВАЖНО ВОЗВРАЩАЕТ РЕЗУЛЬТАТ И ОШИБКУ (во втором параметре)
    предоставляет возможность асинхронного ожидания результата.
    Метод модели может быть sync или async - не важно
    TODO Не тестировалось с @classmethod
    """
    @wraps(func)
    def wrapper(obj,  from_worker=False, *args, **kwargs):
        if from_worker:
            # Синхронный ИЛИ асинхронный вызов функции из модели, если from_worker=True
            if inspect.iscoroutinefunction(func):
                return async_to_sync(func)(obj, *args, **kwargs)
            else:
                return func(obj, *args, **kwargs)
        else:
            # Асинхронный запуск Celery task и ожидание результата
            return _async_run(obj, func, *args, **kwargs)  # Возвращаем корутину
    return wrapper


async def _async_run(obj, func, *args, **kwargs):
    """
    Запускает Celery task асинхронно и ожидает результат.
    """
    task = _inside_worker_task.delay(
        model_name=f"{obj.__class__.__module__.split('.')[0]}.{obj.__class__.__name__}",
        method_name=func.__name__,
        instance_pk=obj.pk,
        *args,
        **kwargs,
    )
    _result = await sync_to_async(task.get)()  # Асинхронно ждем результат
    return _result

@shared_task
def _inside_worker_task(model_name, method_name, instance_pk, *args, **kwargs):
    """
    Celery task, которая выполняет метод модели и возвращает результат SYNC результат или ошибку!!!!
    """
    error = None
    _result = None
    from django.apps import apps

    try:
        model_class = apps.get_model(model_name)
        instance = model_class.objects.get(pk=instance_pk)
        method = getattr(instance, method_name)
        # Выполняем метод модели
        _result = method(from_worker=True, *args, **kwargs)
    except Exception as e:
        _result = None
        error = str(e)
    return _result, error


