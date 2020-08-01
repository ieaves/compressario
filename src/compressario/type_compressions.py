from visions import Integer, Float, String, Object, Complex, Boolean, Categorical, DateTime
import numpy as np


class TypeCompressor:
    def __init__(self):
        self.compression_map = {
            Integer: compress_integer,
            Float: compress_float,
            Complex: compress_complex,
            Object: compress_object,
            DateTime: compress_datetime,
            String: compress_object
        }
    
    def compress(self, series, dtype):
        return self.compression_map.get(dtype, lambda x: x)(series)


def type_tester(minv, maxv, info_func):
    def inner(dtype):
        type_info = info_func(dtype)
        return minv >= type_info.min and maxv <= type_info.max
    return inner


def get_compressed_type(type_options, tester):
    for test_type in type_options:
        if tester(test_type):
            return test_type


def compress_float(series):
    minv, maxv = series.min(), series.max()
    tester = type_tester(minv, maxv, np.finfo)
    test_types = [np.float16, np.float32, np.float64]
    
    compressed_type = get_compressed_type(test_types, tester)
    return series.astype(compressed_type)


def compress_integer(series):
    minv, maxv = series.min(), series.max()
    tester = type_tester(minv, maxv, np.iinfo)
    if minv >= 0:
        test_types = [np.uint8, np.uint16, np.uint32, np.uint64]
    else:
        test_types = [np.int8, np.int16, np.int32, np.int64]
    
    compressed_type = get_compressed_type(test_types, tester)      
    return series.astype(compressed_type)


def compress_complex(series):
    if series.dtype == np.complex64:
        return series

    real_part = series.apply(lambda x: x.real)
    imag_part = series.apply(lambda x: x.imag)

    minv_real, maxv_real = real_part.min(), real_part.max()
    minv_imag, maxv_imag = imag_part.min(), imag_part.max()

    test_real = type_tester(minv_real, maxv_real, np.finfo)
    test_imag = type_tester(minv_imag, maxv_imag, np.finfo)

    if test_real(np.float32) and test_imag(np.float32):
        return series.astype(np.complex64)
    
    return series


def compress_object(series):
    try:
        new_series = series.astype('category')
        if new_series.memory_usage() < series.memory_usage():
            return new_series
    except:
        pass
    return series


def compress_datetime(series):
    try:
        new_series = series.astype('category')
        if new_series.memory_usage() < series.memory_usage():
            return new_series
    except:
        pass
    return series

# TODO: Create a period type which checks if dates fall in well defined interval ranges?
# we can get substantial memory savings from compressing these.