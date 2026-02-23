from base64 import b64decode
from gzip import decompress
from hashlib import sha1
from pickle import loads
from typing import Callable

data = decompress(b64decode((
    b'H4sIACMDel4C/yVSuY4VMRB8sNyniIkQyUpIqC/38RMvntT27GQEDgiR+HRqhmRatqurq6rn'
    b'78OfdXvcvtxuN0oOYXNJYcI31rPtEfcHTW56dO0sxZYtuLdm80l9DG2TtMWYZOv59g3wNGpq'
    b'AQpKCXVLisbuimqcTuvhop29/IlZQ3XuxxxiTkXytAvlHIfNpi5z7+vF9h1wttbY2CPJnINU'
    b'IQSK3aU83ZR9vfyvt5V4Lxrae8kx2m419tRRpHvyaBI9Du7r1fYScOeiXK+vVtaBBKggZ/Ix'
    b'5hjdZU/xUht0tBmxl1asN5cmIVFqCYepnmdtzllBDgzOorneXsTJPI9KRAVEhXibSfsRIYEH'
    b'hHVIbzCx3m1fTx0tnLVAk+hEmkjRriBjvb9fEGvmyMAT7o0RHiBhxNRqfbhvP055FiTYAngJ'
    b'wZUmtkeFmwZGb0RlhT1F2vp4336drBhzMiEERbpwEKnG4EAf+AtFIOpalgqSQwMFVMg5Ri3L'
    b'UsUN/uucgSPsYgjazz5mh3D8Qq3p+nS/NiDUqNbn+++f/wAo+U3jjgIAAA==')))


def checkType(targetType: object, obj: object) -> object:
    if not isinstance(obj, targetType):
        raise TypeError(f'Expected type {targetType} for {repr(obj)}"')
    return obj
    
class LockSolver():
    def __init__(self):
        global data
        self.tcdict = loads(data)
        self.testans = []
        self.func = None

    def run(self, function: Callable) -> None:
        checkType(Callable, function)
        sampletc = function('12345')
        if checkType(str, sampletc) != '2353':
            raise ValueError(
                f'Your function returned {repr(sampletc)} for token "12345".')

        self.func = function
        for i, tc in enumerate(self.tcdict.keys()):
            res = function(tc[1::2])
            if self.tcdict[tc] is not None and \
                (sha1(res.encode('utf-8')).hexdigest() !=
                 self.tcdict[tc][::-1]):
                raise RuntimeError(f"Failed to open lock #{i+1}, "
                                   "your solution is probably wrong.")
            self.testans.append(res)

    def getPassword(self, uid: str) -> str:
        ans = ''.join(self.testans) + self.func(checkType(str, uid))
        return sha1(ans.encode('utf-8')).hexdigest()


def encrypt(number: int) -> int: return checkType(int, number) >> 23 ^ 2333


# user code space
def solve(token: str) -> str:
    #Change string type to list type
    token_num_list = list(token)

    #Change each string type in the list to a number type
    for i in range(len(token_num_list)):
        token_num_list[i] = int(token_num_list[i])

    #First result
    res1 = 0
    for i in token_num_list:
        res1 += i

    #Second result
    res2 = token_num_list[0] + token_num_list[-2]

    #Third result
    res3 = encrypt(int(token))

    #Add the three results together to form the answer
    ans = res1 + res2 + res3

    #If greater than 674381, the answer needs to be minus 78763
    if (ans > 674361):
        ans -= 78763

    #Return string type answers
    return str(ans)

ls = LockSolver()
ls.run(solve)
print(ls.getPassword("20180627"))
print(ls.getPassword("371871742916034561"))