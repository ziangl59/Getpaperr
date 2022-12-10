# from GetPapers import get_links
from time import time, sleep
from GetPapers_ver20 import main_get



def main():
    theme = input("输入主题，空格分隔\n")
    num = str(input("输入获取文章数量，10的倍数，默认30\n"))
    start_time = time()
    number, page = revise_number(num)
    theme = revise_theme(theme)
    print("您要获取的主题是：%s" % theme)
    print("您要获取的数量是：%i" % number)
    main_get(theme, page)
    end_time = time()
    print("总用时 %.5f s" % (end_time-start_time))
    for i in range(5):
        sleep(1)
        print("\r程序将在 %i s后退出" % (5-i))


# 判断输入的数量为数字并转化为整形
def revise_number(number: str):
    if len(number) == 0:
        number = 30
    elif not number.isdigit():
        number = input("输入有误，请重新输入\n")
    elif int(number) <= 0:
        number = input("输入有误，请重新输入\n")
    elif number.isdigit():
        number = int(number)
    page = int(number/10)
    if page == 0:
        page = 4
    number = page*10
    return number, page


# 修改主题以适合网址
def revise_theme(theme):
    theme = theme.split()
    theme = "+".join(theme)
    return theme
# 后续加入溯源，ip代理




if __name__ == '__main__':
    main()
