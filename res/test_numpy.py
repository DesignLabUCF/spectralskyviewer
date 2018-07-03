import numpy as np


# def sliceWithPad(arr, indices):
#     shape = tuple(y-x for x,y in indices)
#     subset = np.zeros(shape=shape)
#     print(subset)
#
#     srcIdx = list([max(0, start), min(arr.shape[i], stop)] for i,(start,stop) in enumerate(indices))
#     print(srcIdx)
#     dstIdx = list([start + max(0-start,0), stop + min(arr.shape[i] - stop, 0)] for i,(start,stop) in enumerate(indices))
#     print(dstIdx)
#
#     src = [slice(start,stop,None) for start,stop in srcIdx]
#     print(src)
#     dst = [slice(start, stop, None) for start, stop in dstIdx]
#     print(dst)
#     subset[dst] = arr[src]
#     return subset
#
# my_arr = np.ones((5, 5,))
# print(my_arr, '\n')
# subset = sliceWithPad(my_arr, ((0, 6), (0, 6)))
# print(subset, '\n')
# subset = sliceWithPad(my_arr, ((3, 8), (3, 8)))
# print(subset, '\n')
# subset = sliceWithPad(my_arr, ((-2, 2), (-1, 1)))
# print(subset, '\n')
# subset = sliceWithPad(my_arr, ((-10, -5), (4, 9)))
# print(subset, '\n')


def sliceWithPad(arr, r1, r2, c1, c2):
    subset = np.zeros((r2-r1, c2-c1,))

    sr1 = max(0, r1)
    sr2 = min(arr.shape[0], r2)
    sc1 = max(0, c1)
    sc2 = min(arr.shape[1], c2)
    print((sr1, sr2), (sc1, sc2))

    dr1 = r1 + max(0 - r1, 0)
    dr2 = r2 + min(r2 - arr.shape[0], 0)
    dc1 = c1 + max(0 - c1, 0)
    dc2 = c2 + min(c2 - arr.shape[1], 0)
    print((dr1, dr2), (dc1, dc2))

    subset[dr1:dr2, dc1:dc2] = arr[sr1:sr2, sc1:sc2]
    return subset

arr = np.ones((5, 5,))
print(arr, '\n')
subset = sliceWithPad(arr, 0, 6, 0, 6)
print(subset, '\n')
subset = sliceWithPad(arr, 3, 8, 3, 8)
print(subset, '\n')
subset = sliceWithPad(arr, -2, 2, -1, 1)
print(subset, '\n')
subset = sliceWithPad(arr, -10, -5, 4, 9)
print(subset, '\n')
