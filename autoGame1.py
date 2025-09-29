import time
from datetime import datetime as dt
from enum import Enum, auto
from io import IOBase

import cv2 as c
import keyboard as kb
import numpy as np
import pyautogui as gui

"""
定义BaseBlock
BaseBlock列表将用于引导整个程序的执行  
['imageAddress','if exists do' 'if not exists do','index','nextJump']
当 nextJump ==  'over' 程序执行完毕
"""
""" 
整个流程将被放在一个列表中
其中的每个元素都是一个baseBlock
也就是说，内部每个元素都遵循['imageAddress','if exists do' 'if not exists do','index','nextJump']的结构
如果 if exists do 或 in not exists do == None,表示不执行任何行为
index表示当有多个同样的按钮时，选择第几个按钮
按钮的排序按照从左到右，从上到下进行排列
index采用0-based系统
"""
"""
定义可以执行的内容
通过列表存储，第一个元素是执行的动作的类型，随后是具体的动作
鼠标示例：[click,left,2]左键双击两次
键盘示例: [host,ctrl,shift,p]使用组合键ctrl+shift+p
"""
"""
定义config格式
每个BaseBlock采用如下定义格式(采用[]表示实际要填写的东西，config中并不需要[])
采用示例：
label: [name]
address: [url]
do: [click,left,1]
else: [to otherLabel]
index: [all]
jump: [otherLabel]
解析时依靠冒号前的字母(标识符)进行解析
如果解析出错将直接报错终止程序
在解析时会进行标签替换成对应的索引
允许标识符后是空，则默认不执行任何步骤
使用begin  和  end 单词对 定义config的范围，begin 和 end 应该独占一行
对于不使用标识符开头的行将不会进行解析,所以可以直接写注释
如果config不以end结尾，会在log中进行记录，但不会直接报错
"""
"""
暂不支持热重载
如果更新配置文件，需要重启程序
"""
PICTURE_GET = 0.85
RNG_INT_LOW = 5
RNG_INT_HIGH = 10
RNG_FLOAT_LOW = 2
RNG_FLOAT_HIGH = 5


# 定义枚举类型
class Action(Enum):
    # 基本类型
    click = auto()
    keyHost = auto()
    notDo = auto()
    # 鼠标类型
    left = auto()
    right = auto()
    # 键盘类型
    # 键盘类型直接保存成str类型,便于直接调用pyautogui库

    # 特殊动作
    jump = auto()
    all = auto()


# 定义baseBlock
class BaseBlock:
    def __init__(self, address, exist, notExist, index, nextJump):
        self.address = address
        self.exist = exist
        self.notExist = notExist
        self.index = index
        self.nextJump = nextJump


# 定义配置文件解析器
class ConfigParser:
    def __init__(self, config, engine):
        self.configLineIndex = 0
        self.curLine = ''
        self.engine = engine
        self.close = False
        if isinstance(config, str):
            self.config = open(config, 'r', encoding='utf-8')
            self.close = True
            engine.logging('配置文件句柄打开,资源文件使用中')
        else:
            self.config = config
            self.engine.logging('配置文件由解析器外部开启,解析器不负责关闭资源')
        self.mapAction = {
            'click': Action.click,
            'keyHost': Action.keyHost,
            'notDo': Action.notDo,
            'left': Action.left,
            'right': Action.right,
            'jump': Action.jump,
            'all': Action.all
        }
        self.mapLabel = dict()

    def __del__(self):
        if self.close:
            self.config.close()
            self.engine.logging('由解析器打开的配置文件句柄已关闭，释放资源文件')

    def nextLine(self):
        self.curLine = self.config.readline()
        self.configLineIndex += 1

    def getTargetStr(self):
        return self.curLine.split(':')

    def processAddress(self):
        target = ['target']
        while target[0] != 'address' and target[0] != '':
            self.nextLine()
            target = self.getTargetStr()
        if target[0] == '':
            self.engine.logging(f'config在第{self.configLineIndex}行存在错误,不完整的块定义')
            exit(1)
        return target[1]

    def processDo(self):
        target = ['target']
        while target[0] != 'do' and target[0] != '':
            self.nextLine()
            target = self.getTargetStr()
        if target[0] == '':
            self.engine.logging(f'config在第{self.configLineIndex}行存在错误,不完整的块定义')
            exit(2)
        doList = target[1].split(',')
        arr = list()
        if doList[0] == 'click':
            if len(doList) != 3:
                self.engine.logging(f'config在第{self.configLineIndex}行出现非法参数,click行期待三个参数')
                exit(-1)
            arr = [self.mapAction[i] for i in doList[:-1]]
            try:
                arr.append(int(doList[-1]))
            except (ValueError, TypeError, OverflowError):
                self.engine.logging(f'config在第{self.configLineIndex}行出现非法参数,{doList[-2]}后期待int')
                exit(3)
        elif doList[0] == 'keyHost':
            arr = [self.mapAction[doList[0]]] + doList[1:]
        elif doList[0] == 'jump':
            if len(doList) != 2:
                self.engine.logging(f'config在第{self.configLineIndex}行出现非法参数,jump行期待两个参数')
                exit(4)
            arr = [self.mapAction['jump'], doList[-1]]
        elif doList[0] == 'notDo':
            if len(doList) != 1:
                self.engine.logging(f'warning:config在第{self.configLineIndex}行出现非法参数,notDo后不应有参数')
            arr = [self.mapAction[doList[0]]]
        else:
            self.engine.logging(f'未知指令: {doList[0]}')
            exit(5)
        return arr

    def processElse(self):
        target = ['target']
        while target[0] != 'else' and target[0] != '':
            self.nextLine()
            target = self.getTargetStr()
        if target[0] == '':
            self.engine.logging(f'config在第{self.configLineIndex}行存在错误,不完整的块定义')
            exit(6)
        doList = target[1].split(',')
        arr = list()
        if doList[0] == 'click':
            if len(doList) != 3:
                self.engine.logging(f'config在第{self.configLineIndex}行出现非法参数,click行期待三个参数')
                exit(7)
            arr = [self.mapAction[i] for i in doList[:-1]]
            try:
                arr.append(int(doList[-1]))
            except (ValueError, TypeError, OverflowError):
                self.engine.logging(f'config在第{self.configLineIndex}行出现非法参数,click后期待int')
                exit(8)
        elif doList[0] == 'keyHost':
            arr = [self.mapAction[doList[0]]] + doList[1:]
        elif doList[0] == 'jump':
            if len(doList) != 2:
                self.engine.logging(f'config在第{self.configLineIndex}行出现非法参数,jump行期待两个参数')
                exit(9)
            arr = [self.mapAction['jump'], doList[-1]]
        elif doList[0] == 'notDo':
            if len(doList) != 1:
                self.engine.logging(f'warning:config在第{self.configLineIndex}行出现非法参数,notDo后不应有参数')
            arr = [self.mapAction[doList[0]]]
        else:
            self.engine.logging(f'未知指令: {doList[0]}')
            exit(10)
        return arr

    def processIndex(self):
        target = ['target']
        while target[0] != 'index' and target[0] != '':
            self.nextLine()
            target = self.getTargetStr()
        if target[0] == '':
            self.engine.logging(f'config在第{self.configLineIndex}行存在错误,不完整的块定义')
            exit(11)
        if target[1] == 'all':
            return self.mapAction['all']
        else:
            try:
                return int(target[1])  # 如果是all,返回Action映射,否则返回数字
            except (ValueError, TypeError, OverflowError):
                self.engine.logging(f'config在第{self.configLineIndex}行存在错误,index后期待all或者数字')

    def processJump(self):
        target = ['target']
        while target[0] != 'jump' and target[0] != '':
            self.nextLine()
            target = self.getTargetStr()
        if target[0] == '':
            self.engine.logging(f'config在第{self.configLineIndex}行存在错误,不完整的块定义')
            exit(12)
        return target[1]  # 这里返回的是字符串类型的Label

    def processBaseBlock(self, res):
        target = ['target']
        while target[0] != 'label' and target[0] != '':
            self.nextLine()
            target = self.getTargetStr()
        if target[0] == '':
            self.engine.logging(f'config在第{self.configLineIndex}行存在错误,不完整的块定义')
            exit(13)
        if target[1] not in self.mapLabel:
            self.mapLabel[target[1]] = len(res)
        else:
            self.engine.logging('重复的Label标签,Label标签不可重复')
            exit(14)
        address = self.processAddress()
        do = self.processDo()
        notDo = self.processElse()
        index = self.processIndex()
        jump = self.processJump()
        res.append(BaseBlock(address, do, notDo, index, jump))

    def parser(self):
        res = list()
        while 'begin' != self.curLine.strip():
            self.nextLine()
        while 'end' != self.curLine.strip() and '' != self.curLine:
            self.processBaseBlock(res)
        if '' == self.curLine:
            self.engine.logging('warning:未使用end对config进行包裹,可能存在潜在错误')
        return self.mapLabel, res


# 定义执行引擎
class Engine:
    def __init__(self, log):
        self.workFlow = list()
        self.mapLabel = dict()
        if isinstance(log, IOBase):
            self.log = log
            self.logClose = False
        else:
            self.log = open(log, 'w', encoding='utf-8')
            self.logClose = True
        self.isRun = True
        self.logging(f'log由{"engine" if self.logClose else "外部"}开启')

    def __del__(self):
        if self.logClose:
            self.log.close()
            self.logging('engine关闭由自己占有的log句柄')

    @staticmethod
    def prtSc():
        return c.cvtColor(np.array(gui.screenshot()), c.COLOR_RGB2GRAY)

    # @staticmethod
    # def searchImg(picture, target):
    #     _, b, _, y = c.minMaxLoc(c.matchTemplate(picture, target, c.TM_CCOEFF_NORMED))
    #     return [b, y[0], y[1]]

    @staticmethod
    def mulSearchImg(picture, target):
        h, w = target.shape[:2]
        matchScore = c.matchTemplate(picture, target, c.TM_CCOEFF_NORMED)
        arr = np.where(matchScore >= PICTURE_GET)
        points = list(zip(*arr[::-1]))
        match = [(matchScore[y, x], x, y) for x, y in points]
        match = sorted(match, key=lambda x: (-x[0]))
        finalRes = list()
        while match:
            val, x, y = match.pop(0)
            finalRes.append((val, x, y))
            match = [m for m in match if (
                    (m[1] > x + w or m[1] + w < x) or
                    (m[2] > y + h or m[2] + h < y)
            )]
        return finalRes

    @staticmethod
    def formatTime() -> str:
        return dt.now().strftime('%Y-%m-%d-%H-%M-%S')

    def worker(self, curBlock: BaseBlock, x, y, rng, exist: bool):
        task = (curBlock.exist if exist else curBlock.notExist)
        if exist:
            if task[0] == Action.click:
                gui.moveTo(x + rng.integers(RNG_INT_LOW, RNG_INT_HIGH, endpoint=True),
                           y + rng.integers(RNG_INT_LOW, RNG_INT_HIGH, endpoint=True),
                           rng.uniform(RNG_FLOAT_LOW, RNG_FLOAT_HIGH),
                           gui.easeInOutQuad)
                button = 'left' if task[1] == Action.left else 'right'
                clicks = task[2]
                gui.click(button=button, clicks=clicks)
            elif task[0] == Action.keyHost:
                gui.hotkey(*(task[1:]))
            elif task[0] == Action.notDo:
                pass
            else:
                self.logging('未知指令')
                exit(15)
            return curBlock.nextJump
        else:
            if task[0] == Action.jump:
                return task[-1]
            elif task[0] == Action.notDo:
                pass

    def getBaseBlocks(self, config):
        parser = ConfigParser(config, self)
        return parser.parser()

    def logging(self, write):
        self.log.write(self.formatTime() + write + '\n')
        self.log.flush()

    def preImgRead(self):
        for i in self.workFlow:
            temp = c.imread(i.address)
            if temp is None:
                self.logging(f'{i.address}所指向的资源未找到')
                exit(16)
            i.address = c.cvtColor(temp, c.COLOR_BGR2GRAY)

    def stopRun(self):
        self.isRun = False

    def run(self, config):
        self.logging('启动成功')
        kb.add_hotkey('ctrl+shift+alt', self.stopRun)
        self.logging('全局紧急停止热键 ctrl+shift+alt 已成功注册')
        close = False
        if isinstance(config, str):
            close = True
            f = open(config, 'r', encoding='utf-8')
            self.logging('引擎打开config文件句柄')
        else:
            f = config
            self.logging('config资源由外部打开')
        self.mapLabel, self.workFlow = self.getBaseBlocks(f)
        if close:
            f.close()
            self.logging('引擎关闭config文件句柄,释放资源')
        self.preImgRead()
        blockLabel = self.workFlow[0].nextJump
        rng = np.random.default_rng()
        while blockLabel != 'over' and self.isRun:
            if blockLabel not in self.mapLabel:
                self.logging(f'未注册的Label {blockLabel} ')
                self.log.flush()
                exit(17)
            num = self.mapLabel[blockLabel]
            picture = self.prtSc()
            curBlock = self.workFlow[num]
            target = curBlock.address
            get = False
            while not get and self.isRun:
                imgs = self.mulSearchImg(picture, target)
                if len(imgs) != 0:
                    if curBlock.index == Action.all:
                        for (val, x, y) in imgs:
                            blockLabel = self.worker(curBlock, x, y, rng, True)
                    else:
                        for _, (val, x, y) in enumerate(imgs):
                            if _ == curBlock.index:
                                blockLabel = self.worker(curBlock, x, y, rng, True)
                                break
                    get = True
                else:  # 执行if not exists do
                    blockLabel = self.worker(curBlock, 0, 0, rng, False)
                time.sleep(rng.uniform(RNG_FLOAT_LOW, RNG_FLOAT_HIGH))
        write = '正常关闭' if self.isRun else '紧急关闭'
        self.logging(write)
