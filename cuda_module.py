#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pycuda.driver as drv
drv.init()


# функция предварительной настройки железа
def cuda_setting_up():
    if drv.Device.count() > 1:  # найдено больше 1 видеокарты
        # для сравнения возьмём первую
        best_dev = drv.Device(0)
        print("Обнаружены видеокарты:")
        # перечисляем найденные видеокарты по очереди
        for i in range(drv.Device.count()):
            # записываем в переменную всю инфу о рассматриваемой видеокарте
            dev = drv.Device(i)
            # печатаем название и объём видеопамяти рассматриваемой видеокарты
            print(f"\t{dev.name()} ({dev.total_memory() // (1024 ** 3)} GB)")
            # если видеокарта самая мощная из всех, сохраняем всю инфу о ней
            if best_dev.compute_capability() < dev.compute_capability():
                best_dev = drv.Device(i)
        print(f"Используется видеокарта {best_dev.name()}")
    elif drv.Device.count() == 1:  # найдена 1 видеокарта
        dev = drv.Device(0)
        print(f"Используется видеокарта {dev.name()} ({dev.total_memory() // (1024 ** 3)} GB)")
    else:  # видеокарты не найдено
        print("Видеокарта не обнаружена")
