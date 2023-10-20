


def find2(lst, x):
    dict = {}
    for i in lst:
        if x-i in lst and x-i not in dict.keys() and x-i!=i:
            dict[i] = x-i
    return dict

def find3(lst, x):
    dict = {}
    for i in range(len(lst)):
        d2 = find2(lst[i+1:],x-lst[i])
        dict[lst[i]] = d2.items()
    return dict



lst = [1,2,3,4,5]
x = 7

print(find3(lst,x))