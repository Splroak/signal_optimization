import random
def solution(n, k):
    num_count = []
    for i in range(1000):
        sum_num = 0
        digit_l = []
        while sum_num < k:
            if len(digit_l) < n:
                digit = random.randint(0,9)
                digit_l.append(digit)
                sum_num += digit
                if sum_num == k:
                    num_count.append(int(''.join(map(str,digit_l))))
                    while len(digit_l) < n:
                        digit_l.append(0)
                        num_count.append(int(''.join(map(str, digit_l))))
            else:
                break
    return set(num_count)
print(solution(2,4))