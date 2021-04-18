#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import tkinter as tk
from math import cos, sin, pi, floor, ceil
from copy import deepcopy

camera = [0.5, 0.5, 1.5, 0.0000000000001, 0.0000000000001]  # позиция камеры {x, y, z, угол в xOy, угол в xOz}
skybox = ['#b0c6fe', 1, 1, 0, 100]

render_distance = 20  # глубина отрисовки в метрах (блоках)
chunk_info_size = 10  # количество блоков на одной оси чанка (кубический)
reflection_number = 0  # количество отражений {0 - без отражений, луч сразу берёт цвет соответствующего блока}

fov_degrees = 90  # градусов горизонтальный обзор = default 90
rays_x = 16 * 10  # лучей по горизонтали = default 160
rays_y = 9 * 10  # лучей по вертикали = default 90

initial_screen_width = 1280  # изначальный размер окна

rays_x_array = []
rays_y_array = []
screen = []

# block_info  =  color [hex], transparent [float] (прозрач 0.0 - 1.0 непрозрач),
# шероховатость [float] (гладкий 0.0 - 1.0 шероховатый), светимость [float] (тёмный 0.0 - 1.0 излучающий), HP [int],
# массив пустой = нет блока
# chunk_info  =  # 10 x 10 x 10 of block_info; (X -> Y -> Z)
world_info = {}  # координаты_чанка:чанк ('-1 13 3':chunk_info)


# функция первоначального задания настроек расчёта рейтрейсинга и рендеринга
def presetting_settings():
    fov = (fov_degrees * pi) / 180  # обзор в радианах
    ray_angle = fov / (rays_x - 1)  # угол между соседними лучами в радианах (по вертикали такой же)

    half_x_fov = fov / 2  # половина обзора по горизонтали, то есть отклонение в одну сторону от середины в радианах
    half_y_fov = fov * 0.5625 / 2  # половина обзора по вертикали

    global rays_x_array  # массив значений углов лучей по горизонтали
    for i in range(rays_x):
        rays_x_array.append(half_x_fov - (ray_angle * i))
    global rays_y_array  # массив значений углов лучей по вертикали
    for j in range(rays_y):
        rays_y_array.append(half_y_fov - (ray_angle * j))

    global screen  # масштабируем окно
    window_scale = (initial_screen_width // rays_x) if rays_x <= initial_screen_width else 1
    screen = [window_scale, window_scale * rays_x, window_scale * rays_y, rays_x, rays_y]

#
# # функция создания визуальных элементов
# def window_creating():
#


# функция простой генерации начального мира из нескольких чанков
def world_creating():
    world_info.clear()

    chunk_distance = int(render_distance // chunk_info_size) + 1
    for x in range(-chunk_distance, chunk_distance):
        for y in range(-chunk_distance, chunk_distance):
            for z in range(-chunk_distance, chunk_distance):
                world_info[x, y, z] = generate_chunk(x, y, z)


# функция создания чанка на основе его глобальных координат (передаёт список из чанка и его координат
def generate_chunk(x_ch, y_ch, z_ch):  # координаты чанка
    chunk = []

    if z_ch < 0:  # ниже горизонта - должны быть блоки земли
        chunk.clear()
        for x in range(chunk_info_size):
            chunk_y = []
            for y in range(chunk_info_size):
                chunk_z = []
                for z in range(chunk_info_size):
                    chunk_z.append(['#964b00', 1, 1, 0, 2] if z < 9 else ['#008000', 1, 1, 0, 1])  # земля или трава
                chunk_y.append(chunk_z)
            chunk.append(chunk_y)

    else:  # чанк выше поверхности земли (все блоки пустые)
        chunk.clear()
        for x in range(chunk_info_size):
            chunk_y = []
            for y in range(chunk_info_size):
                chunk_z = []
                for z in range(chunk_info_size):
                    chunk_z.append([])  # создаём пустой блок
                chunk_y.append(chunk_z)
            chunk.append(chunk_y)

    return chunk


def window_resize(event):
    if (event.keysym == "plus") and (screen[2] < 950):
        screen[0] += 1
    elif (event.keysym == "minus") and (screen[0] > 1):
        screen[0] -= 1
    screen[1] = rays_x * screen[0]
    screen[2] = rays_y * screen[0]
    canvas.config(width=screen[1], height=screen[2])
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
        if cos(camera[4] + rotation_z) > 0:
            camera[4] += rotation_z
        else:
            camera[4] = 2.5 * pi
    elif event.keysym == 'Down':
        if cos(camera[4] - rotation_z) > 0:
            camera[4] -= rotation_z
        else:
            camera[4] = 1.5 * pi
    elif event.keysym == 'Left':
        camera[3] += rotation_y
    elif event.keysym == 'Right':
        camera[3] -= rotation_y
    else:
        displacement = []
        if event.keycode == 87:  # W
            displacement = [speed, camera[3]]
        elif event.keycode == 65:  # A
            displacement = [speed, camera[3] + (pi / 2)]
        elif event.keycode == 83:  # S
            displacement = [speed, camera[3] + pi]
        elif event.keycode == 68:  # D
            displacement = [speed, camera[3] - (pi / 2)]

        if displacement:
            # if not collision(displacement):
            #     camera[0] += displacement[0] * cos(displacement[1])
            #     camera[1] += displacement[0] * sin(displacement[1])

            camera[0] += displacement[0] * cos(displacement[1])
            camera[1] += displacement[0] * sin(displacement[1])

    play()


# функция вычисления параметров пересечения луча с плоскостями X
def x_plane_calculating(ray_vector, d):
    t = (d - ray_vector[0]) / (cos(ray_vector[4]) * cos(ray_vector[3]))
    y = ray_vector[1] + t * cos(ray_vector[4]) * sin(ray_vector[3])
    z = ray_vector[2] + t * sin(ray_vector[4])
    return [d, round(y, 12), round(z, 12), t]


# функция вычисления параметров пересечения луча с плоскостями Y
def y_plane_calculating(ray_vector, d):
    t = (d - ray_vector[1]) / (cos(ray_vector[4]) * sin(ray_vector[3]))
    x = ray_vector[0] + t * (cos(ray_vector[4]) * cos(ray_vector[3]))
    z = ray_vector[2] + t * sin(ray_vector[4])
    return [round(x, 12), d, round(z, 12), t]


# функция вычисления параметров пересечения луча с плоскостями Z
def z_plane_calculating(ray_vector, d):
    t = (d - ray_vector[2]) / sin(ray_vector[4])
    x = ray_vector[0] + t * (cos(ray_vector[4]) * cos(ray_vector[3]))
    y = ray_vector[1] + t * (cos(ray_vector[4]) * sin(ray_vector[3]))
    return [round(x, 12), round(y, 12), d, t]


# делаем массив функций для удобного использования
plane_calculating = (x_plane_calculating, y_plane_calculating, z_plane_calculating)


# функция вычисления факта пересечения с какой-то гранью существующего блока
def intersection_computing(ray_vector, d, axis, n, block_info=''):
    # вектор луча; плоскость с которой начинаем проверку; плоскость; направление движения проверки следующих плоскостей;
    # информация о блоке (пока нет пересечения, переменная "" считается False); расстояние от камеры до пересечения.

    # ищем ближайшее пересечение пока не найдём или не выйдем за пределы обзора
    while not block_info:
        # получаем координаты точки пересечения x, y, z и расстояние до неё t
        intersection_data = deepcopy(plane_calculating[axis](ray_vector, d))

        # если пересечение в области отрисовки
        if intersection_data[3] < render_distance:
            # получаем глобальные координаты блока пересечения
            global_block_coordinates = [floor(intersection_data[0]) if axis != 0 else
                                        floor(intersection_data[0]) if cos(ray_vector[3]) > 0 else
                                        floor(intersection_data[0]) - 1,
                                        floor(intersection_data[1]) if axis != 1 else
                                        floor(intersection_data[1]) if sin(ray_vector[3]) > 0 else
                                        floor(intersection_data[1]) - 1,
                                        floor(intersection_data[2]) if axis != 2 else
                                        floor(intersection_data[2]) if sin(ray_vector[4]) > 0 else
                                        floor(intersection_data[2]) - 1]

            # получаем координаты чанка с блоком пересечения
            chunk_coordinates = (int(global_block_coordinates[0] // chunk_info_size),
                                 int(global_block_coordinates[1] // chunk_info_size),
                                 int(global_block_coordinates[2] // chunk_info_size))
            # получаем локальные координаты блока пересечения в конкретном чанке
            block_coordinates = (int(global_block_coordinates[0] % chunk_info_size),
                                 int(global_block_coordinates[1] % chunk_info_size),
                                 int(global_block_coordinates[2] % chunk_info_size))

            # записываем информацию о блоке пересечения (пересечение будет, когда переменная станет равна не [])
            if world_info[chunk_coordinates][block_coordinates[0]][block_coordinates[1]][block_coordinates[2]]:
                block_info = world_info[chunk_coordinates][block_coordinates[0]][block_coordinates[1]][block_coordinates[2]]
            # если нет пересечения, то проверяем следующую плоскость
            d += n
        else:  # прерываем функцию
            return intersection_data[3], [], axis, n, []

    # возвращаем {дистанцию до пересечения, координаты x, y, z пересечения, индекс оси, нормаль, информацию о блоке}
    return intersection_data.pop(-1), intersection_data, axis, n, block_info


# функция вычисления цвета пикселя луча (возвращает строку hex)
def ray_computing(ray_vector, x_ray, y_ray):

    ray_vector[3] += x_ray  # копируем начальное положение камеры, после
    ray_vector[4] += y_ray  # чего адаптируем под конкретный луч

    color_array = []

    for i in range(reflection_number + 1):

        # начинаем проверять пересечения с этой плоскости (свои для каждого направления)
        d_x = floor(ray_vector[0]) if cos(ray_vector[3]) < 0 else ceil(ray_vector[0])
        d_y = floor(ray_vector[1]) if sin(ray_vector[3]) < 0 else ceil(ray_vector[1])
        d_z = floor(ray_vector[2]) if sin(ray_vector[4]) < 0 else ceil(ray_vector[2])

        # получаем массив пересечений с разными плоскостями (элементы = {distance, axis, n, block_info})
        intersection_array = [intersection_computing(ray_vector, d_x, 0, 1 if cos(ray_vector[3]) > 0 else -1),
                              intersection_computing(ray_vector, d_y, 1, 1 if sin(ray_vector[3]) > 0 else -1),
                              intersection_computing(ray_vector, d_z, 2, 1 if sin(ray_vector[4]) > 0 else -1)]

        # копируем информацию о ближайшем пересечении (min distance)
        intersection = deepcopy(min(intersection_array[0], intersection_array[1], intersection_array[2]))

        # если точка пересечения в области отрисовки
        if intersection[0] < render_distance:
            # берём информацию о блоке
            color_array.append(intersection[4])
            # следующие вычисления будем проводить для отражённого луча с таким вектором:
            if i != reflection_number:
                ray_vector = [intersection[1][0], intersection[1][1], intersection[1][2],
                              camera[3] if intersection[2] == 2 else
                              (-camera[3]) if intersection[2] == 1 else (pi - camera[3]),
                              -ray_vector[4]]
        else:
            color_array.append(skybox)

    # для проверки берём просто первый полученный цвет
    color = color_array[0][0]

    return color


# функция создания массива с информацией о всех пикселях
def raytracing():
    ray_array = []  # двумерный массив цветов пикселей
    i = 0

    for x_ray in rays_x_array:
        j = 0
        ray_array_y = []
        for y_ray in rays_y_array:
            ray_array_y.append(ray_computing(deepcopy(camera), x_ray, y_ray))
            j += 1
        ray_array.append(ray_array_y)
        i += 1

    return ray_array


# функция построения всего этого на холсте
def rendering(ray_array):
    canvas.delete("all")

    print(screen)

    for x in range(screen[3]):
        for y in range(screen[4]):
            canvas.create_line((x * screen[0] + screen[0] // 2, y * screen[0]),
                               (x * screen[0] + screen[0] // 2, (y + 1) * screen[0]),
                               width=screen[0], fill=ray_array[x][y])


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

    canvas = tk.Canvas(master=root, width=screen[1], height=screen[2], relief=tk.FLAT, borderwidth=-2, bg='black')
    canvas.pack(expand=1, fill=tk.BOTH)

    # создаём мир
    world_creating()

    world_info[(0, 0, -1)][1][0][9] = []
    world_info[(0, 0, -1)][2][0][9] = []
    world_info[(0, 0, -1)][3][0][9] = []
    world_info[(0, -1, 0)][2][9][0] = ['#964b00', 1, 1, 0, 2]

    # while True:
    #     play()
    #     time.sleep(1 - time.time() % 1)

    play()

    root.mainloop()
