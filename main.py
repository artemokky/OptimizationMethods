import copy # для создания глубоких копий списков
import numpy as np
from scipy.optimize import linprog # для проверки решения
from itertools import combinations
from simplex import simplex

"""
Чтение файла. Сохраняем систему.
Предполагается, что в строке, начинающейся с goal_gunc, записана целевая функция.
В строке, начинающейся с idx, записаны индексы переменных, имеющих ограничение на знак >= 0.
"""
def read_file(filename):
    system = []
    sign = []
    goal_func = []
    idx = []
    with open(filename, "r") as f:
        for line in f.readlines():
            expression = line.split()
            if expression[0] == "goal_func":
                expression.remove("goal_func")
                for value in expression:
                    goal_func.append(float(value))
                continue
            if expression[0] == "idx":
                expression.remove("idx")
                for value in expression:
                    idx.append(int(value))
                continue
            clean_data = []
            for value in expression:
                if value.isdigit() or value[0] == '-':
                    clean_data.append(float(value))
                else:
                    sign.append(value)
            system.append(clean_data)
    return system, sign, goal_func, idx


def to_canonical(system, sign, goal_func, idx):
    print('to_canonical: ')
    # копирование данных, чтобы исходные остались прежними
    copy_sign = copy.deepcopy(sign)
    copy_system = copy.deepcopy(system)
    copy_idx = copy.deepcopy(idx)
    copy_goal_func = copy.deepcopy(goal_func)
    # приводим к канонической форме
    # сначала заменяем все знаки на равенства
    for i in range(len(copy_system)):
        if copy_sign[i] == '<=':
            for j in range(len(copy_system)):
                if j == i:
                    copy_system[j].insert(-1, 1.0)
                    copy_idx.append(len(copy_system[j]) - 2)
                else:
                    copy_system[j].insert(-1, 0.0)
            copy_goal_func.append(0.0)
            copy_sign[i] = '='
        if copy_sign[i] == '>=':
            for j in range(len(copy_system)):
                if j == i:
                    copy_system[j].insert(-1, -1.0)
                    copy_idx.append(len(copy_system[j]) - 2)
                else:
                    copy_system[j].insert(-1, 0.0)
            copy_goal_func.append(0.0)
            copy_sign[i] = '='
    # теперь переменные без ограничения на знак заменяем новыми
    # в том числе в ф-ии цели
    to_delete = []
    for i in range(len(copy_system[0]) - 1):
        if i not in copy_idx:
            # значит на знак нет ограничения
            for j in range(len(copy_system)):  # заменяем переменную без ограничения на u-v
                copy_system[j].insert(-1, copy_system[j][i])
                copy_system[j].insert(-1, -copy_system[j][i])
            copy_goal_func.insert(-1, copy_goal_func[i])
            copy_goal_func.insert(-1, -copy_goal_func[i])
            to_delete.append(i)
    to_delete = to_delete[::-1]
    for i in range(len(copy_system)):
        for j in to_delete:
            copy_system[i].pop(j)
    for j in to_delete:
        copy_goal_func.pop(j)
    copy_idx = [i for i in range(len(copy_system[0]) - 1)]
    return copy_system, copy_sign, copy_goal_func, copy_idx


def direct_to_dual(system, sign, goal_func, idx):
    dual_func = []
    dual_idx = []
    dual_sign = []
    for exp in system:
        dual_func.append(exp[-1])

    # создаем двойственную систему
    dual_system = list(map(list, zip(*system))) #транспонированная матрица
    dual_system.pop(-1)
    for i in range(len(dual_system)):
        dual_system[i].append(goal_func[i]) # добавляем свободные члены
        if i in idx: # и смотрим знаки новой системы
            dual_sign.append('<=')
        else:
            dual_sign.append('=')
        if sign[i] == '>=':
            dual_idx.append(i)
        if sign[i] == '<=':
            dual_idx.append(-i) # если idx отрицательный, значит x[i] <= 0, если idx положит, то x[i] >= 0
    return dual_system, dual_sign, dual_func, dual_idx

EPS = 0.000000001

def get_basis_matrs(A : np.ndarray):
    N = A.shape[0]
    M = A.shape[1]

    basis_matrs = []
    basis_combinations_indexes = []
    all_indexes = [i for i in range(M)]

    for i in combinations(all_indexes, N):
        basis_matr = A[:, i]
        if np.linalg.det(basis_matr) != 0:
            basis_matrs.append(basis_matr)
            basis_combinations_indexes.append(i)
        #basis_matrs.append(basis_matr)
        #basis_combinations_indexes.append(i)

    return basis_matrs, basis_combinations_indexes

def get_all_possible_vectors(A : list, b : list):
    N = len(A[0])
    M = len(A)
    vectors = []

    if M >= N:
        return vectors
    else:
        basis_matrs, basis_combinations_indexes = get_basis_matrs(np.array(A))

    for i in range(len(basis_matrs)):
        solve = np.linalg.solve(basis_matrs[i], b)
        if (len(solve[solve < -1 * EPS]) != 0) or (len(solve[solve > 1e+15]) != 0):
            continue

        vec = [0 for i in range(N)]
        for j in range(len(basis_combinations_indexes[i])):
            vec[basis_combinations_indexes[i][j]] = solve[j]
        vectors.append(vec)
    return vectors


def solve_brute_force(A : list, b : list, c : list):
    vectors = get_all_possible_vectors(A, b)
    if len(vectors) == 0:
        return []

    solution = vectors[0]
    target_min = np.dot(solution, c)

    for vec in vectors:
        if np.dot(vec, c) < target_min:
            target_min = np.dot(vec, c)
            solution = vec

    return solution

def getAb(system):
    A=[]
    b=[]
    for exp in system:
        b.append(exp[-1])
        A.append(exp[:-1])
    return A,b

def print_system(system, sign, goal_func, idx):
    A, b = getAb(system)
    print('A:')
    for exp in A:
        print(exp)

    print('b:')
    for exp in b:
        print(exp, end=' ')
    print('\n')
    print('sign: ', sign)
    print('goal_func: ', goal_func)
    print('idx: ', idx)
    print('\n')





system, sign, goal_func, idx = read_file("task1.txt")
print('---ИСХОДНАЯ ЗАДАЧА---')
print_system(system, sign, goal_func, idx)
print('---КАНОНИЧЕСКАЯ ФОРМА---')
system, sign, goal_func, idx = to_canonical(system, sign, goal_func, idx)
print_system(system, sign, goal_func, idx)
print('---РЕШЕНИЕ МЕТОДОМ ПЕРЕБОРА ОПОРНЫХ ВЕКТОРОВ---')
A, b = getAb(system)
solution = solve_brute_force(A, b, goal_func)
print(solution)
print('---РЕШЕНИЕ СИМПЛЕКС-МЕТОДОМ---')
solution = simplex(goal_func, A, b)
print(solution)


# res = linprog(method='simplex', A_eq=A, b_eq=b, c=c)
# print(res)