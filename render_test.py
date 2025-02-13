import os
import subprocess
import math
import time

import py_modules.png as png


softimage_root = "C:\\Program Files\\Autodesk\\Softimage 2015"
current_directory = "\\".join(os.path.abspath(__file__).split("\\")[:-1])


def calc_delta(a, b):
    return math.sqrt(sum([abs(a[i] - b[i]) for i in range(len(a))]))


def remove_output_and_clear(output_file, ref_reader, output_reader):
    ref_reader.file.close()
    output_reader.file.close()
    if os.path.exists(output_file):
        os.remove(output_file)


def make_one_test(log_file, file_path, test_index):
    print("Start test " + str(test_index) + ": " + file_path)
    start_time = time.time()
    subprocess.run([softimage_root + "\\Application\\bin\\XSIBATCH.bat",
                    "-render",
                    current_directory + "\\" + file_path],
                   stdout=log_file, stderr=log_file)
    file_folder = "\\".join(file_path.split("\\")[:-1])
    output_file = current_directory + "\\" + file_folder + "\\" + "output.1.png"
    ref_file = current_directory + "\\" + file_folder + "\\" + "ref.png"
    if os.path.exists(output_file):
        if os.path.exists(ref_file):
            ref_reader = png.Reader(filename=ref_file)
            ref_width, ref_height, ref_raw_pixels, ref_metadata = ref_reader.asRGBA8()

            output_reader = png.Reader(filename=output_file)
            output_width, output_height, output_raw_pixels, output_metadata = output_reader.asRGBA8()

            if ref_width != output_width or ref_height != output_height:
                remove_output_and_clear(output_file, ref_reader, output_reader)
                raise Exception(f"Different dismensions. Reference is {ref_width}x{ref_height}, but output is {output_width}x{output_height}")
            else:
                ref_pixels = [[int(v) for v in row] for row in ref_raw_pixels]
                output_pixels = [[int(v) for v in row] for row in output_raw_pixels]

                delta_sum = 0.0
                for row_index in range(ref_height):
                    for column_index in range(ref_width):
                        ref_pixel = tuple(ref_pixels[row_index][4 * column_index:4 * (column_index + 1)])
                        out_pixel = tuple(output_pixels[row_index][4 * column_index:4 * (column_index + 1)])
                        delta_sum += calc_delta(ref_pixel, out_pixel)
                if delta_sum > 1.0:
                    remove_output_and_clear(output_file, ref_reader, output_reader)
                    raise Exception("Too big difference between reference and output image: " + str(delta_sum) + ".")
                remove_output_and_clear(output_file, ref_reader, output_reader)

                end_time = time.time()
                print("\tSuccessfuly done. Time: " + str(end_time - start_time) + " sec.")
        else:
            raise Exception("Reference file doest not exist.")
    else:
        raise Exception("Output file doest not created.")


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
