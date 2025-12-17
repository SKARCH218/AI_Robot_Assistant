def move_to_home_pose():
    '''홈 자세로 이동 (하드코딩)'''
    import json
    home_angles = {
        "base": 90,
        "motor1": 90,
        "motor2": 90,
        "motor3": 90,
        "grip_rotate": 90,
        "grip": 90
    }
    set_servo_angles(json.dumps(home_angles))
    print("홈 자세로 이동 완료")
def get_servo_angles():
    '''
    Arm_Lib을 통해 현재 각도를 읽어옴
    반환 예시: {"base":90, "motor1":45, ...}
    '''
    try:
        from Arm_Lib import Arm_Device
        Arm = Arm_Device()
        # 1~6번 서보 각도 읽기
        angles = {}
        names = ['base', 'motor1', 'motor2', 'motor3', 'grip_rotate', 'grip']
        for i, name in enumerate(names):
            val = Arm.Arm_serial_servo_read(i+1)
            angles[name] = val
    # print(f"DOFBOT 현재 각도: {angles}")  # 콘솔 도배 방지, 필요시만 출력
        return angles
    except Exception as e:
        print(f"각도 읽기 실패: {e}")
        return None
import json

def set_servo_angles(angles_json):
    '''
    angles_json 예시:
    {
        "base": 90,
        "motor1": 45,
        "motor2": 30,
        "motor3": 60,
        "grip_rotate": 10,
        "grip": 5
    }
    '''
    try:
        angles = json.loads(angles_json)
        # Arm_Lib을 통한 실제 DOFBOT 제어
        try:
            from Arm_Lib import Arm_Device
            import time
            Arm = Arm_Device()
            # 속도(시간) 기본값 느리게
            move_time = angles.get('move_time', 1500)
            # JSON 키와 Arm_Lib 인덱스 매핑
            servo_values = [
                angles.get('base', 90),
                angles.get('motor1', 90),
                angles.get('motor2', 90),
                angles.get('motor3', 90),
                angles.get('grip_rotate', 90),
                angles.get('grip', 90)
            ]
            # 순차 제어 옵션
            if angles.get('sequential', False):
                for idx, val in enumerate(servo_values):
                    # 1~6번 서보에 각각 적용
                    Arm.Arm_serial_servo_write(idx+1, val, move_time)
                    time.sleep(move_time/1000.0 + 0.2)
                print(f"DOFBOT 순차 제어: {servo_values}")
            else:
                
                Arm.Arm_serial_servo_write6(*servo_values, move_time)
                print(f"DOFBOT 동시 제어: {servo_values}")
        except Exception as sdk_e:
            print(f"Arm_Lib 제어 실패: {sdk_e}")
        return True
    except Exception as e:
        print(f"제어 실패: {e}")
        return False
