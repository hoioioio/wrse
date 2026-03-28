# 📈 WRSE QUANT ENGINE (Walkforward-Regime-Shock-Execution)

[🚀 인터랙티브 백테스트 대시보드 (HTML Viewer)](https://hoioioio.github.io/WRSE-QUANT-ENGINE/)
[📄 대시보드 소스 (docs/index.html)](docs/index.html) (GitHub Pages `/docs`로 서비스되며, 레포 이름 변경 시 URL도 함께 갱신 필요)

*"문제 정의에서 실행비용을 반영한 퀀트 파이프라인까지."*  
이 프로젝트는 실전 시장 마찰(수수료, 슬리피지, 펀딩)과 **레짐 변화**를 견디도록 설계된 **암호화폐 선물 퀀트 연구 및 백테스트 엔진**입니다. 이 프로젝트는 인샘플 커브 피팅을 근본적으로 거부하며, 엄격한 **전진 분석 기반 Out-of-Sample(OOS)** 검증으로만 검증되었습니다.

---

## 📑 목차 (Table of Contents)
1. [프로젝트 개요](#1-project-overview)
2. [문제 정의](#2-problem-statement)
3. [가설](#3-hypothesis)
4. [데이터 & 연구 방법](#4-data--research-methodology)
5. [전략 설계](#5-strategy-design)
6. [리스크 관리](#6-risk-management)
7. [백테스트 결과 (WFO OOS)](#7-backtest-results-wfo-oos)
8. [엔진 아키텍처](#8-engine-architecture)
9. [실거래 결과](#9-live-trading-results)
10. [실패 & 개선](#10-failures--improvements)
11. [결론](#11-conclusion)

---

<a id="1-project-overview"></a>
## 1. 프로젝트 개요 🔭

- **핵심 목표**: 이론적 연구 가설을 반복 가능한 기관급 파이프라인으로 변환하는 엔진을 구축합니다: `데이터` → `가설` → `OOS 검증` → `실행비용 반영 시뮬레이션` → `리포팅`.
- **산출물**: GitHub Pages 대시보드(`docs/`), 재현 가능한 CLI 벤치마킹, 그리고 자동 생성 PNG/JSON 테어시트.

<a id="2-problem-statement"></a>
## 2. 문제 정의 🚨

*대부분의 개인 암호화폐 선물 전략은 구조적 현실을 무시하기 때문에 실거래 시장에서 실패합니다.* 이 엔진은 네 가지 핵심 문제를 해결하기 위해 구축되었습니다:

1. **레짐 변화**: 시장 레짐이 변하면(예: 강세 추세 vs 겹치는 횡보) 고정 파라미터가 붕괴하며, 이는 낙폭 확대로 이어집니다.
2. **변동성 클러스터링**: 변동성 확대는 본질적으로 레버리지 리스크를 증가시키고 유동성 꼬리를 노출시킵니다.
3. **실행 마찰**: 이론적 “종이 알파”는 maker/taker 수수료와 오더북 슬리피지로 인해 자주 소거됩니다.
4. **펀딩비 극단값**: 과밀한 파생 시장에서는 펀딩비가 급등할 때 구조적 기대수익 역풍이 발생합니다.

> **실행 명령(Execution Mandate)**: “나는 커브 피팅된 ‘시그널’을 설계하는 것이 아니라, 백테스트가 실현 가능한 손익을 그대로 반영하는 **OOS-검증, 실행비용 반영 시스템**을 엔지니어링한다.”

<a id="3-hypothesis"></a>
## 3. 가설 🧪

엔진 로직은 세 가지 핵심 정량 가설에 기반합니다:

- **가설 I (추세)**: 방향성 흐름을 동반한 변동성 확장은 수익 기회가 될 수 있으며, 다만 쇼크/과열 상태에서는 리스크를 공격적으로 잘라야 합니다.
- **가설 II (리버설/쇼크)**: 펀딩비 극단값과 유동성 공백은 확률적으로 평균회귀(counter-trade)를 유발하거나, 즉각적인 포트폴리오 디리스크(리스크 축소)를 강제해야 합니다.
- **가설 III (견고성)**: *전진 분석 기반 파라미터 락(Walk-Forward Parameter Locking)*을 통해 동적 비중(weight)을 사용하는 이중 모델 앙상블(추세 + 쇼크 방어)은 데이터 스누핑 바이어스와 레짐 변화에 구조적으로 방어력을 제공해야 합니다.

<a id="4-data--research-methodology"></a>
## 4. 데이터 & 연구 방법 📊

백테스트와 현실의 간극을 줄이기 위해, WRSE는 엄격한 정량 프로토콜을 따릅니다:

- **평가 프로토콜**: **전진 분석(WFO)**. 최적화기는 과거 `Train` 구간을 탐색하고 최적 앙상블 파라미터를 고정한 뒤, 보지 못한 미래 `Test(OOS)` 구간에서만 성과를 누적합니다.
- **바이어스 통제**: 룩어헤드 바이어스 0, 그리고 생존편향(survivorship bias)에 강한 로직.
- **미시구조 마찰**: Maker/Taker 제한을 하드코딩합니다. 지정가 미체결 폴백 또는 시장 충격에서 동적 슬리피지(bps)를 실제로 부과합니다.
- **재현성**: 데이터 스키마와 실행 경로는 [`docs/reproducibility.md`](docs/reproducibility.md)에 문서화되어 있습니다.

<a id="5-strategy-design"></a>
## 5. 전략 설계 ⚙️

WRSE는 단일 스크립트가 아니라, 결합된 시스템 엔진으로 동작합니다.

- 📡 **시그널 엔진(Signal Engine)**:
  - *추세 컴포넌트(Trend Component)*: 멀티 타임프레임 방향성 모멘텀을 평가합니다(`v2xa-style`).
  - *쇼크 컴포넌트(Shock Component)*: 9개 차원의 시장 특징을 정규화하여 **Ridge Regression Signed Classifier**를 학습하고, 예측 `shock_score`를 생성합니다.
- ⚖️ **포트폴리오 엔진(Portfolio Engine)**: 국소적인 Train 윈도우에서 그리드 서치를 수행하여 추세 모델과 쇼크 모델 간 자본 배분 weight를 최적화합니다.
- ⚡ **실행 엔진(Execution Engine)**: L2 오더북 마이크로 편차를 모델링합니다. 최적 지정가(`maker`)가 체결되지 않으면, 시스템은 지연된 시장가(`taker`) 체결을 강제하며 큰 슬리피지 페널티를 부과합니다.

<a id="6-risk-management"></a>
## 6. 리스크 관리 🛡️

*리스크는 시그널 생성과 독립적으로 동작하는, 1급 시민(first-class citizen)으로 취급됩니다.*

- **변동성 타게팅**: 현재 시장 상태에 따라 포트폴리오 슬롯 제한과 거래당 리스크 스케일링을 동적으로 조정합니다.
- **펀딩 쇼크 억제**: 펀딩비의 Z-score 정규화를 통해 과레버리지 극단 구간에서 포지션 진입을 하드 캡으로 제한합니다.
- **낙폭 제어**: 추세 및 평균회귀 컴포넌트 각각에 대해 분리된 하드-스탑 로직을 매핑합니다.
- **실행 스트레스 테스트**: `AB Hybrid`(현실적 지정가/시장가 혼합)와 극단적으로 보수적인 `Taker-only` 환경을 비교하여 성능을 평가합니다.

<a id="7-backtest-results-wfo-oos"></a>
## 7. 백테스트 결과 (WFO OOS, 2021→2024; Train 시작 2020) 📈

> 💡 *아래 모든 지표는 100% Out-of-Sample입니다. 엔진은 평가 대상 데이터를 “본 적이 없습니다”.*

### 7.1 전체 지표 (AB Hybrid vs 스트레스 테스트)

해석 노트:
- Sharpe는 4h 바 시뮬레이터가 생성한 “일간 에쿼티 커브”로부터 계산되며, 수수료/슬리피지/펀딩을 반영합니다(실행비용 반영의 현실성은 headline Sharpe를 낮추는 경향이 있습니다).

| 항목 | AB Hybrid (Execution-Aware) | Taker-only (Pessimistic Penalty) |
| :--- | :---: | :---: |
| **누적 수익률** | **+109.45%** | +95.88% |
| **연 환산(CAGR)** | **20.35%** | 18.34% |
| **최대 낙폭(MDD)** | **-13.08%** | -14.38% |
| **샤프 지수(Sharpe)** | **0.65** | 0.59 |
| **운용 일수** | 1,457 일 | 1,457 일 |

![Strategy Equity vs Bitcoin Benchmark](docs/assets_public/equity_vs_btc_log.png)

### 7.2 연도별 OOS Split (Train → Test)

| 테스트 연도 | OOS 수익률(AB) | MDD(AB) | Sharpe (AB/Taker) | 앙상블 Weight(고정) |
| :---: | :---: | :---: | :---: | :---: |
| **2021** (Split 1) | +8.67% | -13.08% | 0.55 / 0.40 | 0.5 (*Train: 2020*) |
| **2022** (Split 2) | -0.26% | -11.76% | 0.03 / -0.19 | 0.3 (*Train: 2020-2021*) |
| **2023** (Split 3) | +79.92% | -11.17% | 1.11 / 1.08 | 0.7 (*Train: 2020-2022*) |
| **2024** (Split 4) | +7.41% | -2.24% | 1.34 / 1.02 | 0.3 (*Train: 2020-2023*) |

> 🔍 **레짐 분석**: 2022 디레버리징 사이클에서는 펀딩/변동성 혼돈 하에서 진입이 공격적으로 억제되어 성장세가 둔화되었지만 낙폭은 통제되었습니다. 2023의 방향성 추세 구간에서는 추세 컴포넌트가 지배적이었고 상승분의 대부분을 견인했습니다.

![WFO OOS Sharpe](docs/assets_public/wfo_oos_sharpe.png)

<a id="8-engine-architecture"></a>
## 8. 엔진 아키텍처 🧩
*(아래 “주요 파일”을 사용하면 소스 코드로 바로 이동할 수 있습니다)*

```text
📁 C:\wrse\
 ├── 📁 alpha/
 │    └── shock.py         # Ridge 기반 점프 리스크 & 리버설 분류기
 ├── 📁 backtest/
 │    ├── simulators.py    # 고해상도 바 단위 시뮬레이터 (TCA)
 │    ├── walkforward.py   # 롤링 WFO 최적화기 & 비중 할당기
 │    └── metrics.py       # PnL 평가기 (Sharpe, MDD, 복리)
 ├── 📁 data/
 │    └── loader.py        # 캐시 기반 과거 유니버스 파서
 ├── 📁 execution/
 │    └── models.py        # L2 maker→taker 실행 슬리피지 로직
 ├── 📁 utils/
 │    └── config.py        # TOML 설정 로더
 ├── 📁 config/
 │    └── strategy_params.example.toml # 환경 제약
 ├── 📁 docs/                      # 인터랙티브 HTML 대시보드
 ├── cli.py                     # 커맨드라인 실행 인터페이스
 ├── report.py                  # 그래프 테어시트 & JSON 생성기
 └── requirements.txt
```

### 주요 파일 (클릭 가능)

- 시그널: [alpha/shock.py](alpha/shock.py)
- WFO & 앙상블: [backtest/walkforward.py](backtest/walkforward.py)
- 시뮬레이터(수수료/슬리피지/펀딩): [backtest/simulators.py](backtest/simulators.py)
- 지표/연도별 테이블: [backtest/metrics.py](backtest/metrics.py)
- 실행 모델(maker→taker): [execution/models.py](execution/models.py)
- 설정 로더: [utils/config.py](utils/config.py)
- 예시 설정: [config/strategy_params.example.toml](config/strategy_params.example.toml)
- 리포트 익스포터(PNG/JSON): [report.py](report.py)

<a id="9-live-trading-results"></a>
## 9. 실거래 결과 🌐

- 실거래 결과는 이 레포지토리에 포함되어 있지 않습니다.
- 코드베이스는 `시그널`, `리스크`, `실행` 레이어를 분리하여, 연구 로직을 변경하지 않고도 동일한 메커니즘을 WebSocket 기반 실거래 환경에 통합할 수 있습니다.

<a id="10-failures--improvements"></a>
## 10. 실패 & 개선 🛠️

건강한 퀀트 엔진은 결코 완성되지 않습니다. 현재 향후 업그레이드가 필요하다고 식별된 핵심 영역은 다음과 같습니다:
1. **레짐 과민성**: 2022년에 극단적 쇼크 억제가 너무 많은 중립 구간 트레이드를 질식시켰습니다. Gaussian Mixture Model(GMM) 또는 HMM을 추가해 마이크로 레짐을 식별하면, 거시적 공포와 국지적 기회를 분리할 수 있습니다.
2. **경로 의존성 검증**: 트레이드 시퀀스에 대한 몬테카를로(MC) 리샘플링을 포함하면 추정된 샤프 지수 및 프로핏 팩터 주변의 통계적 신뢰구간을 더 타이트하게 만들 수 있습니다.
3. **실행 지연 개선**: Python은 연구에는 최적이지만 L2 파싱 지연에는 최적이 아닙니다. `execution/models.py`에 해당하는 메커닉을 Rust/C++ 모듈로 옮기면, 현재 통계적으로 모델링되는 큐 포지션 지연을 최소화할 수 있습니다.

<a id="11-conclusion"></a>
## 11. 결론 🏁

WRSE Quant Engine은 암호화폐 파생 시스템에 대해 성숙한 접근을 보여줍니다: 단순한 전략 커브 피팅보다 **문제 중심 설계**, **데이터 스누핑 제거**, 그리고 **실행비용 반영 현실성**을 우선합니다.

---

### 🖥️ 빠른 재현 (Quick Reproduce)

```bash
pip install -r requirements.txt
python cli.py wfo --config config/strategy_params.example.toml --write_csv ./outputs
python report.py --config config/strategy_params.example.toml --public
python verify_portfolio.py
```
