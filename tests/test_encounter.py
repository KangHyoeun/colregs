"""
Test cases for encounter classification
"""
import pytest
import numpy as np
from colregs_core import EncounterClassifier, EncounterType


class TestEncounterClassifier:
    """
    COLREGs Rule 13, 14, 15 시나리오 기반 테스트
    """
    
    def setup_method(self):
        """각 테스트 전 실행"""
        self.classifier = EncounterClassifier(safe_distance=3000.0)
    
    def test_head_on_situation(self):
        """
        Rule 14: Head-on situation
        
        시나리오:
        - OS: (0, 0), heading 0° (North), 10 m/s
        - TS: (0, 2000), heading 180° (South), 10 m/s
        - 정면 충돌 코스
        """
        situation = self.classifier.classify(
            os_position=(0, 0),
            os_heading=0,
            os_speed=10,
            ts_position=(0, 2000),
            ts_heading=180,
            ts_speed=10
        )
        
        assert situation.encounter_type == EncounterType.HEAD_ON
        assert abs(situation.relative_bearing) < 10  # 거의 0도
        print(f"✓ Head-on: bearing={situation.relative_bearing:.1f}°")
    
    def test_crossing_give_way_starboard(self):
        """
        Rule 15: Crossing - OS가 give-way vessel
        
        시나리오:
        - OS: (0, 0), heading 0° (North)
        - TS: (1000, 1000), heading 270° (West)
        - TS가 OS의 우현(약 45°)에서 접근
        """
        situation = self.classifier.classify(
            os_position=(0, 0),
            os_heading=0,
            os_speed=10,
            ts_position=(1000, 1000),
            ts_heading=270,
            ts_speed=12
        )
        
        assert situation.encounter_type == EncounterType.CROSSING_GIVE_WAY
        assert 5 < situation.relative_bearing < 112.5
        print(f"✓ Crossing give-way: bearing={situation.relative_bearing:.1f}°")
    
    def test_crossing_stand_on_port(self):
        """
        Rule 15: Crossing - OS가 stand-on vessel
        
        시나리오:
        - OS: (0, 0), heading 0° (North)
        - TS: (-1000, 1000), heading 90° (East)
        - TS가 OS의 좌현(약 315°)에서 접근
        """
        situation = self.classifier.classify(
            os_position=(0, 0),
            os_heading=0,
            os_speed=10,
            ts_position=(-1000, 1000),
            ts_heading=90,
            ts_speed=12
        )
        
        assert situation.encounter_type == EncounterType.CROSSING_STAND_ON
        assert 247.5 < situation.relative_bearing < 355
        print(f"✓ Crossing stand-on: bearing={situation.relative_bearing:.1f}°")
    
    def test_overtaking_from_astern(self):
        """
        Rule 13: Overtaking
        
        시나리오:
        - OS: (0, 1000), heading 0° (North), 15 m/s (빠름)
        - TS: (0, 0), heading 0° (North), 8 m/s (느림)
        - OS가 TS를 정선미에서 추월
        """
        situation = self.classifier.classify(
            os_position=(0, 1000),
            os_heading=0,
            os_speed=15,
            ts_position=(0, 0),
            ts_heading=0,
            ts_speed=8
        )
        
        assert situation.encounter_type == EncounterType.OVERTAKING
        assert 112.5 <= situation.relative_bearing <= 247.5
        print(f"✓ Overtaking: bearing={situation.relative_bearing:.1f}°")
    
    def test_safe_distance(self):
        """
        안전 거리 밖 - SAFE
        
        시나리오:
        - OS: (0, 0)
        - TS: (5000, 0) - 안전 거리(3000m) 밖
        """
        situation = self.classifier.classify(
            os_position=(0, 0),
            os_heading=0,
            os_speed=10,
            ts_position=(5000, 0),
            ts_heading=180,
            ts_speed=10
        )
        
        assert situation.encounter_type == EncounterType.SAFE
        assert situation.distance > 3000
        print(f"✓ Safe: distance={situation.distance:.1f}m")
    
    def test_boundary_cases(self):
        """
        경계값 테스트
        
        Rule 15 경계: 5°, 112.5°, 247.5°, 355°
        """
        # 정확히 6도 - crossing give-way
        situation = self.classifier.classify(
            os_position=(0, 0),
            os_heading=0,
            os_speed=10,
            ts_position=(100, 1000),  # 약 5.7도
            ts_heading=270,
            ts_speed=10
        )
        assert situation.encounter_type == EncounterType.CROSSING_GIVE_WAY
        
        # 정확히 113도 근처
        situation = self.classifier.classify(
            os_position=(0, 0),
            os_heading=0,
            os_speed=10,
            ts_position=(1732, -1000),  # 약 120도
            ts_heading=0,
            ts_speed=15
        )
        assert situation.encounter_type == EncounterType.OVERTAKING
        print("✓ Boundary cases passed")
    
    def test_action_requirements(self):
        """
        각 상황별 조치 요구사항 확인
        """
        # Head-on
        action = self.classifier.get_action_requirement(EncounterType.HEAD_ON)
        assert "우현" in action
        assert "Rule 14" in action
        
        # Crossing give-way
        action = self.classifier.get_action_requirement(EncounterType.CROSSING_GIVE_WAY)
        assert "give-way" in action
        assert "Rule 15" in action
        
        print("✓ Action requirements correct")


def run_visual_test():
    """
    시각적 확인용 다양한 시나리오 테스트
    """
    classifier = EncounterClassifier(safe_distance=2000)
    
    test_scenarios = [
        {
            "name": "Head-on",
            "os_pos": (0, 0), "os_hdg": 0, "os_spd": 10,
            "ts_pos": (0, 1500), "ts_hdg": 180, "ts_spd": 10
        },
        {
            "name": "Overtaking",
            "os_pos": (0, 500), "os_hdg": 0, "os_spd": 15,
            "ts_pos": (0, 0), "ts_hdg": 0, "ts_spd": 8
        },
        {
            "name": "Crossing - Give way (Starboard)",
            "os_pos": (0, 0), "os_hdg": 0, "os_spd": 10,
            "ts_pos": (800, 800), "ts_hdg": 270, "ts_spd": 12
        },
        {
            "name": "Crossing - Stand on (Port)",
            "os_pos": (0, 0), "os_hdg": 0, "os_spd": 10,
            "ts_pos": (-800, 800), "ts_hdg": 90, "ts_spd": 12
        },
        {
            "name": "Safe - Far away",
            "os_pos": (0, 0), "os_hdg": 0, "os_spd": 10,
            "ts_pos": (3000, 0), "ts_hdg": 180, "ts_spd": 10
        }
    ]
    
    print("\n" + "="*70)
    print("COLREGs Encounter Classification Test Results")
    print("="*70)
    
    for scenario in test_scenarios:
        situation = classifier.classify(
            os_position=scenario["os_pos"],
            os_heading=scenario["os_hdg"],
            os_speed=scenario["os_spd"],
            ts_position=scenario["ts_pos"],
            ts_heading=scenario["ts_hdg"],
            ts_speed=scenario["ts_spd"]
        )
        
        print(f"\n{scenario['name']}:")
        print(f"  Type: {situation.encounter_type.value}")
        print(f"  Relative Bearing: {situation.relative_bearing:.1f}°")
        print(f"  Relative Course: {situation.relative_course:.1f}°")
        print(f"  Distance: {situation.distance:.1f} m")
        print(f"  Aspect Angle: {situation.aspect_angle:.1f}°")
        print(f"  Action: {classifier.get_action_requirement(situation.encounter_type)}")
    
    print("\n" + "="*70)


if __name__ == "__main__":
    # pytest 실행
    pytest.main([__file__, "-v"])
    
    # 시각적 테스트
    print("\n")
    run_visual_test()
