# 基于opencv&pyautogui的自动脚本

## 说明

- 可以通过 config 来设置自动化工作，当前支持鼠标点击和键盘热键(2025-09-29)
- 以下是配置文件说明格式说明
- 注意：配置文件最上面的第一个label必须是第一张图片
- pip install opencv-python pyautogui keyboard numpy pillow

```
定义BaseBlock
BaseBlock列表将用于引导整个程序的执行  
['imageAddress','if exists do' 'if not exists do','index','nextJump']
当 nextJump ==  'over' 程序执行完毕
label: [name]
address: [url]
do: [click,left,1]
else: [jump,otherLabel]
index: [all]
jump: [otherLabel]
解析时依靠冒号前的字母(标识符)进行解析
如果解析出错将直接报错终止程序
在解析时会进行标签替换成对应的索引
允许标识符后是notDo，则默认不执行任何步骤
使用begin  和  end 单词对 定义config的范围，begin 和 end 应该独占一行
对于不使用标识符开头的行将不会进行解析,所以可以直接写注释
如果config不以end结尾，会在log中进行记录，但不会直接报错
定义当成功执行后必然会跳转,失败则只执行if not exists do 
鼠标示例：[click,left,2]左键双击两次
键盘示例: [keyHot,ctrl,shift,p]使用组合键ctrl+shift+p
```

- 配置文件示例：

```
begin
这是一个注释测试
label:brow
address:C:\Users\temp\Pictures\Screenshots\xxx1.png
do:click,left,1
else:notDo
index:0
这些话应该会被忽视
jump:plus
label:plus
address:C:\Users\temp\Pictures\Screenshots\xxx2.png
do:click,left,1
else:notDo
index:0
jump:min
label:min
address:C:\Users\temp\Pictures\Screenshots\xxx3.png
do:keyHot,f12
else:notDo
index:0
jump:over
end
```

## 2025-09-30

- 在`2025-09-29`时已经写完第一个可以使用的版本，累计用时三天
- 不过算起来累计写代码时间，应该只有八九个小时

- 在今天决定上传GitHub

## 2025-09-29

- 注意到了几个会导致问题的地方，进行修复
- jump的字符和整形类型问题，jump的字符串标签应该保留，到engine的run再通过mapLabel临时转换，run里原来转换字符数字成int的逻辑修改一下，在engine里增加mapLabel变量，从parser接收
  调整mapAction的host映射变成keyHost
- over就不需要注册了，虽然本来就没注册
- 注册notDo进入字符指令映射表(mapAction)，给解析do和else的环节增加对notDo的支持
- 在exit(-1)改成递增的1 2 3 4 ，并且在退出前刷新一次写入日志

## 2025-09-28

- 我本来只是想写一个可以帮我自动清空体力的游戏小脚本，怎么一写就铺开了呢？


