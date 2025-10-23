# COLREGs Rules Reference

International Regulations for Preventing Collisions at Sea (COLREGs) 1972

## Part B - Steering and Sailing Rules

### Section II - Conduct of Vessels in Sight of One Another

## Rule 13: Overtaking

**Definition**:
선박이 다른 선박의 정선미로부터 22.5도를 넘는 방향(즉, 피추월선의 현등이 보이지 않는 위치)에서 접근하여 추월하는 경우.

**Key Points**:
- 추월하는 선박(overtaking vessel)이 **피항선(give-way vessel)**
- 피추월선(vessel being overtaken)은 **유지선(stand-on vessel)**
- 추월 상황은 추월이 완료될 때까지 지속
- 야간: 선미등만 보이고 현등이 보이지 않을 때

**Implementation in Code**:
```python
# Relative bearing 112.5° - 247.5° (선미 섹터)
if 112.5 <= relative_bearing <= 247.5:
    if os_speed > ts_speed:  # OS가 더 빠름
        return EncounterType.OVERTAKING
```

**Action Required**:
- 추월선: 피추월선의 진로를 완전히 피하여 통과
- 피추월선: 침로와 속력 유지

---

## Rule 14: Head-on Situation

**Definition**:
두 동력선이 정면 또는 거의 정면으로 조우하여 충돌 위험이 있는 경우.

**Key Points**:
- 양 선박 모두 우현으로 변침
- 야간: 상대선의 양쪽 현등이 모두 보이는 경우
- 주간: 상대선이 정선수 방향에 있고 마스트가 일직선상에 보이는 경우

**Implementation in Code**:
```python
# TS가 정선수(0° ± 6°) 방향
dead_ahead = (relative_bearing <= 6 or relative_bearing >= 354)

# 상대 침로가 반대(180° ± 12°)
opposite_course = abs(abs(relative_course) - 180) <= 12

if dead_ahead and opposite_course:
    return EncounterType.HEAD_ON
```

**Action Required**:
- 양 선박: 우현으로 변침
- 음향신호: 1 short blast (변침 의사 표시)

---

## Rule 15: Crossing Situation

**Definition**:
두 동력선이 서로의 진로를 횡단하여 충돌 위험이 있는 경우.

**Key Points**:
- 상대선을 우현에 두는 선박이 **피항선(give-way vessel)**
- 상대선을 좌현에 두는 선박이 **유지선(stand-on vessel)**

### Case 1: Give-way Vessel (OS가 피항선)

**Condition**:
```python
# TS가 OS의 우현(5° - 112.5°)에 위치
if 5 < relative_bearing < 112.5:
    return EncounterType.CROSSING_GIVE_WAY
```

**Action Required**:
- 피항선(OS): 상대선의 진로를 피해야 함
  - 일반적으로 **우현 변침** (상대선 선미 통과)
  - 또는 **감속** (상대선 선수 통과 회피)
  - **절대 좌현 변침 금지** (상대선 선수를 가로지름)
- 음향신호: 2 short blasts (좌현 변침 시)

### Case 2: Stand-on Vessel (OS가 유지선)

**Condition**:
```python
# TS가 OS의 좌현(247.5° - 355°)에 위치
if 247.5 < relative_bearing < 355:
    return EncounterType.CROSSING_STAND_ON
```

**Action Required**:
- 유지선(OS): 침로와 속력 유지 (Rule 17)
- 단, Rule 17(a)(ii): 피항선이 적절한 조치를 하지 않는 것이 명백해지면 단독 조치 가능
- Rule 17(b): 피항선과 너무 접근하여 피항선의 조치만으로 충돌 회피 불가능 시 즉시 조치

---

## Rule 17: Action by Stand-on Vessel

**Key Points**:
- (a)(i): 침로와 속력 유지
- (a)(ii): 피항선이 적절한 조치를 하지 않는 것이 명백해지면 단독 조치 가능
  - 단, 좌현 변침으로 피항선을 피하지 말 것
- (b): 아주 가까이 접근하여 피항선의 조치만으로는 충돌 회피 불가능 시 즉시 조치

---

## Sector Definitions

```
        000° (Dead Ahead)
         |
    315° | 045°
        \|/
   ------+------
        /|\
    225° | 135°
         |
        180° (Dead Astern)
```

### Own Ship Perspective:
- **정선수 (Dead Ahead)**: 0° ± 5°
- **우현 정횡 (Starboard Beam)**: 90°
- **정선미 (Dead Astern)**: 180°
- **좌현 정횡 (Port Beam)**: 270°

### Sector Boundaries:
- **Bow Crossing (우현)**: 5° - 112.5°
- **Stern Sector**: 112.5° - 247.5°
- **Bow Crossing (좌현)**: 247.5° - 355°

---

## Distance and Time Thresholds

### DCPA (Distance at Closest Point of Approach):
- **Critical**: < 200m (0.1 NM)
- **High**: < 500m (0.27 NM)
- **Medium**: < 1000m (0.54 NM)
- **Low**: < 2000m (1.08 NM)

### TCPA (Time to CPA):
- **Critical**: < 5 minutes
- **High**: < 10 minutes
- **Medium**: < 20 minutes
- **Low**: < 30 minutes

### Safe Distances (General Guidelines):
- Open sea: 1-2 NM (1852-3704m)
- Coastal waters: 0.5-1 NM (926-1852m)
- Restricted waters: 0.3-0.5 NM (556-926m)

*Note: 실제 안전 거리는 선박 크기, 조종성능, 해역 특성, 교통량에 따라 조정*

---

## Sound Signals (Rule 34)

### Maneuvering Signals:
- **1 short blast**: 우현 변침 (altering course to starboard)
- **2 short blasts**: 좌현 변침 (altering course to port)
- **3 short blasts**: 후진 중 (operating astern propulsion)

### Warning Signal:
- **5 or more short blasts**: 위험 경고 (doubt about other vessel's intentions)

---

## References

- IMO COLREGs 1972 (Consolidated Edition 2020)
- IALA Recommendation V-128
- IMO Resolution A.1106(29)
- UK MAIB Safety Digest
- US Coast Guard Navigation Rules

---

## Implementation Notes

### Constant Bearing, Decreasing Range (CBDR):
충돌 위험의 핵심 지표:
- 방위각이 일정하게 유지되면서 거리가 감소
- Bearing rate < 0.1 deg/s

### Aspect Angle:
Target Ship에서 Own Ship을 바라보는 방위각:
- 상대 선박의 의도 파악에 중요
- 충돌 회피 조치 효과 검증

### Bow Crossing Range (BCR):
Crossing 상황에서 TS가 OS 선수를 지나는 시점의 거리:
- BCR이 작을수록 위험
- 조기 회피 판단 지표
