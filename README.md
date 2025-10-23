# COLREGs Core

**Maritime Encounter Classification and Collision Risk Assessment**

항해 규칙(COLREGs)에 기반한 선박 조우 상황 분류 및 충돌 위험 평가 패키지입니다.

## Features

### 1. Encounter Situation Classification (Rule 13, 14, 15)
- **Head-on**: 정면 조우 (Rule 14)
- **Overtaking**: 추월 상황 (Rule 13)
- **Crossing**: 횡단 상황 (Rule 15)
  - Give-way vessel (피항선)
  - Stand-on vessel (유지선)

### 2. Collision Risk Assessment
- **CPA/TCPA**: Closest Point of Approach & Time to CPA
- **DCPA**: Distance at CPA
- **Risk Level**: Low / Medium / High / Critical

## Installation

```bash
cd colregs-core
poetry install
```

## Quick Start

```python
from colregs_core import EncounterClassifier, RiskAssessment, heading_to_velocity

# 1. 초기화
classifier = EncounterClassifier()
risk_assessor = RiskAssessment()

# 2. Encounter 분류
situation = classifier.classify(
    os_position=(0, 0),
    os_heading=0,
    os_speed=10,
    ts_position=(1000, 500),
    ts_heading=270,
    ts_speed=12
)

print(f"Encounter: {situation.encounter_type}")
print(f"Distance: {situation.distance:.2f} m")

# 3. 충돌 위험 평가
from colregs_core.geometry import heading_to_velocity

os_vel = heading_to_velocity(0, 10)
ts_vel = heading_to_velocity(270, 12)

risk = risk_assessor.assess(
    os_position=(0, 0),
    os_velocity=os_vel,
    ts_position=(1000, 500),
    ts_velocity=ts_vel
)

print(f"Risk: {risk.risk_level.name}")
print(f"DCPA: {risk.dcpa:.2f}m, TCPA: {risk.tcpa:.2f}s")

# 4. 권장 조치
if risk.requires_action:
    action = risk_assessor.get_recommended_action(risk)
    print(f"Action: {action}")
```

더 많은 예제는 `examples/` 디렉토리를 참고하세요.

## Installation

```bash
cd colregs-core
pip install -e .
```

For development:
```bash
pip install -e ".[dev]"  # pytest, black, mypy 포함
```
