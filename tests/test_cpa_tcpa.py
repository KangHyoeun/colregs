"""
Test cases for CPA/TCPA calculation and risk assessment
"""
import pytest
import numpy as np
from colregs_core import (
    RiskAssessment,
    RiskLevel,
    calculate_cpa_tcpa,
    heading_to_velocity
)


class TestCPATCPA:
    """
    CPA/TCPA 계산 정확성 테스트
    """
    
    def test_collision_course(self):
        """
        정면 충돌 코스
        
        시나리오:
        - OS: (0, 0), heading 0°, 10 m/s
        - TS: (0, 2000), heading 180°, 10 m/s
        - DCPA = 0 (충돌), TCPA = 100초
        """
        os_vel = heading_to_velocity(0, 10)
        ts_vel = heading_to_velocity(180, 10)
        
        dcpa, tcpa = calculate_cpa_tcpa(
            os_position=(0, 0),
            os_velocity=os_vel,
            ts_position=(0, 2000),
            ts_velocity=ts_vel
        )
        
        assert dcpa < 1.0  # 거의 0
        assert abs(tcpa - 100) < 1.0  # 2000m / 20m/s = 100s
        print(f"✓ Collision course: DCPA={dcpa:.2f}m, TCPA={tcpa:.1f}s")
    
    def test_crossing_miss(self):
        """
        교차 통과 (충돌하지 않음)
        
        시나리오:
        - OS: (0, 0), heading 0° (North), 10 m/s
        - TS: (1000, 1000), heading 270° (West), 10 m/s
        """
        os_vel = heading_to_velocity(0, 10)
        ts_vel = heading_to_velocity(270, 10)
        
        dcpa, tcpa = calculate_cpa_tcpa(
            os_position=(0, 0),
            os_velocity=os_vel,
            ts_position=(1000, 1000),
            ts_velocity=ts_vel
        )
        
        assert dcpa > 0  # 충돌하지 않음
        assert tcpa > 0  # 미래에 CPA 발생
        print(f"✓ Crossing miss: DCPA={dcpa:.2f}m, TCPA={tcpa:.1f}s")
    
    def test_parallel_same_speed(self):
        """
        평행 항해 (같은 속도)
        
        시나리오:
        - OS: (0, 0), heading 0°, 10 m/s
        - TS: (500, 0), heading 0°, 10 m/s
        - DCPA = 500m (현재 거리), TCPA = inf
        """
        os_vel = heading_to_velocity(0, 10)
        ts_vel = heading_to_velocity(0, 10)
        
        dcpa, tcpa = calculate_cpa_tcpa(
            os_position=(0, 0),
            os_velocity=os_vel,
            ts_position=(500, 0),
            ts_velocity=ts_vel
        )
        
        assert abs(dcpa - 500) < 1.0
        assert np.isinf(tcpa)
        print(f"✓ Parallel: DCPA={dcpa:.2f}m, TCPA=inf")
    
    def test_past_cpa(self):
        """
        이미 CPA 통과한 경우
        
        시나리오:
        - OS와 TS가 서로 멀어지는 중
        """
        os_vel = heading_to_velocity(0, 10)
        ts_vel = heading_to_velocity(180, 10)
        
        dcpa, tcpa = calculate_cpa_tcpa(
            os_position=(0, 1000),
            os_velocity=os_vel,
            ts_position=(0, 0),
            ts_velocity=ts_vel
        )
        
        assert tcpa < 0  # 음수 = 이미 통과
        print(f"✓ Past CPA: DCPA={dcpa:.2f}m, TCPA={tcpa:.1f}s (negative)")
    
    def test_overtaking_cpa(self):
        """
        추월 상황의 CPA
        
        시나리오:
        - OS가 TS를 추월 중
        - 약간 옆으로 비켜서 추월
        """
        os_vel = heading_to_velocity(0, 15)  # 빠름
        ts_vel = heading_to_velocity(0, 8)   # 느림
        
        dcpa, tcpa = calculate_cpa_tcpa(
            os_position=(50, 0),     # 약간 옆
            os_velocity=os_vel,
            ts_position=(0, 500),    # 앞
            ts_velocity=ts_vel
        )
        
        assert tcpa > 0
        assert dcpa > 40  # 최소 50m 옆으로 통과
        print(f"✓ Overtaking CPA: DCPA={dcpa:.2f}m, TCPA={tcpa:.1f}s")


class TestRiskAssessment:
    """
    위험도 평가 테스트
    """
    
    def setup_method(self):
        """각 테스트 전 실행"""
        self.risk_assessor = RiskAssessment()
    
    def test_critical_risk(self):
        """
        긴급 위험 상황 (CRITICAL)
        
        시나리오:
        - DCPA < 200m
        - TCPA < 5분
        """
        os_vel = heading_to_velocity(0, 10)
        ts_vel = heading_to_velocity(180, 10)
        
        risk = self.risk_assessor.assess(
            os_position=(0, 0),
            os_velocity=os_vel,
            ts_position=(0, 300),  # 300m ahead
            ts_velocity=ts_vel
        )
        
        assert risk.risk_level == RiskLevel.CRITICAL
        assert risk.is_dangerous
        assert risk.requires_action
        print(f"✓ Critical risk: {risk.risk_level.name}")
        print(f"  Action: {self.risk_assessor.get_recommended_action(risk)}")
    
    def test_high_risk(self):
        """
        높은 위험 (HIGH)
        
        시나리오:
        - DCPA < 500m
        - TCPA < 10분
        """
        os_vel = heading_to_velocity(0, 10)
        ts_vel = heading_to_velocity(180, 10)
        
        risk = self.risk_assessor.assess(
            os_position=(0, 0),
            os_velocity=os_vel,
            ts_position=(0, 800),
            ts_velocity=ts_vel
        )
        
        assert risk.risk_level in [RiskLevel.HIGH, RiskLevel.CRITICAL]
        assert risk.is_dangerous
        print(f"✓ High risk: {risk.risk_level.name}")
    
    def test_medium_risk(self):
        """
        중간 위험 (MEDIUM)
        
        시나리오:
        - DCPA < 1000m
        - TCPA < 20분
        """
        os_vel = heading_to_velocity(0, 10)
        ts_vel = heading_to_velocity(270, 10)
        
        risk = self.risk_assessor.assess(
            os_position=(0, 0),
            os_velocity=os_vel,
            ts_position=(800, 800),
            ts_velocity=ts_vel
        )
        
        assert risk.requires_action
        print(f"✓ Medium risk: {risk.risk_level.name}, DCPA={risk.dcpa:.0f}m")
    
    def test_low_risk(self):
        """
        낮은 위험 (LOW)
        
        시나리오:
        - DCPA < 2000m
        - TCPA < 30분
        """
        os_vel = heading_to_velocity(0, 10)
        ts_vel = heading_to_velocity(270, 8)
        
        risk = self.risk_assessor.assess(
            os_position=(0, 0),
            os_velocity=os_vel,
            ts_position=(1500, 1500),
            ts_velocity=ts_vel
        )
        
        assert risk.risk_level in [RiskLevel.LOW, RiskLevel.MEDIUM]
        print(f"✓ Low risk: {risk.risk_level.name}")
    
    def test_safe_situation(self):
        """
        안전 (SAFE)
        
        시나리오:
        - DCPA > 2000m or TCPA > 30분
        """
        os_vel = heading_to_velocity(0, 10)
        ts_vel = heading_to_velocity(90, 10)
        
        risk = self.risk_assessor.assess(
            os_position=(0, 0),
            os_velocity=os_vel,
            ts_position=(3000, 3000),
            ts_velocity=ts_vel
        )
        
        assert not risk.is_dangerous
        print(f"✓ Safe: {risk.risk_level.name}")
    
    def test_constant_bearing(self):
        """
        Constant bearing (방위각 불변) 체크
        
        시나리오:
        - 충돌 코스에서 방위각 변화율이 거의 0
        """
        os_vel = heading_to_velocity(0, 10)
        ts_vel = heading_to_velocity(180, 10)
        
        risk = self.risk_assessor.assess(
            os_position=(0, 0),
            os_velocity=os_vel,
            ts_position=(0, 1000),
            ts_velocity=ts_vel
        )
        
        # 방위각 변화율이 거의 0이어야 함
        assert abs(risk.bearing_rate) < 0.1
        print(f"✓ Constant bearing: rate={risk.bearing_rate:.4f} deg/s")
    
    def test_multiple_targets(self):
        """
        다중 목표선 평가
        
        시나리오:
        - 여러 선박 중 가장 위험한 선박 식별
        """
        os_pos = (0, 0)
        os_vel = heading_to_velocity(0, 10)
        
        targets = [
            # Target 1: 멀리 있음 (안전)
            ((3000, 3000), heading_to_velocity(180, 10)),
            # Target 2: 가까우나 멀어짐
            ((100, -100), heading_to_velocity(180, 10)),
            # Target 3: 충돌 위험 (가장 위험)
            ((0, 500), heading_to_velocity(180, 10))
        ]
        
        result = self.risk_assessor.get_most_dangerous_target(
            os_pos, os_vel, targets
        )
        
        assert result is not None
        target_idx, most_dangerous = result
        assert target_idx == 2  # Target 3이 가장 위험
        assert most_dangerous.is_dangerous
        print(f"✓ Multiple targets: Most dangerous = Target {target_idx+1}")
        print(f"  Risk: {most_dangerous.risk_level.name}, DCPA={most_dangerous.dcpa:.0f}m")


def run_scenario_tests():
    """
    실전 시나리오 종합 테스트
    """
    risk_assessor = RiskAssessment()
    
    scenarios = [
        {
            "name": "1. Head-on collision course",
            "os_pos": (0, 0), "os_vel": heading_to_velocity(0, 10),
            "ts_pos": (0, 800), "ts_vel": heading_to_velocity(180, 10),
            "expected_risk": RiskLevel.CRITICAL
        },
        {
            "name": "2. Crossing - Close miss",
            "os_pos": (0, 0), "os_vel": heading_to_velocity(0, 10),
            "ts_pos": (600, 600), "ts_vel": heading_to_velocity(270, 12),
            "expected_risk": RiskLevel.HIGH
        },
        {
            "name": "3. Overtaking - Safe distance",
            "os_pos": (100, 0), "os_vel": heading_to_velocity(0, 15),
            "ts_pos": (0, 500), "ts_vel": heading_to_velocity(0, 8),
            "expected_risk": RiskLevel.LOW
        },
        {
            "name": "4. Parallel - No risk",
            "os_pos": (0, 0), "os_vel": heading_to_velocity(0, 10),
            "ts_pos": (500, 0), "ts_vel": heading_to_velocity(0, 10),
            "expected_risk": RiskLevel.SAFE
        }
    ]
    
    print("\n" + "="*70)
    print("Collision Risk Assessment - Scenario Tests")
    print("="*70)
    
    for scenario in scenarios:
        risk = risk_assessor.assess(
            os_position=scenario["os_pos"],
            os_velocity=scenario["os_vel"],
            ts_position=scenario["ts_pos"],
            ts_velocity=scenario["ts_vel"]
        )
        
        print(f"\n{scenario['name']}")
        print(f"  Risk Level: {risk.risk_level.name}")
        print(f"  DCPA: {risk.dcpa:.1f} m")
        print(f"  TCPA: {risk.tcpa:.1f} s ({risk.tcpa/60:.1f} min)")
        print(f"  Distance: {risk.distance:.1f} m")
        print(f"  Bearing Rate: {risk.bearing_rate:.4f} deg/s")
        print(f"  Recommended: {risk_assessor.get_recommended_action(risk)[:60]}...")
    
    print("\n" + "="*70)


if __name__ == "__main__":
    # pytest 실행
    pytest.main([__file__, "-v"])
    
    # 시나리오 테스트
    print("\n")
    run_scenario_tests()
