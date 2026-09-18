# Blender 理想 L9 建模示例

基于理想 L9 外观参考图、蓝图与 `2022.max` 原始资产的 Blender 建模实验项目。

## 内容

- `build_l9.py`：第 1 版图片参考建模脚本。
- `build_l9_v02.py` / `refine_l9_v02.py`：第 2 版照片匹配模型与修正。
- `build_l9_v03.py`：按蓝图尺寸约束的第 3 版模型。
- `prepare_l9_2022_assembly.py`：把 `2022.max` 转换源整理为米制 Blender 装配的脚本。
- `素材/理想L9-外观/`：L9 外观参考图片。
- `docs/`：Blender MCP 配置与操作说明。

## 黑武士成品（本地输出）

生成的 Blender、GLB、原始 MAX 和贴图不提交到 Git，统一保存在本地：

`output/2022max_black_knight/`

主要文件：

- `L9_2022_black_knight_v03.blend`：Blender 黑武士材质版。
- `L9_2022_black_knight_v03.glb`：Three.js 可加载的高精度 GLB。
- `l9-viewer.html`：本地 Three.js 查看器。
- `start-l9-viewer.bat`：启动本地查看器。

## 查看 Three.js 模型

在项目根目录启动本地服务器：

```powershell
py -m http.server 8080
```

然后打开：

```text
http://localhost:8080/output/2022max_black_knight/l9-viewer.html
```

也可以双击 `output/2022max_black_knight/start-l9-viewer.bat`。

## 注意

- `output/`、`.tools/`、`blueprint/` 和 Playwright 临时文件已被 Git 忽略。
- 黑武士 GLB 约 72 MB，来自高精度原始模型；网页实时查看会占用较多显卡资源。
- 如需网页端更流畅，应另行导出减面/压缩版 GLB。
