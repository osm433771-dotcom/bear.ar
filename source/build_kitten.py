"""바나나 옷을 입은 오리지널 아기 고양이 캐릭터를 만들고 GLB(안드로이드/웹)와 USDZ(아이폰 Quick Look)로 내보내는 스크립트.
실행: python build_bear.py <출력폴더>   (pip install bpy==5.3.0, Python 3.13)
단위: 센티미터로 만들고 루트를 0.01배 → 결과물은 미터 단위, 원점 = 발바닥. 키 약 16cm.
"""
import sys, os, math
import bpy, bmesh

OUT = os.path.abspath(sys.argv[-1] if len(sys.argv) > 1 else '.')
os.makedirs(OUT, exist_ok=True)
FPS = 30
TAU = math.pi * 2

# ---------- 장면 초기화 ----------
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.render.fps = FPS

def material(name, hexcol, rough=0.8):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    h = hexcol.lstrip('#')
    srgb = [int(h[i:i+2], 16) / 255 for i in (0, 2, 4)]
    lin = [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in srgb]
    bsdf = m.node_tree.nodes.get('Principled BSDF')
    bsdf.inputs['Base Color'].default_value = (*lin, 1)
    bsdf.inputs['Roughness'].default_value = rough
    m.diffuse_color = (*lin, 1)
    return m

M = dict(
    suit=material('BananaSuit', '#F6D64A', 0.75),
    stem=material('BananaStem', '#6E4A2A', 0.8),
    fur=material('KittenFur', '#F3CBA0'),
    stripe=material('Stripe', '#DE9F68'),
    muzzle=material('Muzzle', '#FFF8EE'),
    paw=material('Paw', '#F6DCC0'),
    eye=material('Eye', '#2A211C', 0.25),
    shine=material('Shine', '#FFFFFF', 0.2),
    cheek=material('Cheek', '#FFB4A2', 0.9),
    nose=material('Nose', '#F2A0A4', 0.5),
    mouth=material('Mouth', '#7A4A35', 0.5),
)

def empty(name, parent=None, loc=(0, 0, 0)):
    o = bpy.data.objects.new(name, None)
    o.empty_display_size = 0.5
    scene.collection.objects.link(o)
    o.parent = parent
    o.location = loc
    return o

def sphere(name, mat, parent, loc, scl, rot=(0, 0, 0)):
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=40, v_segments=24, radius=1.0)
    bm.to_mesh(me); bm.free()
    for p in me.polygons: p.use_smooth = True
    me.materials.append(mat)
    o = bpy.data.objects.new(name, me)
    scene.collection.objects.link(o)
    o.parent = parent
    o.location, o.scale, o.rotation_euler = loc, scl, rot
    return o

def smile(name, mat, parent, loc, R=0.48, r=0.11):
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    N, n = 32, 10
    verts = []
    for i in range(N + 1):                      # 아래쪽 반원 (웃는 입)
        a = math.pi + math.pi * i / N
        ring = []
        for j in range(n):
            b = TAU * j / n
            x = (R + r * math.cos(b)) * math.cos(a)
            z = (R + r * math.cos(b)) * math.sin(a)
            y = r * math.sin(b)
            ring.append(bm.verts.new((x, y, z)))
        verts.append(ring)
    for i in range(N):
        for j in range(n):
            bm.faces.new((verts[i][j], verts[i][(j+1) % n], verts[i+1][(j+1) % n], verts[i+1][j]))
    bm.to_mesh(me); bm.free()
    for p in me.polygons: p.use_smooth = True
    me.materials.append(mat)
    o = bpy.data.objects.new(name, me)
    scene.collection.objects.link(o)
    o.parent = parent
    o.location = loc
    return o


def cylinder(name, mat, parent, loc, r1, r2, h, rot=(0, 0, 0)):
    me = bpy.data.meshes.new(name)
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=20, radius1=r1, radius2=r2, depth=h)
    bm.to_mesh(me); bm.free()
    me.materials.append(mat)
    o = bpy.data.objects.new(name, me)
    scene.collection.objects.link(o)
    o.parent = parent
    o.location, o.rotation_euler = loc, rot
    return o

# ---------- 캐릭터 (앞쪽 = -Y, 위 = +Z) ----------
root = empty('Kitten'); root.scale = (0.0085, 0.0085, 0.0085)   # 약 16cm
mover = empty('Mover', root)          # 점프/달리기 이동
squash = empty('Squash', mover)       # 몸 늘었다 줄었다 (발바닥 기준)

sphere('SuitBody', M['suit'], squash, (0, 0, 4.4), (3.5, 3.2, 3.7))

head = empty('Head', squash, (0, 0, 7.2))
# 바나나 모자: 머리를 감싸고 위로 갈수록 가늘어지며 살짝 휘어짐
sphere('SuitHood', M['suit'], head, (0, 0.2, 2.6), (4.2, 3.8, 4.2))
for i in range(16):                       # 위로 갈수록 가늘어지며 한쪽으로 살짝 휘는 바나나 끝
    u = i / 15
    rad = 3.3 * (1 - u) ** 0.9 + 0.55 * u
    sphere(f'SuitTip_{i}', M['suit'], head, (1.6 * u * u, 0.3 + 1.0 * u, 4.5 + 6.0 * u), (rad, rad * 0.95, rad))
cylinder('Stem', M['stem'], head, (1.85, 1.3, 11.15), 0.5, 0.4, 1.4, (0, 0.3, 0))
# 모자 구멍으로 보이는 아기 고양이 얼굴
sphere('Face', M['fur'], head, (0, -2.6, 2.4), (2.9, 1.6, 2.5))
for i, x in enumerate((-0.7, 0, 0.7)):
    sphere(f'Stripe_{i}', M['stripe'], head, (x, -3.72, 4.05 + (0.15 if x == 0 else 0)), (0.2, 0.22, 0.55), (0, -x * 0.35, 0))
sphere('Muzzle', M['muzzle'], head, (0, -3.85, 1.5), (1.35, 0.55, 0.9))
sphere('Nose', M['nose'], head, (0, -4.36, 1.9), (0.3, 0.2, 0.22))
smile('Mouth', M['mouth'], head, (0, -4.36, 1.5), R=0.3, r=0.08)
for s, side in ((1, 'L'), (-1, 'R')):
    eye = empty(f'Eye_{side}', head, (s * 1.15, -3.95, 2.6))
    sphere(f'EyeBall_{side}', M['eye'], eye, (0, 0, 0), (0.62, 0.3, 0.72))
    sphere(f'EyeShine_{side}', M['shine'], eye, (s * 0.15 + 0.08, -0.24, 0.25), (0.22, 0.1, 0.22))
    sphere(f'Cheek_{side}', M['cheek'], head, (s * 2.05, -3.55, 1.65), (0.55, 0.2, 0.35), (0, 0, s * 0.6))

for s, side in ((1, 'L'), (-1, 'R')):
    arm = empty(f'Arm_{side}', squash, (s * 3.1, -0.3, 6.0))
    sphere(f'ArmSuit_{side}', M['suit'], arm, (s * 0.55, 0, -1.3), (0.95, 0.95, 1.5), (0, -s * 0.35, 0))
    sphere(f'Paw_{side}', M['paw'], arm, (s * 1.05, 0, -2.75), (0.75, 0.75, 0.7))
    foot = empty(f'Foot_{side}', mover, (s * 1.5, -0.5, 0))
    sphere(f'FootPaw_{side}', M['paw'], foot, (0, 0, 0.65), (1.2, 1.5, 0.7))

ANIM = ['Mover', 'Squash', 'Head', 'Arm_L', 'Arm_R', 'Eye_L', 'Eye_R', 'Foot_L', 'Foot_R']
OBJ = {n: bpy.data.objects[n] for n in ANIM}
REST = {n: tuple(OBJ[n].location) for n in ANIM}

# ---------- 동작 정의: t(초) → 각 부위의 위치/회전/크기 ----------
def ease(p): p = min(max(p, 0), 1); return p * p * (3 - 2 * p)
def bell(p): return math.sin(math.pi * min(max(p, 0), 1))

def rest_pose():
    return {n: dict(loc=list(REST[n]), rot=[0, 0, 0], scl=[1, 1, 1]) for n in ANIM}

def breathe(P, t, dur, cycles, amp=0.025):
    b = math.sin(TAU * cycles * t / dur) * amp
    P['Squash']['scl'] = [1 + b * 0.5, 1 + b * 0.5, 1 - b]

def idle(P, t, dur=3.0):
    breathe(P, t, dur, 2)
    P['Head']['rot'][1] = math.sin(TAU * t / dur) * 0.06
    k = 1 - 0.9 * bell((t - 2.0) / 0.18)            # 눈 깜빡
    P['Eye_L']['scl'][2] = P['Eye_R']['scl'][2] = k

def wave(P, t, dur=2.6):
    breathe(P, t, dur, 1)
    p = t / dur
    up = ease(p / 0.18) * ease((1 - p) / 0.18)
    P['Arm_R']['rot'][1] = up * (2.1 + math.sin(t * 12) * 0.4)    # 오른팔 들고 흔들기
    P['Arm_R']['rot'][0] = -up * 0.6                               # 팔을 살짝 앞으로
    P['Head']['rot'][1] = up * 0.12
    P['Squash']['rot'][1] = up * 0.05

def jump(P, t, dur=1.3):
    p = t / dur
    crouch = bell(p / 0.25) if p < 0.25 else 0
    land = bell((p - 0.72) / 0.22) if 0.72 < p < 0.94 else 0
    air = bell((p - 0.2) / 0.55)
    P['Mover']['loc'][2] = air * 5.0                               # 5cm 점프
    sq = -0.14 * (crouch + land) + 0.08 * air
    P['Squash']['scl'] = [1 - sq * 0.5, 1 - sq * 0.5, 1 + sq]
    for side in ('L', 'R'):
        s = 1 if side == 'L' else -1
        P[f'Arm_{side}']['rot'][1] = -s * air * 1.6                # 팔 번쩍
        P[f'Foot_{side}']['loc'][2] += air * 0.6
    P['Eye_L']['scl'][2] = P['Eye_R']['scl'][2] = 1 - 0.75 * (crouch + land)

RUN_A, RUN_B = 9.0, 10.0   # 8자 경로: 가로 약 18cm, 세로 약 10cm
def run_path(p):
    s = p - math.sin(TAU * p) / TAU                                # 처음/끝 천천히
    th = TAU * s
    return RUN_A * math.sin(th), -RUN_B * math.sin(th) * math.cos(th)

def run_heading_table(dur, n):
    hs, prev = [], None
    for i in range(n):
        p = i / (n - 1)
        x0, y0 = run_path(max(p - 0.002, 0)); x1, y1 = run_path(min(p + 0.002, 1))
        dx, dy = x1 - x0, y1 - y0
        if abs(dx) + abs(dy) < 1e-9:
            dx, dy = run_path(0.01)
        h = math.atan2(dx, -dy)
        if prev is not None:
            while h - prev > math.pi: h -= TAU
            while h - prev < -math.pi: h += TAU
        hs.append(h); prev = h
    return hs

def run(P, t, dur=6.0, heading=None):
    p = t / dur
    x, y = run_path(p)
    w = ease(p / 0.07) * ease((1 - p) / 0.07)
    ph = TAU * 14 * t / dur                                        # 28걸음
    P['Mover']['loc'] = [x, y, abs(math.sin(ph)) * 0.9 * w]
    P['Mover']['rot'][2] = heading * w
    P['Squash']['rot'][0] = -0.18 * w                              # 앞으로 기울기
    P['Squash']['rot'][1] = math.sin(ph) * 0.06 * w
    P['Foot_L']['loc'][2] += max(0, math.sin(ph)) * 1.0 * w
    P['Foot_R']['loc'][2] += max(0, -math.sin(ph)) * 1.0 * w
    P['Foot_L']['loc'][1] += -math.sin(ph) * 0.6 * w
    P['Foot_R']['loc'][1] += math.sin(ph) * 0.6 * w
    P['Arm_L']['rot'][0] = math.sin(ph) * 0.8 * w
    P['Arm_R']['rot'][0] = -math.sin(ph) * 0.8 * w

CLIPS = {'Idle': 3.0, 'Wave': 2.6, 'Jump': 1.3, 'Run': 6.0}

def pose_at(name, t):
    P = rest_pose()
    if name == 'Idle': idle(P, t)
    elif name == 'Wave': wave(P, t)
    elif name == 'Jump': jump(P, t)
    elif name == 'Run':
        n = round(CLIPS['Run'] * FPS) + 1
        hs = RUN_HEAD
        i = min(round(t / CLIPS['Run'] * (n - 1)), n - 1)
        run(P, t, heading=hs[i])
    return P

RUN_HEAD = run_heading_table(CLIPS['Run'], round(CLIPS['Run'] * FPS) + 1)

def key_pose(P, frame):
    for n in ANIM:
        o = OBJ[n]
        o.location, o.rotation_euler, o.scale = P[n]['loc'], P[n]['rot'], P[n]['scl']
        o.keyframe_insert('location', frame=frame)
        o.keyframe_insert('rotation_euler', frame=frame)
        o.keyframe_insert('scale', frame=frame)

def clear_actions():
    for n in ANIM:
        ad = OBJ[n].animation_data_create()
        ad.action = None

def reset_rest():
    P = rest_pose()
    for n in ANIM:
        OBJ[n].location, OBJ[n].rotation_euler, OBJ[n].scale = P[n]['loc'], P[n]['rot'], P[n]['scl']

def set_linear():
    for n in ANIM:
        act = OBJ[n].animation_data.action
        for fc in getattr(act, 'fcurves', []) or []:
            for kp in fc.keyframe_points: kp.interpolation = 'LINEAR'

# ---------- 1) GLB: 동작마다 따로 (Idle/Wave/Jump/Run) ----------
for name, dur in CLIPS.items():
    clear_actions()
    n = round(dur * FPS)
    for f in range(n + 1):
        key_pose(pose_at(name, f / FPS), f)
    for o_name in ANIM:
        ad = OBJ[o_name].animation_data
        act = ad.action
        act.name = f'{name}_{o_name}'
        track = ad.nla_tracks.new(); track.name = name
        strip = track.strips.new(name, 0, act)
        ad.action = None
clear_actions(); reset_rest()
scene.frame_start, scene.frame_end = 0, 1

bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT, 'kitten.blend'))

bpy.ops.export_scene.gltf(
    filepath=os.path.join(OUT, 'kitten.glb'), export_format='GLB',
    export_animations=True, export_animation_mode='NLA_TRACKS',
    export_force_sampling=True, export_frame_step=1, export_yup=True,
    export_def_bones=False, export_optimize_animation_size=False)

# ---------- 2) USDZ: 아이폰은 버튼을 쓸 수 없어서 한 줄로 이어진 반복 동작 ----------
for n in ANIM:
    ad = OBJ[n].animation_data
    for tr in list(ad.nla_tracks): ad.nla_tracks.remove(tr)
SEQ = [('Idle', 1.0), ('Wave', None), ('Idle', 1.0), ('Jump', None), ('Jump', None),
       ('Idle', 1.0), ('Run', None), ('Idle', 1.5)]
clear_actions()
frame = 0
for name, length in SEQ:
    dur = length if length else CLIPS[name]
    n = round(dur * FPS)
    for f in range(n):
        key_pose(pose_at(name, f / FPS), frame + f)
    frame += n
key_pose(pose_at('Idle', 0), frame)
scene.frame_start, scene.frame_end = 0, frame
print('USDZ sequence frames:', frame, 'seconds:', frame / FPS)

bpy.ops.wm.usd_export(
    filepath=os.path.join(OUT, 'kitten.usdz'),
    export_animation=True, export_materials=True, generate_preview_surface=True,
    selected_objects_only=False,
    convert_orientation=True, export_global_forward_selection='NEGATIVE_Z',
    export_global_up_selection='Y')
print('done', OUT)
