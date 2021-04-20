#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import raycomputing as rc
import tkinter as tk
from math import cos, sin, pi  # , floor, ceil
from copy import deepcopy


data = {'camera': [0.5, 0.5, 1.5, 0.0000000000001, 0.0000000000001],  # позиц камеры {x,y,z, угол в xOy, угол в xOz}
        'render_distance': 10,  # глубина отрисовки в метрах (блоках)
        'chunk_info_size': 10,  # количество блоков на одной оси чанка (кубический)
        'reflection_number': 0,  # количество отражений {0 - без отраж, луч сразу берёт цвет соответств блока}

        'fov_degrees': 90,  # градусов горизонтальный обзор = default 90
        'rays_x': 16 * 8,  # лучей по горизонтали = default 160
        'rays_y': 9 * 8,  # лучей по вертикали = default 90

        'initial_screen_width': 1280,  # изначальный размер окна

        'world_info': {},  # координаты_чанка: чанк ('-1 13 3': chunk_info)
        'skybox': [{'general': ((176, 198, 255, 255), 0, 255, 255, (128, 128, 255))}, 100],

        'UV_size': 16,

        'block': {  # массив материалов блоков, включающих пути на все карты для различных полигонов
            # блок травы (сверху - трава, снизу - земля, по краям - переходный)
            'grass': {'general': ('grass_side', 'grass_side_m', 'grass_side_r', 0, 'grass_side_n'),
                      (2, -1): ('grass_top', 0, 255, 0, 'grass_top_n'),
                      (2, 1): ('dirt', 'dirt_m', 'dirt_r', 0, 'dirt_n'),
                      'HP': 1},
            # блок земли (одинаков по сторонам)
            'dirt': {'general': ('dirt', 'dirt_m', 'dirt_r', 0, 'dirt_n'),
                     'HP': 2},
            # блок ствола дуба (сверху и снизу - срез, по краям - кора)
            'oak_log': {'general': ('oak_log', 0, 255, 0, 'oak_log_n'),
                        (2, -1): ('oak_log_top', 0, 255, 0, 'oak_log_top_n'),
                        (2, 1): ('oak_log_top', 0, 255, 0, 'oak_log_top_n'),
                        'HP': 3}
            }
        }

# chunk_info = # 10 x 10 x 10 of block_info; (X -> Y -> Z)

# block_info = карты материала полигона, ХП блока. .PNG писать не нужно, оно ставится автоматически
# [{'general': ('rgb_map.png', 'metallic_map.png', 'roughness_map.png', 'emissive_map.png', 'normal_map.png')}, 100]
# Карты = {текстура RGBA, зеркальность (0x6..Fx6), шероховатость (0x6..Fx6), светимость (0x6..Fx6), карта нормалей}

# Массив пустой, то нет блока. Если нет текстуры, то вместо пути на неё указывается hex-цвет всего полигона.
# По умолчанию запрашивается материал отдельного полигона блока, если его нет - берётся материал general.


rays_x_array = []
rays_y_array = []


# функция первоначального задания настроек расчёта рейтрейсинга и рендеринга
def presetting_settings():
    fov = (data['fov_degrees'] * pi) / 180  # обзор в радианах
    ray_angle = fov / (data['rays_x'] - 1)  # угол между соседними лучами в радианах (по вертикали такой же)

    half_x_fov = fov / 2  # половина обзора по горизонтали, то есть отклонение в одну сторону от середины в радианах
    half_y_fov = fov * 0.5625 / 2  # половина обзора по вертикали

    global rays_x_array  # массив значений углов лучей по горизонтали
    for i in range(data['rays_x']):
        rays_x_array.append((half_x_fov - (ray_angle * i)))  # * (cos(half_x_fov - (ray_angle * i)))
    global rays_y_array  # массив значений углов лучей по вертикали
    for j in range(data['rays_y']):
        rays_y_array.append((half_y_fov - (ray_angle * j)))  # * (cos(half_y_fov - (ray_angle * j)))

    window_scale = (data['initial_screen_width'] // data['rays_x'])\
        if data['rays_x'] <= data['initial_screen_width'] else 1

    data['screen'] = [window_scale, int(window_scale * data['rays_x']), int(window_scale * data['rays_y']),
                      int(data['rays_x']), int(data['rays_y'])]

#
# # функция создания визуальных элементов
# def window_creating():
#


# функция простой генерации начального мира из нескольких чанков
def world_creating():
    data['world_info'].clear()

    chunk_distance = int(data['render_distance'] // data['chunk_info_size']) + 1
    for x in range(-chunk_distance, chunk_distance):
        for y in range(-chunk_distance, chunk_distance):
            for z in range(-chunk_distance, chunk_distance):
                data['world_info'][x, y, z] = generate_chunk(x, y, z)


# функция создания чанка на основе его глобальных координат (передаёт список из чанка и его координат
def generate_chunk(x_ch, y_ch, z_ch):  # координаты чанка
    chunk = []

    if z_ch < 0:  # ниже горизонта - должны быть блоки земли
        chunk.clear()
        for x in range(data['chunk_info_size']):
            chunk_y = []
            for y in range(data['chunk_info_size']):
                chunk_z = []
                for z in range(data['chunk_info_size']):
                    chunk_z.append([data['block']['dirt'], data['block']['dirt']['HP']]  # земля
                                   if z < 9 else [data['block']['grass'], data['block']['grass']['HP']])  # трава
                chunk_y.append(chunk_z)
            chunk.append(chunk_y)

    else:  # чанк выше поверхности земли (все блоки пустые)
        chunk.clear()
        for x in range(data['chunk_info_size']):
            chunk_y = []
            for y in range(data['chunk_info_size']):
                chunk_z = []
                for z in range(data['chunk_info_size']):
                    chunk_z.append([])  # создаём пустой блок
                chunk_y.append(chunk_z)
            chunk.append(chunk_y)

    return chunk


def window_resize(event):
    if (event.keysym == "plus") and (data['screen'][2] < 950):
        data['screen'][0] += 1
    elif (event.keysym == "minus") and (data['screen'][0] > 1):
        data['screen'][0] -= 1
    data['screen'][1] = data['rays_x'] * data['screen'][0]
    data['screen'][2] = data['rays_y'] * data['screen'][0]
    canvas.config(width=data['screen'][1], height=data['screen'][2])
    play()


# функция расчёта факта столкновения при следующем движении камеры
# def collision(displacement):  # true - будет столкновение, false - не будет
#     is_collision = False
#     for w in range(len(walls)):
#         massive = [[cos(displacement[1]), walls[w][0][0] - walls[w][1][0]],
#                    [sin(displacement[1]), walls[w][0][1] - walls[w][1][1]]]
#         vector_k = [walls[w][0][0] - camera[0], walls[w][0][1] - camera[1]]
#
#         det = massive[0][0] * massive[1][1] - massive[0][1] * massive[1][0]
#         if det == 0:
#             print("Определитель равен 0")
#         inv_matrix = [[massive[1][1] / det, (-1) * massive[0][1] / det],
#                       [(-1) * massive[1][0] / det, massive[0][0] / det]]
#
#         vector_u = [inv_matrix[0][0] * vector_k[0] + inv_matrix[0][1] * vector_k[1],  # distance
#                     inv_matrix[1][0] * vector_k[0] + inv_matrix[1][1] * vector_k[1]]  # lambda
#
#         if (0 <= vector_u[1] <= 1) and (0 < vector_u[0] <= 1.1 * displacement[0]):
#             is_collision = True
#
#     return is_collision


# функция вычисления вектора перемещения и самого движения камеры
def moving(event, speed=0.1, rotation_z=0.05 * pi, rotation_y=0.05 * pi):
    if event.keysym == 'Up':
        if cos(data['camera'][4] + rotation_z) > 0:
            data['camera'][4] += rotation_z
        else:
            data['camera'][4] = 2.5 * pi
    elif event.keysym == 'Down':
        if cos(data['camera'][4] - rotation_z) > 0:
            data['camera'][4] -= rotation_z
        else:
            data['camera'][4] = 1.5 * pi
    elif event.keysym == 'Left':
        data['camera'][3] += rotation_y
    elif event.keysym == 'Right':
        data['camera'][3] -= rotation_y
    else:
        displacement = []
        if event.keycode == 87:  # W
            displacement = [speed, data['camera'][3]]
        elif event.keycode == 65:  # A
            displacement = [speed, data['camera'][3] + (pi / 2)]
        elif event.keycode == 83:  # S
            displacement = [speed, data['camera'][3] + pi]
        elif event.keycode == 68:  # D
            displacement = [speed, data['camera'][3] - (pi / 2)]

        if displacement:
            # if not collision(displacement):
            #     camera[0] += displacement[0] * cos(displacement[1])
            #     camera[1] += displacement[0] * sin(displacement[1])

            data['camera'][0] += displacement[0] * cos(displacement[1])
            data['camera'][1] += displacement[0] * sin(displacement[1])

    play()


# функция создания массива с информацией о всех пикселях
def raytracing():
    ray_array = []  # двумерный массив цветов пикселей
    for x_ray in rays_x_array:
        ray_array_y = []
        for y_ray in rays_y_array:
            ray_array_y.append(rc.ray_computing(data, deepcopy(data['camera']), x_ray, y_ray))
        ray_array.append(ray_array_y)

    return ray_array


# функция построения всего этого на холсте
def rendering(ray_array):
    canvas.delete("all")

    for x in range(data['screen'][3]):
        for y in range(data['screen'][4]):
            canvas.create_line((x * data['screen'][0] + data['screen'][0] // 2, y * data['screen'][0]),
                               (x * data['screen'][0] + data['screen'][0] // 2, (y + 1) * data['screen'][0]),
                               width=data['screen'][0], fill=ray_array[x][y])


# функция пересчёта данных и перестроения
def play():
    rendering(raytracing())


# coded by QWertyIX
if __name__ == '__main__':
    # определяем количество лучей и разрешение окна
    presetting_settings()

    # # создаём окно
    # window_creating()

    root = tk.Tk()
    root.title("Minecraft 2 Remastered")

    root.bind("<plus>", window_resize)
    root.bind("<minus>", window_resize)

    root.bind("<Key>", moving)

    canvas = tk.Canvas(master=root, width=data['screen'][1], height=data['screen'][2],
                       relief=tk.FLAT, borderwidth=-2, bg='black')
    canvas.pack(expand=1, fill=tk.BOTH)

    # создаём мир
    world_creating()

    data['world_info'][0, 0, -1][1][0][9] = []
    data['world_info'][0, 0, -1][2][0][9] = []
    data['world_info'][0, 0, -1][3][0][9] = []
    data['world_info'][0, -1, 0][2][9][0] = [data['block']['oak_log'], data['block']['oak_log']['HP']]

    # while True:
    #     play()
    #     time.sleep(1 - time.time() % 1)

    play()

    root.mainloop()
