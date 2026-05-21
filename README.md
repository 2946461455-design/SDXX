# SDXX

基于 OpenFOAM 11 的 `coinIBLMSolver` 三维定网格 IB-LM 原型工程。

## 目录
- `applications/solvers/coinIBLMSolver/`：自定义 C++ 求解器源码
- `01_openfoam_case_iblm/`：基础算例（32×32×80）
- `run_build_iblm_solver.sh`：编译脚本
- `run_solve_iblm.sh`：建网格 + 求解脚本

## 使用
```bash
source /opt/openfoam11/etc/bashrc
./run_build_iblm_solver.sh
./run_solve_iblm.sh
```
