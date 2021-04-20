#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# import main as mn
from math import cos, sin, pi, floor, ceil
from copy import deepcopy
from PIL import Image


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
def intersection_computing(data, ray_vector, d, axis, n, block_info=''):
    # вектор луча; плоскость с которой начинаем проверку; плоскость; направление движения проверки следующих плоскостей;
    # информация о блоке (пока нет пересечения, переменная "" считается False); расстояние от камеры до пересечения.

    # ищем ближайшее пересечение пока не найдём или не выйдем за пределы обзора
    while not block_info:
        # получаем координаты точки пересечения x, y, z и расстояние до неё t
        intersection_data = deepcopy(plane_calculating[axis](ray_vector, d))

        # если пересечение в области отрисовки
        if intersection_data[3] < data['render_distance']:
            # получаем глобальные координаты блока пересечения
            global_block_coordinates = (floor(intersection_data[0]) if axis != 0 else
                                        floor(intersection_data[0]) if cos(ray_vector[3]) * cos(ray_vector[4]) > 0 else
                                        floor(intersection_data[0]) - 1,
                                        floor(intersection_data[1]) if axis != 1 else
                                        floor(intersection_data[1]) if sin(ray_vector[3]) * cos(ray_vector[4]) > 0 else
                                        floor(intersection_data[1]) - 1,
                                        floor(intersection_data[2]) if axis != 2 else
                                        floor(intersection_data[2]) if sin(ray_vector[4]) > 0 else
                                        floor(intersection_data[2]) - 1)

            # получаем координаты чанка с блоком пересечения
            chunk_coordinates = (int(global_block_coordinates[0] // data['chunk_info_size']),
                                 int(global_block_coordinates[1] // data['chunk_info_size']),
                                 int(global_block_coordinates[2] // data['chunk_info_size']))
            # получаем локальные координаты блока пересечения в конкретном чанке
            block_coordinates = (int(global_block_coordinates[0] % data['chunk_info_size']),
                                 int(global_block_coordinates[1] % data['chunk_info_size']),
                                 int(global_block_coordinates[2] % data['chunk_info_size']))

            # записываем информацию о блоке пересечения (пересечение будет, когда переменная станет равна не [])
            if data['world_info'][chunk_coordinates][block_coordinates[0]][block_coordinates[1]][block_coordinates[2]]:
                # получаем информацию о блоке
                block_info = data['world_info'][
                    chunk_coordinates][block_coordinates[0]][block_coordinates[1]][block_coordinates[2]]
            # если нет пересечения, то проверяем следующую плоскость
            d += n
        else:  # прерываем функцию
            return intersection_data[3], [], axis, n, []

    # возвращаем {дистанцию до пересечения, координаты x, y, z пересечения, индекс оси, нормаль, информацию о блоке}
    return intersection_data.pop(-1), intersection_data, axis, n, block_info


# функция вычисления цвета пикселя луча (возвращает строку hex)
def ray_computing(data, ray_vector, x_ray, y_ray):

    ray_vector[3] += x_ray  # копируем начальное положение камеры, после
    ray_vector[4] += y_ray  # чего адаптируем под конкретный луч

    color_array = []

    for i in range(data['reflection_number'] + 1):
        # rgba = ()

        # начинаем проверять пересечения с этой плоскости (свои для каждого направления)
        d_x = floor(ray_vector[0]) if cos(ray_vector[3]) * cos(ray_vector[4]) < 0 else ceil(ray_vector[0])
        d_y = floor(ray_vector[1]) if sin(ray_vector[3]) * cos(ray_vector[4]) < 0 else ceil(ray_vector[1])
        d_z = floor(ray_vector[2]) if sin(ray_vector[4]) < 0 else ceil(ray_vector[2])

        # получаем массив пересечений с разными плоскостями (элементы = {distance, axis, n, block_info})
        intersection_array = (intersection_computing(data, ray_vector, d_x, 0,
                                                     1 if cos(ray_vector[3]) * cos(ray_vector[4]) > 0 else -1),
                              intersection_computing(data, ray_vector, d_y, 1,
                                                     1 if sin(ray_vector[3]) * cos(ray_vector[4]) > 0 else -1),
                              intersection_computing(data, ray_vector, d_z, 2,
                                                     1 if sin(ray_vector[4]) > 0 else -1))

        # копируем информацию о ближайшем пересечении (min distance)
        intersection = min(intersection_array[0], intersection_array[1], intersection_array[2])

        # если точка пересечения в области отрисовки
        if intersection[0] < data['render_distance']:
            # если ключ с особым материалом полигона существует, то берём его, если нет, то берём стандартный
            color_map = intersection[4][0].get((intersection[2], intersection[3]), intersection[4][0]['general'])[0]
            # если в поле color_map указана строка (путь на текстуру), то достаём пиксель из этой текстуры
            if isinstance(color_map, str):
                # получаем локальные координаты в системе полигона блока
                uv_coordinates = (intersection[1][1] % 1, intersection[1][2] % 1) if intersection[2] == 0 else \
                                 (intersection[1][0] % 1, intersection[1][2] % 1) if intersection[2] == 1 else \
                                 (intersection[1][0] % 1, intersection[1][1] % 1)
                # получаем целочисленные координаты пикселя в зависимости от разрешения текстуры
                uv_pixel = (int(uv_coordinates[0] // (1 / data['UV_size'])),
                            data['UV_size'] - 1 - int(uv_coordinates[1] // (1 / data['UV_size'])))
                # получаем RGBA пикселя из нужной текстуры
                rgba = Image.open(f"materials/{color_map}.png").getpixel(uv_pixel)
            else:
                # иначе указано общее значение для всего полигона (r, g, b, a)
                rgba = color_map

            # следующие вычисления будем проводить для отражённого луча с таким вектором:
            if i != data['reflection_number']:
                ray_vector = [intersection[1][0], intersection[1][1], intersection[1][2],
                              ray_vector[3] if intersection[2] == 2 else
                              (-ray_vector[3]) if intersection[2] == 1 else (pi - ray_vector[3]),
                              -ray_vector[4]]
        else:
            rgba = data['skybox'][0]['general'][0]

        color_array.append(f'#{rgba[0]:0>2x}{rgba[1]:0>2x}{rgba[2]:0>2x}')

    # для проверки берём просто первый полученный цвет
    color = color_array[0]

    return color
