# COLREGs Core + ir-sim 통합 가이드

## 개요

이 문서는 `colregs-core` 패키지를 `ir-sim` 시뮬레이션 환경에 통합하는 방법을 설명합니다.

---

## 통합 테스트 결과

### ✅ 시뮬레이션 통합 테스트 완료

다음 5가지 시나리오로 통합 테스트 완료:

1. **Head-on Situation**: 정면 조우 감지 및 위험도 평가 ✓
2. **Crossing Give-way**: 우현 crossing 상황 분류 ✓
3. **Overtaking**: 추월 상황 처리 ✓
4. **Multiple Targets**: 다중 목표선 우선순위 평가 ✓
5. **Dynamic Scenario**: 동적 상황 변화 추적 ✓

**실행 방법**:
```bash
cd colregs-core
python3 tests/test_simulation_integration.py
```

---

## ir-sim 통합 방법

### 1. 패키지 설치

```bash
# colregs-core 설치
cd /path/to/colregs-core
pip install -e .

# ir-sim 설치 (이미 되어있다고 가정)
# cd /path/to/ir-sim
# pip install -e .
```

---

### 2. ir-sim Observation에 COLREGs 정보 추가

#### 기존 ir-sim 구조 (추정)

```python
# ir_sim/env.py
class NavigationEnv:
    def __init__(self):
        self.own_ship = OwnShip()
        self.target_ships = []
    
    def get_observation(self):
        obs = {
            'own_ship': {...},
            'targets': [...]
        }
        return obs
```

#### COLREGs 통합

```python
# ir_sim/env.py
from colregs_core import EncounterClassifier, RiskAssessment

class NavigationEnv:
    def __init__(self):
        self.own_ship = OwnShip()
        self.target_ships = []
        
        # COLREGs 모듈 추가
        self.encounter_classifier = EncounterClassifier(
            safe_distance=2500.0  # meters, 해역 특성에 맞게 조정
        )
        self.risk_assessor = RiskAssessment()
    
    def get_observation(self):
        obs = {
            'own_ship': self._get_own_ship_state(),
            'targets': []
        }
        
        for ts in self.target_ships:
            # 기존 observation
            target_obs = {
                'position': ts.position,
                'heading': ts.heading,
                'speed': ts.speed,
                # ... 기존 정보들
            }
            
            # COLREGs 정보 추가
            situation = self.encounter_classifier.classify(
                os_position=self.own_ship.position,
                os_heading=self.own_ship.heading,
                os_speed=self.own_ship.speed,
                ts_position=ts.position,
                ts_heading=ts.heading,
                ts_speed=ts.speed
            )
            
            risk = self.risk_assessor.assess(
                os_position=self.own_ship.position,
                os_velocity=self.own_ship.get_velocity(),
                ts_position=ts.position,
                ts_velocity=ts.get_velocity()
            )
            
            # COLREGs 정보 추가
            target_obs.update({
                'encounter_type': situation.encounter_type.value,
                'relative_bearing': situation.relative_bearing,
                'risk_level': risk.risk_level.value,
                'dcpa': risk.dcpa,
                'tcpa': risk.tcpa,
                'requires_action': risk.requires_action
            })
            
            obs['targets'].append(target_obs)
        
        return obs
```

---

### 3. Reward Shaping에 COLREGs 적용

#### Encounter Type별 차등 Reward

```python
# ir_sim/rewards.py (또는 env.py 내부)
from colregs_core import EncounterType, RiskLevel

class RewardCalculator:
    def __init__(self):
        self.encounter_classifier = EncounterClassifier()
        self.risk_assessor = RiskAssessment()
        
        # Encounter type별 가중치
        self.encounter_weights = {
            EncounterType.CROSSING_GIVE_WAY: 2.0,   # 피항선 책임 강조
            EncounterType.HEAD_ON: 1.8,              # 양쪽 책임
            EncounterType.OVERTAKING: 1.5,           # 추월선 책임
            EncounterType.CROSSING_STAND_ON: 1.0,   # 유지선
        }
    
    def calculate_reward(self, state, action, next_state):
        reward = 0.0
        
        for ts in state['targets']:
            situation = self.encounter_classifier.classify(...)
            risk = self.risk_assessor.assess(...)
            
            # 위험도 기본 페널티
            risk_penalty = {
                RiskLevel.SAFE: 0,
                RiskLevel.LOW: -0.5,
                RiskLevel.MEDIUM: -2.0,
                RiskLevel.HIGH: -5.0,
                RiskLevel.CRITICAL: -10.0
            }[risk.risk_level]
            
            # Encounter type별 가중치 적용
            weight = self.encounter_weights.get(
                situation.encounter_type, 1.0
            )
            
            reward += risk_penalty * weight
            
            # COLREGs 준수 보너스
            if self._is_following_colregs(situation, action):
                reward += 2.0
        
        return reward
    
    def _is_following_colregs(self, situation, action):
        """COLREGs 규칙 준수 여부 확인"""
        
        # Head-on: 우현 변침
        if situation.encounter_type == EncounterType.HEAD_ON:
            return action['rudder'] > 0  # 우현 변침
        
        # Crossing give-way: 회피 조치
        elif situation.encounter_type == EncounterType.CROSSING_GIVE_WAY:
            # 우현 변침 또는 감속
            return action['rudder'] > 0 or action['throttle'] < 0
        
        # Crossing stand-on: 침로 유지
        elif situation.encounter_type == EncounterType.CROSSING_STAND_ON:
            return abs(action['rudder']) < 0.1  # 침로 유지
        
        return True
```

---

### 4. DRL Agent에 COLREGs 정보 활용

#### Observation Space 확장

```python
# DRL-otter-navigation/env/observation.py
def get_observation_space(self):
    spaces = {
        # 기존 observation
        'distance': gym.spaces.Box(low=0, high=10000, shape=(n_targets,)),
        'bearing': gym.spaces.Box(low=0, high=360, shape=(n_targets,)),
        
        # COLREGs 정보 추가
        'encounter_type': gym.spaces.MultiDiscrete([6] * n_targets),  # 6 types
        'risk_level': gym.spaces.MultiDiscrete([5] * n_targets),      # 5 levels
        'dcpa': gym.spaces.Box(low=0, high=10000, shape=(n_targets,)),
        'tcpa': gym.spaces.Box(low=-1000, high=10000, shape=(n_targets,)),
    }
    return gym.spaces.Dict(spaces)
```

#### Policy Network에서 활용

```python
# DRL-otter-navigation/networks/policy.py
class COLREGsAwarePolicy(nn.Module):
    def __init__(self):
        super().__init__()
        
        # Encounter type embedding
        self.encounter_embed = nn.Embedding(6, 16)
        
        # Risk level embedding
        self.risk_embed = nn.Embedding(5, 8)
        
        # Feature extraction
        self.fc = nn.Sequential(
            nn.Linear(input_dim + 16 + 8, 256),
            nn.ReLU(),
            nn.Linear(256, 128),
            nn.ReLU()
        )
        
    def forward(self, obs):
        # Encounter type embedding
        encounter_emb = self.encounter_embed(obs['encounter_type'])
        
        # Risk level embedding
        risk_emb = self.risk_embed(obs['risk_level'])
        
        # Concatenate all features
        features = torch.cat([
            obs['basic_features'],
            encounter_emb,
            risk_emb
        ], dim=-1)
        
        return self.fc(features)
```

---

### 5. 실전 통합 예시

#### 전체 통합 코드

```python
# ir_sim/enhanced_env.py
from colregs_core import (
    EncounterClassifier,
    RiskAssessment,
    EncounterType,
    RiskLevel
)

class COLREGsEnhancedNavigationEnv:
    """COLREGs 기능이 통합된 항해 환경"""
    
    def __init__(self):
        # 기존 ir-sim 초기화
        # self.base_env = NavigationEnv(...)
        
        # COLREGs 모듈
        self.encounter_classifier = EncounterClassifier(
            safe_distance=2000.0
        )
        self.risk_assessor = RiskAssessment(
            dcpa_critical=200.0,
            tcpa_critical=300.0
        )
        
    def step(self, action):
        # 기존 step 실행
        # next_state, reward, done, info = self.base_env.step(action)
        
        # COLREGs 정보 추가
        colregs_info = self._get_colregs_info()
        
        # Reward에 COLREGs 반영
        reward = self._calculate_colregs_aware_reward(
            action, colregs_info
        )
        
        # Info에 COLREGs 정보 추가
        info['colregs'] = colregs_info
        
        return next_state, reward, done, info
    
    def _get_colregs_info(self):
        """모든 목표선에 대한 COLREGs 정보"""
        colregs_info = []
        
        for ts in self.target_ships:
            situation = self.encounter_classifier.classify(
                self.own_ship.position,
                self.own_ship.heading,
                self.own_ship.speed,
                ts.position,
                ts.heading,
                ts.speed
            )
            
            risk = self.risk_assessor.assess(
                self.own_ship.position,
                self.own_ship.velocity,
                ts.position,
                ts.velocity
            )
            
            colregs_info.append({
                'target_id': ts.id,
                'encounter_type': situation.encounter_type,
                'risk_level': risk.risk_level,
                'dcpa': risk.dcpa,
                'tcpa': risk.tcpa,
                'requires_action': risk.requires_action,
                'colregs_action': self.encounter_classifier.get_action_requirement(
                    situation.encounter_type
                )
            })
        
        return colregs_info
    
    def _calculate_colregs_aware_reward(self, action, colregs_info):
        """COLREGs를 고려한 reward 계산"""
        reward = 0.0
        
        for info in colregs_info:
            # 위험도 페널티
            if info['risk_level'] == RiskLevel.CRITICAL:
                reward -= 10.0
            elif info['risk_level'] == RiskLevel.HIGH:
                reward -= 5.0
            elif info['risk_level'] == RiskLevel.MEDIUM:
                reward -= 2.0
            
            # Encounter type별 가중치
            if info['encounter_type'] == EncounterType.CROSSING_GIVE_WAY:
                reward *= 1.5  # Give-way vessel 책임 강조
        
        return reward
```

---

## 사용 예시

### 학습 시

```python
from ir_sim import COLREGsEnhancedNavigationEnv
from stable_baselines3 import PPO

# 환경 생성
env = COLREGsEnhancedNavigationEnv()

# 학습
model = PPO('MlpPolicy', env, verbose=1)
model.learn(total_timesteps=100000)

# 학습 중 COLREGs 정보 확인
obs = env.reset()
for step in range(1000):
    action, _ = model.predict(obs)
    obs, reward, done, info = env.step(action)
    
    if info['colregs']:
        for ts_info in info['colregs']:
            if ts_info['requires_action']:
                print(f"⚠️ {ts_info['target_id']}: "
                      f"{ts_info['encounter_type'].value} - "
                      f"{ts_info['risk_level'].name}")
    
    if done:
        break
```

### 평가 시

```python
from colregs_core import EncounterClassifier, RiskAssessment

# 시나리오 평가
def evaluate_colregs_compliance(env, model, n_episodes=100):
    """COLREGs 준수율 평가"""
    
    stats = {
        'total_encounters': 0,
        'colregs_compliant': 0,
        'collisions': 0,
        'encounter_types': {}
    }
    
    for episode in range(n_episodes):
        obs = env.reset()
        done = False
        
        while not done:
            action, _ = model.predict(obs)
            obs, reward, done, info = env.step(action)
            
            # COLREGs 준수 확인
            if info['colregs']:
                for ts_info in info['colregs']:
                    stats['total_encounters'] += 1
                    
                    encounter_type = ts_info['encounter_type'].value
                    stats['encounter_types'][encounter_type] = \
                        stats['encounter_types'].get(encounter_type, 0) + 1
                    
                    # COLREGs 준수 여부
                    if check_colregs_compliance(action, ts_info):
                        stats['colregs_compliant'] += 1
    
    compliance_rate = stats['colregs_compliant'] / stats['total_encounters']
    print(f"COLREGs Compliance Rate: {compliance_rate:.2%}")
    print(f"Encounter Types Distribution: {stats['encounter_types']}")
    
    return stats
```

---

## 성능 최적화 팁

### 1. 거리 기반 필터링

```python
# 먼 거리의 선박은 COLREGs 계산 생략
def get_colregs_info_optimized(self):
    for ts in self.target_ships:
        distance = calculate_distance(
            self.own_ship.position,
            ts.position
        )
        
        # 10km 밖은 생략
        if distance > 10000:
            continue
        
        # COLREGs 계산 수행
        situation = self.encounter_classifier.classify(...)
```

### 2. 업데이트 주기 조정

```python
# 매 스텝마다가 아닌 일정 주기로 업데이트
class COLREGsCache:
    def __init__(self, update_interval=10):
        self.update_interval = update_interval
        self.step_count = 0
        self.cached_info = None
    
    def get_colregs_info(self, force_update=False):
        if (force_update or 
            self.step_count % self.update_interval == 0 or
            self.cached_info is None):
            self.cached_info = self._compute_colregs_info()
        
        self.step_count += 1
        return self.cached_info
```

---

## 테스트 및 검증

### 단위 테스트

```bash
# COLREGs 모듈 테스트
cd colregs-core
python3 -m pytest tests/

# 시뮬레이션 통합 테스트
python3 tests/test_simulation_integration.py
```

### ir-sim 통합 테스트

```python
# ir_sim/tests/test_colregs_integration.py
def test_colregs_integration():
    env = COLREGsEnhancedNavigationEnv()
    
    # Head-on 시나리오
    env.reset()
    env.add_target_ship(...)
    
    obs = env.get_observation()
    assert 'encounter_type' in obs['targets'][0]
    assert 'risk_level' in obs['targets'][0]
```

---

## 문제 해결

### Q: 좌표계가 맞지 않습니다

**A**: colregs-core는 다음 좌표계를 사용합니다:
- Position: (x, y) - x=East, y=North
- Heading: 0°=North, clockwise

ir-sim의 좌표계에 맞게 변환하세요.

### Q: 성능이 느립니다

**A**: 
1. 거리 기반 필터링 적용
2. 업데이트 주기 조정
3. 필요한 정보만 계산

### Q: Encounter type이 이상합니다

**A**: 
1. 안전 거리 임계값 확인 (`safe_distance`)
2. 선박 속도 확인 (0이 아닌지)
3. 좌표계 확인

---

## 참고 자료

- `colregs-core/docs/usage_guide.md`: 상세 API 문서
- `colregs-core/docs/colregs_rules.md`: COLREGs 규칙 설명
- `colregs-core/examples/`: 사용 예제
- `colregs-core/tests/test_simulation_integration.py`: 통합 테스트 예제

---

## 다음 단계

1. ✅ COLREGs 모듈 개발 완료
2. ✅ 시뮬레이션 통합 테스트 완료
3. ⬜ 실제 ir-sim에 통합
4. ⬜ DRL 학습에 적용
5. ⬜ 성능 평가 및 논문 작성

---

**작성일**: 2025-10-22  
**버전**: 1.0  
**문의**: colregs-core 패키지 개발자
