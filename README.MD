# Decorator for running Django object methods as a celery task

Using example 


```python
from decorators import worker_task
from django.db import models
from datetime import datetime
import time
import asyncio 

class Chislo(models.Model):
    chislo = models.IntegerField(verbose_name="Для какого числа считаем",default=0)
    fibonachi = models.PositiveBigIntegerField(verbose_name="Число Фибоначи",default=0)

    def __str__(self):
        return f' {self.chislo} => {self.fibonachi}'
    
########   SYNC EXAMPLE #############
    @worker_task
    def start_calc(self):
        def fibonacci(n):
            if n <= 1:
                return n
            else:
                a, b = 0, 1
                for _ in range(2, n + 1):
                    a, b = b, a + b
                return b
        self.fibonachi = fibonacci(self.chislo)
        self.save() ######
        time.sleep(5)
        return self.pk
    
# ASYNC Exemple
    
    @worker_task
    async def start_calc_async(self):
        def fibonacci(n):
            if n <= 1:
                return n
            else:
                a, b = 0, 1
                for _ in range(2, n + 1):
                    a, b = b, a + b
                return b

        self.fibonachi = fibonacci(self.chislo)
        await self.asave() 
        await asyncio.sleep(10)
        return self.pk

    @classmethod
    async def create_range(cls,_min,_max):
        tasks=[]
        for i in range(_min,_max+1):
            if not await cls.objects.filter(chislo=i).aexists():
                chislo = await cls.objects.acreate(chislo=i)
                await chislo.asave()
                tasks.append(chislo._calc_waiter())
                print(tasks)
            else:
                print(f'Число {i} уже существует')
        await asyncio.gather(*tasks)


    async def _calc_waiter(self):
        print(f"Start calculating {self}")
                ### Run Syns or Async
        #result = self.start_calc()
        result = await self.start_calc_async()
        print(f"End calculating {self}, result={result}")
```
