# WRSE Quant Engine

전진 분석 기반 OOS 평가와 실행 마찰(수수료/슬리피지/펀딩/메이커→테이커 폴백)을 반영하는 크립토 선물 연구/백테스트 엔진입니다.

- 대시보드: [인터랙티브 백테스트 대시보드](https://hoioioio.github.io/WRSE-QUANT-ENGINE/)
- 제출용 풀 리포트(1~13 구조): [docs/portfolio_ko.md](docs/portfolio_ko.md)
- 데이터 스키마/재현: [docs/reproducibility.md](docs/reproducibility.md)
- English README: [README.md](README.md)

참고:
- 원본 시장 데이터는 포함하지 않습니다(용량/라이선스). OHLCV(필수) 및 funding/L2 요약(선택)을 cache로 읽습니다.
- Python 3.11+ 필요 (`tomllib` 사용).

## 핵심 특징

- 전진 분석(Walk-forward) 기반 OOS-only 누적 평가(연도 split)
- 실행 마찰 반영(메이커/테이커 수수료, 슬리피지, 펀딩, 메이커→테이커 폴백)
- 재현 가능한 공개 산출물(docs/assets_public/의 JSON/그림, 대시보드 입력)
- TOML 설정 기반 연구/실행 워크플로우

## 연구 가설 및 전략 논리 (Research & Hypotheses)

단순 백테스트를 넘어, 다음과 같은 시장 미시구조(Microstructure) 관찰과 가설을 시스템에 반영했습니다.

- **관찰 1 (펀딩비 왜곡)**: 펀딩비가 극단적 양수(+)로 치솟는 구간은 롱 포지션의 과도한 레버리지가 집중된 상태를 의미합니다.
- **가설 1**: 이 상태에서 모멘텀이 둔화되면 롱 스퀴즈(Long squeeze)로 인한 급락 확률이 높아지므로, 추세 추종 진입을 억제해야 기댓값이 유지됩니다.
- **관찰 2 (변동성 군집)**: 청산 연쇄는 단기 변동성을 폭증시키며, 급변장(Shock)을 형성합니다.
- **가설 2**: 변동성 확장 초기의 추세는 지속성을 가지나, 이미 변동성이 고점에 달한 유동성 공백 구간에서는 슬리피지/역선택이 발생해 기대 수익을 압도하므로 릿지 회귀 기반 충격 분류기(ShockScore)로 진입을 차단해야 합니다.

## 취약 구간(일반적)

- 횡보/레인지 장
- 저변동성 구간
- 급격한 유동성 저하(체결 비용 악화)

## 성과 요약 (WFO OOS; 2021–2024)

모든 지표는 전진 분석 기반 OOS 구간으로만 누적됩니다. `AB Hybrid`는 실행 모델(메이커→테이커 폴백 + 수수료/슬리피지/펀딩)을 반영한 모드이며, `Taker-only`는 더 보수적인 스트레스 모드입니다.

| 항목 | AB Hybrid | Taker-only |
| :--- | :---: | :---: |
| 누적 수익률 | +55.74% | +43.10% |
| CAGR | 11.74% | 9.39% |
| MDD | -11.99% | -12.73% |
| Sharpe | 0.78 | 0.64 |
| 운용 일수 | 1,457 | 1,457 |

![Equity vs BTC](docs/assets_public/equity_vs_btc_log.png)

## 아키텍처(개요)

```text
시장 데이터(OHLCV / funding / L2 요약)
  -> Cache 저장
  -> 피처/시그널(Trend + ShockScore)
  -> 전진 분석(train -> 파라미터/비중 고정 -> OOS test)
  -> 시뮬레이터(수수료/슬리피지/펀딩 + maker->taker 폴백)
  -> 지표/리포트(docs/assets_public/*.json 생성)
```

## 레포 구조

- CLI 실행: [cli.py](cli.py)
- WFO 엔진: [backtest/walkforward.py](backtest/walkforward.py)
- 시뮬레이터(수수료/슬리피지/펀딩): [backtest/simulators.py](backtest/simulators.py)
- 실행 모델(maker→taker): [execution/models.py](execution/models.py)
- 데이터 로더(cache 스키마): [data/loader.py](data/loader.py)
- 리포트/대시보드 JSON: [report.py](report.py)
- 예시 설정: [config/strategy_params.example.toml](config/strategy_params.example.toml)

## 재현 실행(How to Run)

재현 실행에는 본인 cache 데이터가 필요합니다. 파일 패턴/컬럼 정의는 [docs/reproducibility.md](docs/reproducibility.md)를 참고하세요.

```bash
python -m venv .venv
.\.venv\Scripts\activate
python -m pip install -r requirements.txt

python scripts/fetch_data.py --config config/strategy_params.example.toml --start 2020-01-01 --end 2024-12-31
python cli.py wfo --config config/strategy_params.example.toml --write_csv ./outputs
python report.py --config config/strategy_params.example.toml --public
python verify_portfolio.py
```

스모크 실행(빠른 동작 확인):

```bash
python scripts/fetch_data.py --config config/strategy_params.smoke.toml --start 2024-01-01 --end 2024-01-02
python cli.py wfo --config config/strategy_params.smoke.toml
```

cache 경로가 다르면 [config/strategy_params.example.toml](config/strategy_params.example.toml)의 `[data].backtest_cache_dir` / `[data].regime_cache_dir` 값을 수정하세요.
