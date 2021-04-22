#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from PIL import Image


#  По умолчанию значение 255 Альфа-канала соответствует полной непрозрачности, но в A- и AMR-текстуре
#             для удобства 255 (белый) соответствует полной светопропускаемости материала


# функция создания AMR-текстуры
def main(filename, size, a_default=None, m_default=None, r_default=None):  # имя файла без расширения и индексов;
    # размер стороны квадратной картинки; значения A, M, R-каналов, если их значения постоянны и не имеют карт
    # изменим формат integer на cortege
    size = (size, size)
    # открываем изображения, из которых берём Alpha, Metallic, Roughness-каналы
    a_ch = Image.open(f"materials/redactor/{filename}.png") if not a_default else None
    m_ch = Image.open(f"materials/redactor/{filename}_m.png") if not m_default else None
    r_ch = Image.open(f"materials/redactor/{filename}_r.png") if not r_default else None
    # проверяем существование палитр (8-битные кодировки и меньше)
    palette_a = a_ch.getpalette() if not a_default else None
    palette_m = m_ch.getpalette() if not m_default else None
    palette_r = r_ch.getpalette() if not r_default else None

    # создаём новый файл текстуры
    amr = Image.new('RGB', size)
    # перебираем пиксели
    for x in range(size[0]):
        for y in range(size[1]):
            # вычисляем компоненты Alpha, Metallic, Roughness-каналов для каждого пикселя из перебора
            # если палитра существует, то берём значение из 8-битного формата, иначе берём из 32-битного формата
            a = a_default if a_default else \
                (palette_a[3 * a_ch.getpixel((x, y))]) if palette_a else (255 - a_ch.getpixel((x, y))[3])
            m = m_default if m_default else \
                (palette_m[3 * m_ch.getpixel((x, y))]) if palette_m else m_ch.getpixel((x, y))[0]
            r = r_default if r_default else \
                (palette_r[3 * r_ch.getpixel((x, y))]) if palette_r else r_ch.getpixel((x, y))[0]
            # создаём на новой текстуре пиксель со значениями Alpha, Metallic, Roughness-каналов
            amr.putpixel((x, y), (a, m, r))
    # сохраняем готовую AMR-текстуру
    amr.save(f"materials/redactor/{filename}_amr.png")


# coded by QWertyIX
if __name__ == '__main__':
    main(filename='grass_side', size=16, a_default=None, m_default=None, r_default=None)
