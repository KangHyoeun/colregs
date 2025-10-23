"""
항해 기하학 계산 유틸리티
"""
import numpy as np
from typing import Tuple


def normalize_angle(angle: float) -> float:
    """
    각도를 -180 ~ 180 범위로 정규화
    
    Args:
        angle: 각도 (degrees)
    
    Returns:
        정규화된 각도 [-180, 180]
    """
    return ((angle + 180) % 360) - 180


def normalize_angle_360(angle: float) -> float:
    """
    각도를 0 ~ 360 범위로 정규화
    
    Args:
        angle: 각도 (degrees)
    
    Returns:
        정규화된 각도 [0, 360)
    """
    return angle % 360


def calculate_relative_bearing(
    os_position: Tuple[float, float],
    os_heading: float,
    ts_position: Tuple[float, float]
) -> float:
    """
    Own Ship에서 Target Ship의 상대 방위각 계산
    
    Args:
        os_position: OS 위치 (x, y) in meters
        os_heading: OS heading (degrees, 0=North, clockwise)
        ts_position: TS 위치 (x, y) in meters
    
    Returns:
        상대 방위각 (degrees, [0, 360), 0=dead ahead)
    """
    dx = ts_position[0] - os_position[0]
    dy = ts_position[1] - os_position[1]
    
    # 절대 방위각 계산 (North=0, clockwise)
    absolute_bearing = np.degrees(np.arctan2(dx, dy))
    
    # 상대 방위각 = 절대 방위각 - OS heading
    relative_bearing = absolute_bearing - os_heading
    
    return normalize_angle_360(relative_bearing)


def calculate_distance(
    pos1: Tuple[float, float],
    pos2: Tuple[float, float]
) -> float:
    """
    두 위치 간 유클리드 거리 계산
    
    Args:
        pos1: 위치 1 (x, y)
        pos2: 위치 2 (x, y)
    
    Returns:
        거리 (meters)
    """
    dx = pos2[0] - pos1[0]
    dy = pos2[1] - pos1[1]
    return np.sqrt(dx**2 + dy**2)


def calculate_relative_velocity(
    os_velocity: Tuple[float, float],
    ts_velocity: Tuple[float, float]
) -> Tuple[float, float]:
    """
    상대 속도 벡터 계산 (TS relative to OS)
    
    Args:
        os_velocity: OS 속도 벡터 (vx, vy) in m/s
        ts_velocity: TS 속도 벡터 (vx, vy) in m/s
    
    Returns:
        상대 속도 벡터 (vx, vy)
    """
    return (
        ts_velocity[0] - os_velocity[0],
        ts_velocity[1] - os_velocity[1]
    )


def heading_to_velocity(heading: float, speed: float) -> Tuple[float, float]:
    """
    Heading과 속도를 속도 벡터로 변환
    
    Args:
        heading: Heading (degrees, 0=North, clockwise)
        speed: 속도 (m/s or knots)
    
    Returns:
        속도 벡터 (vx, vy)
    """
    heading_rad = np.radians(heading)
    vx = speed * np.sin(heading_rad)
    vy = speed * np.cos(heading_rad)
    return (vx, vy)


def velocity_to_heading_speed(velocity: Tuple[float, float]) -> Tuple[float, float]:
    """
    속도 벡터를 heading과 속도로 변환
    
    Args:
        velocity: 속도 벡터 (vx, vy)
    
    Returns:
        (heading, speed)
        heading: degrees, [0, 360)
        speed: magnitude of velocity
    """
    vx, vy = velocity
    speed = np.sqrt(vx**2 + vy**2)
    heading = np.degrees(np.arctan2(vx, vy))
    return (normalize_angle_360(heading), speed)


def calculate_aspect_angle(
    ts_heading: float,
    os_position: Tuple[float, float],
    ts_position: Tuple[float, float]
) -> float:
    """
    Target Ship의 aspect angle 계산
    (TS에서 OS를 바라보는 상대 방위각)
    
    Args:
        ts_heading: TS heading (degrees)
        os_position: OS 위치 (x, y)
        ts_position: TS 위치 (x, y)
    
    Returns:
        Aspect angle (degrees, [0, 360))
        0 = OS가 TS의 정선수 방향
        90 = OS가 TS의 우현
        180 = OS가 TS의 정선미
        270 = OS가 TS의 좌현
    """
    dx = os_position[0] - ts_position[0]
    dy = os_position[1] - ts_position[1]
    
    absolute_bearing = np.degrees(np.arctan2(dx, dy))
    aspect = absolute_bearing - ts_heading
    
    return normalize_angle_360(aspect)


def calculate_bearing_rate(
    os_position: Tuple[float, float],
    os_velocity: Tuple[float, float],
    ts_position: Tuple[float, float],
    ts_velocity: Tuple[float, float]
) -> float:
    """
    방위각 변화율 계산 (deg/s)
    일정한 경우 충돌 위험 존재 (constant bearing, decreasing range)
    
    Args:
        os_position: OS 위치 (x, y)
        os_velocity: OS 속도 벡터 (vx, vy)
        ts_position: TS 위치 (x, y)
        ts_velocity: TS 속도 벡터 (vx, vy)
    
    Returns:
        방위각 변화율 (deg/s)
        0에 가까우면 충돌 위험
    """
    # 상대 위치 벡터
    dx = ts_position[0] - os_position[0]
    dy = ts_position[1] - os_position[1]
    range_sq = dx**2 + dy**2
    
    if range_sq < 1e-6:  # 거의 같은 위치
        return 0.0
    
    # 상대 속도
    dvx = ts_velocity[0] - os_velocity[0]
    dvy = ts_velocity[1] - os_velocity[1]
    
    # 방위각 변화율 = (r × v_rel) / |r|^2
    # r × v_rel (2D cross product)
    cross_product = dx * dvy - dy * dvx
    
    # rad/s to deg/s
    bearing_rate_rad = cross_product / range_sq
    return np.degrees(bearing_rate_rad)
