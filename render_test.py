import os
import subprocess
import time

import py_modules.png as png


softimage_root = "C:\\Program Files\\Autodesk\\Softimage 2015"
current_directory = "\\".join(os.path.abspath(__file__).split("\\")[:-1])


def calc_images_delta(pixels_a, pixels_b):
    '''pixels_a and pixels_b are in the format [[row_0, ...], [row_1, ...], ...]
    each row is a plain array of colors r, g, b, a, ...
    we assume that sizeas of the images are the same (it checked before the function called)
    '''
    s = 0
    pixels_count = 0
    for row_index in range(len(pixels_a)):
        row_a = pixels_a[row_index]
        row_b = pixels_b[row_index]
        length = len(row_a) // 4
        pixels_count += length
        for pixel_index in range(length):
            a = row_a[4 * pixel_index: 4 * (pixel_index + 1)]
            b = row_b[4 * pixel_index: 4 * (pixel_index + 1)]
            for channel in range(4):
                s += (a[channel] - b[channel])**2
    s = s / (4 * pixels_count * 255**2)
    return s


def remove_output_and_clear(output_directory, new_files, ref_reader, output_reader):
    ref_reader.file.close()
    output_reader.file.close()
    for file in new_files:
        output_file = output_directory + "\\" + file
        if os.path.exists(output_file):
            os.remove(output_file)


def get_file_names_from_directory(directory):
    return os.listdir(directory)


def get_new_files(pre_files, post_files):
    to_return = []
    for name in post_files:
        if name not in pre_files:
            to_return.append(name)
    return to_return


def make_one_test(log_file, file_path, test_index):
    print("Start test " + str(test_index) + ": " + file_path)
    file_folder = "\\".join(file_path.split("\\")[:-1])
    # get files in the directory before the render
    pre_render_files = get_file_names_from_directory(current_directory + "\\" + file_folder)

    start_time = time.time()
    subprocess.run([softimage_root + "\\Application\\bin\\XSIBATCH.bat",
                    "-render",
                    current_directory + "\\" + file_path],
                   stdout=log_file, stderr=log_file)
    # next all files after the render
    post_render_files = get_file_names_from_directory(current_directory + "\\" + file_folder)
    new_files = get_new_files(pre_render_files, post_render_files)

    if len(new_files) > 0:
        # use as output fle the first new file
        output_directory = current_directory + "\\" + file_folder
        output_file = output_directory + "\\" + new_files[0]
        ref_file = output_directory + "\\" + "ref.png"

        if os.path.exists(ref_file):
            ref_reader = png.Reader(filename=ref_file)
            ref_width, ref_height, ref_raw_pixels, ref_metadata = ref_reader.asRGBA8()

            output_reader = png.Reader(filename=output_file)
            output_width, output_height, output_raw_pixels, output_metadata = output_reader.asRGBA8()

            if ref_width != output_width or ref_height != output_height:
                remove_output_and_clear(output_directory, new_files, ref_reader, output_reader)
                raise Exception(f"Different dismensions. Reference is {ref_width}x{ref_height}, but output is {output_width}x{output_height}")
            else:
                ref_pixels = [[int(v) for v in row] for row in ref_raw_pixels]
                output_pixels = [[int(v) for v in row] for row in output_raw_pixels]

                delta = calc_images_delta(ref_pixels, output_pixels)
                if delta > 0.01:
                    remove_output_and_clear(output_directory, new_files, ref_reader, output_reader)
                    raise Exception("Too big difference between reference and output image: " + str(delta) + ".")
                remove_output_and_clear(output_directory, new_files, ref_reader, output_reader)

                end_time = time.time()
                print("\tSuccessfuly done. Time: " + str(end_time - start_time) + " sec. Image delta: " + str(delta))
        else:
            raise Exception("Reference file doest not exist.")
    else:
        raise Exception("There are no new files after the render.")


def make_tests(scenes_directory, render_log_filename, only_tests=None):
    test_files = []

    for root, dirs, files in os.walk(scenes_directory):
        for file in files:
            if file.endswith("scn") and file[:-4] != "default":
                test_files.append(root + "\\" + file)

    with open(render_log_filename, "w") as log_file:
        for test_index, file_path in enumerate(test_files):
            if only_tests is None or (only_tests is not None and test_index in only_tests):
                make_one_test(log_file, file_path, test_index)
        print("All tests are done.")


if __name__ == "__main__":
    make_tests(scenes_directory="scenes", render_log_filename="render_log.txt", only_tests=None)
