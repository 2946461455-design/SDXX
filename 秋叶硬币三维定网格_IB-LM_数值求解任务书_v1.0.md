# 秋叶硬币三维定网格 IB-LM 数值求解任务书

**基于 OpenFOAM C++ 自定义求解器 `coinIBLMSolver`**  
**版本：v1.0**｜**用途：竞赛理论/数值模拟任务规划与验收**

| 项目 | 内容 |
|---|---|
| 计算对象 | 硬币/薄圆盘在水中下落的三维流固耦合运动 |
| 核心方法 | 固定 Eulerian 网格 + Lagrangian marker + Peskin delta + Lagrange multiplier |
| 实现平台 | OpenFOAM 11，C++ 自定义 solver |
| 输出目标 | 硬币轨迹、姿态、受力/力矩、U、p、U_tilde、ibAcceleration |
| 当前状态 | 求解器原型已跑通，后续需进行网格/时间步/扰动验证 |

---

## 目录

- 一、任务背景与目标
- 二、理论依据与算法链条
- 三、计算对象、参数与扰动设置
- 四、OpenFOAM C++ 求解器实现要求
- 五、网格与时间步推进计划
- 六、轨迹与流场判断标准
- 七、阶段任务、验收标准与风险点
- 八、PyCharm/ParaView 后处理要求
- 九、PPT 可用表述与参考文献

---

## 一、任务背景与目标

“秋叶硬币”问题关注硬币在液体中下落时，由流体力、流体力矩、刚体惯性和姿态演化共同作用产生的复杂运动模式，包括稳定下落、flutter、tumbling 以及不同模态之间的转变。  
传统 OpenFOAM 动网格 / sixDoF 方法需要贴体网格或动网格更新，计算复杂且容易出现网格畸变。为避免动网格问题，本任务采用固定 Eulerian 背景网格，将硬币作为穿过固定网格的刚体，由 Lagrangian marker 表示，并通过拉格朗日乘子强制刚体区域满足无滑移约束。

总体目标：建立一个可运行、可验证、可逐步加密的三维 OpenFOAM C++ 自定义求解器 `coinIBLMSolver`，用于模拟硬币在水中下落的三维流固耦合运动。

### 1.1 必须满足的核心要求

- 使用固定 Cartesian 背景网格，不使用 `dynamicMesh`、`moveMesh` 或 `sixDoFRigidBodyMotion`。
- 求解器必须是 OpenFOAM C++ 自定义 solver，而不是 Python 后处理脚本。
- 采用浸没边界-拉格朗日乘子法处理硬币与流体耦合。
- 能够输出硬币三维质心轨迹、姿态角、角速度、水动力和水动力矩。
- 能够输出流场速度 `U`、压力 `p`、临时速度 `U_tilde` 和 LM 扩散后的 `ibAcceleration`。
- 能够加入初始姿态扰动、初始流体扰动以及几何微扰：花纹高度、边缘锯齿和边缘倒角。
- 能够逐步加密网格，观察轨迹是否由近似直线下落发展出横向漂移和姿态演化。

### 1.2 当前定位

当前程序应定位为“可运行的三维定网格 IB-LM 数值原型”。它可以用于验证流固耦合链条、扰动触发趋势和输出流程，但不能直接把第一次 2 秒计算结果当成最终物理结论。定量可信度需要通过网格收敛、时间步收敛、扰动敏感性和实验轨迹对比进一步确认。

---

## 二、理论依据与算法链条

### 2.1 不可压缩流体控制方程

流体在固定 Eulerian 网格上求解不可压缩 Navier-Stokes 方程：

- ρ(∂u/∂t + u·∇u) = −∇p + μ∇²u + f
- ∇·u = 0

其中 u 为流体速度，p 为压力，ρ 为密度，μ 为动力黏度，f 为由拉格朗日乘子扩散到 Eulerian 网格上的等效体力项。

### 2.2 Eulerian-Lagrangian 耦合

硬币由一组 Lagrangian marker 表示，流体速度和压力定义在固定 Eulerian 背景网格上。速度插值与力扩散分别写作：

- U(X) = J[X] u
- f = S[X] F

其中 J 是速度插值算子，S 是力扩散算子，F 是 marker 上的拉格朗日乘子。文献说明，IB 方法不需要贴体网格，结构点允许自由切过背景 Cartesian 网格，并通过 regularized delta functions 进行 Lagrangian-Eulerian 变量传递。

### 2.3 Direct-forcing IB-LM 时间推进

本任务采用 Nangia 等（2017）文献中的 direct-forcing IB-LM 形式，对应 Eq.(6)–Eq.(9) 的算法链条。

第一步，联立求临时速度 U_tilde 与压力 p：

ρ[(ũⁿ⁺¹ − uⁿ)/Δt + (u·∇ₕu)ⁿ⁺¹/²] = −∇ₕpⁿ⁺¹/² + (μ/2)∇ₕ²(ũⁿ⁺¹ + uⁿ)  
∇ₕ·ũⁿ⁺¹ = 0

第二步，将临时速度插值到硬币 marker，计算拉格朗日乘子：

Fⁿ⁺¹/² = (ρ/Δt) [ U_bⁿ⁺¹ − Jₕ[Xⁿ⁺¹/²] ũⁿ⁺¹ ]

第三步，将拉格朗日乘子扩散回 Eulerian 网格，修正流体速度：

ρ[(uⁿ⁺¹ − ũⁿ⁺¹)/Δt] = Sₕ[Xⁿ⁺¹/²] Fⁿ⁺¹/²

实现时不应额外加入人为松弛系数 alpha；若出于数值稳定性临时加入，必须作为非严格版本明确标注，不能混入文献对应的严格算法链条。

### 2.4 水动力与力矩计算

水动力和水动力矩不通过硬币表面压力/剪切应力直接积分，而通过 LM 和刚体动量平衡计算。文献给出：

- d/dt ∫_{V_b(t)} ρU dV = F_hydro + ∫_{V_b(t)} F dV
- d/dt ∫_{V_b(t)} ρR×U dV = M_hydro + ∫_{V_b(t)} R×F dV

这使得净水动力和力矩可以作为求解过程的一部分在 Lagrangian 框架中得到，避免直接在扩散界面上求压力和速度梯度导致的噪声问题。

---

## 三、计算对象、参数与扰动设置

### 3.1 硬币与流体参数

| 类别 | 参数 | 默认值 | 说明 |
|---|---|---|---|
| 硬币 | 直径 d | 0.022 m | 22 mm 圆盘硬币 |
| 硬币 | 厚度 t | 0.001 m | 1 mm 薄圆盘 |
| 流体 | 密度 ρ | 约 1000 kg/m³ | 水 |
| 流体 | 运动黏度 ν | 约 1e-6 m²/s | 水的量级 |
| 计算域 | 尺寸 | 0.20 m × 0.20 m × 0.50 m | 简化实验水箱局部区域 |

### 3.2 当前微小扰动设置

```text
omega0                  (0 0 0)
initialPosePerturbDeg   (0.20 -0.15 0.10)

patternHeight           2e-5     // 0.02 mm
edgeSerrationAmplitude  1e-5     // 0.01 mm
edgeChamfer             5e-5     // 0.05 mm
initialFluidPerturbation 1e-4    // m/s
```

这些扰动量级非常小。以当前 32×32×80 网格为例，网格尺度约为 6.25 mm，而花纹高度仅 0.02 mm，边缘锯齿仅 0.01 mm，因此真实几何扰动远低于当前网格分辨率。当前扰动主要作为打破对称性的触发项，而不是已经被流场完全解析的真实微结构。

### 3.3 扰动敏感性测试组

| 组别 | patternHeight | edgeSerrationAmplitude | edgeChamfer | 用途 |
|---|---:|---:|---:|---|
| A：真实微扰 | 2e-5 | 1e-5 | 5e-5 | 接近真实花纹/边缘微扰 |
| B：中等放大 | 5e-4 | 3e-4 | 5e-4 | 检查几何扰动是否开始影响姿态 |
| C：强扰动验证 | 0.002 | 0.001 | 0.001 | 验证几何非对称→流体力矩→姿态演化链条 |

C 组不作为真实硬币参数，仅用于验证程序中几何扰动是否确实可以影响流体力矩、姿态和轨迹。

---

## 四、OpenFOAM C++ 求解器实现要求

### 4.1 求解器与目录结构

| 项目 | 要求 |
|---|---|
| 求解器名称 | `coinIBLMSolver` |
| 源文件 | `applications/solvers/coinIBLMSolver/coinIBLMSolver.C` |
| 算例目录 | `01_openfoam_case_iblm/` |
| 参数文件 | `01_openfoam_case_iblm/constant/coinIBLMProperties` |
| 运行脚本 | `run_build_iblm_solver.sh`；`run_solve_iblm.sh` |

### 4.2 禁止与必须使用的机制

| 不得使用 | 必须使用 |
|---|---|
| `pimpleFoam` 作为最终求解器 | OpenFOAM C++ 自定义 solver `coinIBLMSolver` |
| `dynamicMesh` / `moveMesh` | 固定 Cartesian 背景网格 |
| `sixDoFRigidBodyMotion` | 自定义 Lagrangian marker + 6DoF 姿态更新 |
| 贴体表面应力直接积分作为主力计算 | LM 力/力矩平衡计算水动力和力矩 |

### 4.3 必须输出的场与文件

| 输出 | 位置 | 含义 |
|---|---|---|
| U | OpenFOAM 时间步目录 | LM 修正后的最终速度场 |
| p | OpenFOAM 时间步目录 | 压力场 |
| U_tilde | OpenFOAM 时间步目录 | Eq.(6)-(7) 求得的临时速度 |
| ibAcceleration | OpenFOAM 时间步目录 | LM 扩散后的等效加速度/体力项 |
| trajectory_lm.csv | `postProcessing/coinIBLM/` | 质心、速度、姿态角、角速度 |
| forces_lm.csv | `postProcessing/coinIBLM/` | Fx, Fy, Fz, Tx, Ty, Tz |

---

## 五、网格与时间步推进计划

当前默认网格为 32×32×80，总网格数 81920，计算域为 0.20 m × 0.20 m × 0.50 m，对应 dx=dy=dz=6.25 mm。该网格只能用于验证求解器稳定性和输出流程，不能作为最终定量结果。

| 阶段 | 网格 | 网格尺度 | 计算量相对 32×32×80 | 目标 |
|---|---|---|---|---|
| 粗网格验证 | 32×32×80 | 6.25 mm | 1× | 确认 solver 能稳定跑到 0.2、0.5、1.0、2.0 s |
| 第一加密 | 48×48×120 | 4.17 mm | 3.375× | 观察横漂、姿态角和力矩是否变化 |
| 推荐中等网格 | 64×64×160 | 3.125 mm | 8× | 形成第一版较可信的三维 IB-LM 结果 |
| 进一步加密 | 96×96×240 | 2.08 mm | 27× | 初步网格收敛判断 |
| 高成本测试 | 128×128×320 | 1.56 mm | 64× | 计算资源允许时再做 |

### 5.1 时间步计划

| 项目 | 当前建议 | 说明 |
|---|---|---|
| deltaT | 1e-4 s | 当前 2 s 计算约 20000 步 |
| writeInterval | 20 | 每 0.002 s 写出一次 |
| 时间步收敛 | 1e-4 → 5e-5 → 2.5e-5 | 比较轨迹和姿态是否保持趋势一致 |

### 5.2 网格修改命令

从工程根目录运行以下命令可将 `blockMeshDict` 修改为 48×48×120：

```bash
python3 - <<'PY'
from pathlib import Path
import re
p = Path('01_openfoam_case_iblm/system/blockMeshDict')
s = p.read_text()
s = re.sub(r'hex\s*\(([^)]*)\)\s*\(\s*\d+\s+\d+\s+\d+\s*\)', r'hex (\1) (48 48 120)', s)
p.write_text(s)
print('已把网格改成 48 × 48 × 120')
PY
```

修改网格后需要清理旧网格和旧时间步，然后重新运行：

```bash
rm -rf 01_openfoam_case_iblm/constant/polyMesh
rm -rf 01_openfoam_case_iblm/0.* 01_openfoam_case_iblm/[1-9]* 01_openfoam_case_iblm/postProcessing/coinIBLM
./run_solve_iblm.sh
```

---

## 六、轨迹与流场判断标准

### 6.1 轨迹判断

| 图像/数据 | 判断内容 | 合理表现 | 需要警惕 |
|---|---|---|---|
| x-z 侧视轨迹 | 横向漂移随下落深度变化 | 可能出现逐渐偏转或左右摆动 | 完全直线且姿态不变 |
| y-z 侧视轨迹 | 另一个横向方向的漂移 | 与扰动方向有关 | 横漂为 0 且所有扰动不起作用 |
| x-y 俯视轨迹 | 最终落点和水平漂移 | 出现非零落点半径 | 落点无论扰动如何都固定不变 |
| z-t 下落深度 | 总体是否下落 | z_down 总体增加 | 硬币上飞、穿出边界或速度爆炸 |

### 6.2 姿态与力矩判断

| 量 | 判断问题 | 合理表现 |
|---|---|---|
| roll/pitch/yaw | 姿态是否被流体力矩激发 | 弱旋转、周期振荡或持续翻滚，取决于初始角和扰动 |
| omega_x/y/z | 角速度是否有物理演化 | 可出现增大、减小、换向或周期性变化 |
| Fx/Fy/Fz | 水动力是否平滑 | 不应突然出现非物理极大值 |
| Tx/Ty/Tz | 力矩是否对应姿态变化 | 力矩变化应与姿态扰动方向和运动模态有关 |
| ibAcceleration | LM 是否作用于硬币附近 | 应在硬币附近局部集中，不应完全为零 |
| U_tilde 与 U | LM 修正是否生效 | 两者在硬币附近应有差异 |

---

## 七、阶段任务、验收标准与风险点

### 7.1 当前阶段任务

1. 完成 2 秒粗网格运行：32×32×80，endTime=2.0 s，检查是否发散。
2. 绘制 x-z、y-z、x-y、z-t、roll/pitch/yaw、omega_x/y/z、forces/torques 曲线。
3. 运行 48×48×120 网格，并与 32×32×80 结果对比。
4. 运行 64×64×160 网格，作为第一版较可信结果。
5. 在 64 网格下进行 A/B/C 三组扰动敏感性测试。

### 7.2 求解器验收标准

- `coinIBLMSolver` 能成功编译并运行到指定 endTime。
- 运行过程中无 floating point exception 和严重 Courant 数发散。
- 输出 `U`、`p`、`U_tilde`、`ibAcceleration` 以及 `trajectory_lm.csv`、`forces_lm.csv`。
- `trajectory_lm.csv` 中 z 方向总体下落，力和力矩无非物理爆炸。
- 扰动增大时，姿态、横向漂移或力矩应出现可观响应。

### 7.3 需要警惕的结果

- 硬币完全不下落，或 z 方向突然反向飞出水面。
- 所有扰动增大后轨迹仍严格直线，roll/pitch/yaw 始终不变。
- `ibAcceleration` 在硬币附近完全为零。
- `U_tilde` 与 `U` 完全没有差异，说明 LM 修正可能没有生效。
- 网格一加密，模态完全改变且没有收敛趋势。

---

## 八、PyCharm/ParaView 后处理要求

### 8.1 PyCharm 轨迹绘图

PyCharm 读取 `postProcessing/coinIBLM/trajectory_lm.csv` 后，需要至少输出以下图：x-z 侧视、y-z 侧视、x-y 俯视、z-t 下落深度、roll/pitch/yaw 姿态角、omega_x/y/z 角速度。

```python
import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv(r'D:\coin_iblm_results\trajectory_lm.csv')
t = df['time'] if 'time' in df.columns else df['t']
x = df['x'] * 100
y = df['y'] * 100
z_down = -(df['z'] - df['z'].iloc[0]) * 100

plt.figure(figsize=(6, 8))
plt.plot(x - x.iloc[0], z_down)
plt.xlabel('x drift / cm')
plt.ylabel('falling depth / cm')
plt.title('x-z side trajectory')
plt.grid(True)
plt.show()
```

### 8.2 ParaView 流场查看

在算例目录中运行 paraFoam，重点查看 `U`、`p`、`U_tilde`、`ibAcceleration`。推荐先做中间平面 Slice，观察硬币附近的压力分布、速度扰动和 LM 等效体力分布。

```bash
cd 01_openfoam_case_iblm
paraFoam
```

---

## 九、PPT 可用表述与参考文献

### 9.1 PPT 可用表述

本研究采用固定欧拉网格下的浸没边界-拉格朗日乘子方法模拟硬币在水中的三维下落过程。流体速度和压力在固定背景网格上求解，硬币由拉格朗日标记点表示，并通过 Peskin delta 函数实现 Eulerian-Lagrangian 变量传递。首先求解临时速度场与压力场，再通过拉格朗日乘子强制硬币区域满足刚体无滑移约束，并由乘子反算硬币所受水动力与水动力矩。该方法避免了动网格更新和硬币表面应力直接积分，可用于研究初始姿态、流体扰动和几何微扰对硬币 flutter/tumbling 模态形成的影响。

当前计算为三维定网格 IB-LM 数值原型，主要用于验证流固耦合机制和扰动触发趋势。其定量结果仍需通过网格收敛、时间步收敛和实验轨迹对比进一步验证。

### 9.2 参考文献

- Nangia, N., Johansen, H., Patankar, N. A., & Bhalla, A. P. S. (2017). *A moving control volume approach to computing hydrodynamic forces and torques on immersed bodies*. Journal of Computational Physics.
- Peskin, C. S. Immersed boundary method 相关工作：用于 Eulerian-Lagrangian 耦合和 regularized delta 传递。
- Bhalla et al. direct-forcing immersed boundary / Lagrange multiplier 相关实现：用于刚体约束与水动力计算。

---

## 附录 A：当前建议的运行顺序

```bash
# 1. 确认 OpenFOAM 环境
foamVersion

# 2. 编译 solver
./run_build_iblm_solver.sh

# 3. 修改 endTime 为 2 秒
sed -i 's/^endTime[[:space:]]\+[0-9.eE+-]\+;/endTime         2.0;/' 01_openfoam_case_iblm/system/controlDict

# 4. 清理旧结果并运行
rm -rf 01_openfoam_case_iblm/0.* 01_openfoam_case_iblm/[1-9]* 01_openfoam_case_iblm/postProcessing/coinIBLM
./run_solve_iblm.sh

# 5. 查看结果
tail 01_openfoam_case_iblm/postProcessing/coinIBLM/trajectory_lm.csv
tail 01_openfoam_case_iblm/postProcessing/coinIBLM/forces_lm.csv
```
