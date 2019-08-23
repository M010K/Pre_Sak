import os


class Insert_Element():
    """
    向positive.txt和negative.txt插入因素
    """
    def __init__(self):
        self.abs_path = os.path.join(os.getcwd(), 'file')

    def insert_pos(self):
        with open(os.path.join(self.abs_path, 'positive.txt'), 'r+') as f:
            while True:
                element = input('请输入因素:')
                for line in f.readlines():
                    if element == line.replace('\n', ''):
                        print('因素"%s"已经存在' % element)
                        break
                else:
                    print('插入因素"%s"' % element)
                    f.write(element + '\n')
                    break

    def insert_neg(self):
        with open(os.path.join(self.abs_path, 'negative.txt'), 'r+') as f:
            while True:
                element = input('请输入因素:')
                for line in f.readlines():
                    if element == line.replace('\n', ''):
                        print('因素"%s"已经存在' % element)
                        break
                else:
                    print('插入因素"%s"' % element)
                    f.write(element + '\n')
                    break


if __name__ == '__main__':
    IE = Insert_Element()
    # 均为单次插入
    # IE.insert_pos()
    # IE.insert_neg()

