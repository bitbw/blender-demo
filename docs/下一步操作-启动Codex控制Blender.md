# 下一步操作：启动 Codex 控制 Blender

安装和配置已经完成。你只需要按以下顺序执行。

## 1. 保存并重启 Blender

1. 在当前 Blender 中先保存你的工作。
2. 完全退出 Blender。
3. 重新打开 Blender 5.1。

原因：MCP 扩展是在 Blender 已打开时安装的，重启后才会加载并启动本机桥接服务。

## 2. 确认 Blender MCP 已启动

1. 在 Blender 菜单中打开 `Edit > Preferences > Extensions`。
2. 搜索 `MCP`。
3. 确认名为 **MCP**、维护者为 **Blender Lab** 的扩展已启用。
4. 打开扩展设置，确认：
   - Host：`localhost`
   - Port：`9876`
   - Auto Start：开启
   - 状态：`Server is running`

如果没有自动启动，直接在扩展设置中点击启动服务。

## 3. 重启 Codex

完全关闭并重新打开 Codex。这样它会加载已经注册好的本地 `blender` MCP 服务。

在 Codex 输入 `/mcp`，应能看到 `blender` 已连接或已启用。

## 4. 先做只读连接测试

新开一个 Codex 对话，发送：

```text
使用 Blender MCP：只读取当前场景，列出所有对象名称、类型与数量；不要修改、删除或保存任何内容。
```

预期结果：Codex 会调用 Blender MCP，并返回当前场景对象列表。

如果失败，检查这三项：

1. Blender 是否仍在运行。
2. MCP 扩展状态是否为 `Server is running`。
3. Host 和 Port 是否仍是 `localhost:9876`。

## 5. 准备参考图

在项目根目录创建 `references` 文件夹，将图片放进去。推荐命名：

```text
references/
  object-front.png
  object-side.png
  object-back.png
  object-45deg.png
```

单张图只能推测背面、厚度和隐藏结构；至少提供正面、侧面、背面和 45 度图，效果会明显更稳定。

## 6. 第一次按图建模

先打开一个新的 Blender 文件或你的 `.blend` 副本，再把下面提示词发给 Codex：

```text
使用 Blender MCP，根据 references/object-front.png、references/object-side.png、references/object-back.png 和 references/object-45deg.png 建模。

要求：
- 先分析参考图并列出不确定的尺寸或不可见结构；
- 先只建立灰模、比例和主体轮廓，不做材质细节；
- 所有新对象放到 AI_Model 集合；
- 不删除、修改或保存任何既有对象；
- 渲染正面、侧面和 45 度预览图；
- 根据预览与参考图的差异自行修正，最多 3 轮；
- 完成后停下来，报告模型内容和仍需我确认的部分。
```

确认灰模正确后，再发送：

```text
保留当前模型结构，添加必要的倒角、平滑法线、UV 和基础材质。渲染预览供我确认；未确认前不要导出。
```

## 7. 确认后导出

模型确认无误后，再发送：

```text
保存当前文件为 output/object.blend，并导出 output/object.glb。导出完成后报告文件路径、对象数量和三角面数量。
```

## 注意事项

- 每次让 Codex 修改前先保存 `.blend` 副本。
- Blender MCP 能执行模型生成的 Python，不要把端口 `9876` 暴露给局域网或公网。
- 一次只要求一个阶段：灰模、细化、材质、导出。不要把全部要求塞进第一次指令。
