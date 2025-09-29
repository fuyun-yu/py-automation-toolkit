# 基于opencv&pyautogui的自动脚本

## 2025-09-29

- 注意到了几个会导致问题的地方，进行修复
- jump的字符和整形类型问题，jump的字符串标签应该保留，到engine的run再通过mapLabel临时转换，run里原来转换字符数字成int的逻辑修改一下，在engine里增加mapLabel变量，从parser接收
  调整mapAction的host映射变成keyHost
- over就不需要注册了，虽然本来就没注册
- 注册notDo进入字符指令映射表(mapAction)，给解析do和else的环节增加对notDo的支持
- 在exit(-1)改成递增的1 2 3 4 ，并且在退出前刷新一次写入日志

## 2025-09-28

- 我本来只是想写一个可以帮我自动清空体力的游戏小脚本，怎么一写就铺开了呢？


