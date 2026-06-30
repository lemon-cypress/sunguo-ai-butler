import * as THREE from "three";
import { GLTFLoader } from "three/examples/jsm/loaders/GLTFLoader.js";
import { VRMLoaderPlugin, VRMUtils } from "../node_modules/@pixiv/three-vrm/lib/three-vrm.module.js";

const canvas = document.querySelector("#avatar3dCanvas");
let renderer;
let scene;
let camera;
let avatar;
let fallbackAvatar;
let currentVrm = null;
let activeModelUrl = "";
let route = [];
let routeIndex = 0;
let routeTimer = 0;
let movementSpeed = 0;
let previousAvatarPosition = new THREE.Vector3();
let voiceSpeaking = false;
let motionPulse = 0;
let motionClips = createDefaultMotionClips();
const motionState = {
  expression: "warm",
  gesture: "small_nod",
  mouth: "closed",
  lip_sync: "rest",
  speaking: false,
  section: "idle"
};
const clock = new THREE.Clock();
const markers = new Map();
const modelWarmCache = new Map();

if (canvas) {
  initScene();
  loadMotionClips();
  window.addEventListener("sunguo:avatar3d", (event) => loadAvatarPackage(event.detail || {}));
  window.addEventListener("sunguo:avatarMotion", (event) => setMotionState(event.detail || {}));
  window.addEventListener("sunguo:voiceState", (event) => setAvatarVoiceState(event.detail || {}));
  window.addEventListener("sunguo:motionConfigPatch", (event) => applyMotionConfigPatch(event.detail || {}));
  window.addEventListener("resize", resizeRenderer);
  if (window.__sunguoAvatar3d) loadAvatarPackage(window.__sunguoAvatar3d);
  animate();
}


async function loadMotionClips() {
  try {
    const response = await fetch("./avatar_motion_clips.json", { cache: "no-store" });
    if (!response.ok) throw new Error(`Cannot load motion clips: ${response.status}`);
    motionClips = mergeMotionClips(createDefaultMotionClips(), await response.json());
  } catch (error) {
    console.warn("Using built-in avatar motion clips", error);
  }
}

function createDefaultMotionClips() {
  return {
    defaults: {
      walkSpeedThreshold: 0.018,
      walkCycleSpeed: 8.4,
      breathSpeed: 1.55,
      blinkCycleSeconds: 5.8
    },
    walk: {
      spineBase: 0.04,
      chestBase: 0.03,
      bodySwing: 0.018,
      armSwing: 0.12,
      legSwing: 0.28,
      kneeLift: 0.34,
      footLift: 0.18,
      bounce: 0.035
    }
  };
}

function mergeMotionClips(base, custom = {}) {
  return {
    ...base,
    ...custom,
    defaults: { ...(base.defaults || {}), ...(custom.defaults || {}) },
    clips: mergeClipMap(base.clips || {}, custom.clips || {}),
    walk: { ...(base.walk || {}), ...(custom.walk || {}) }
  };
}

function mergeClipMap(baseClips, customClips) {
  const merged = { ...baseClips };
  Object.entries(customClips || {}).forEach(([name, clip]) => {
    merged[name] = { ...(baseClips[name] || {}), ...(clip || {}) };
  });
  return merged;
}

function applyMotionConfigPatch(patch) {
  motionClips = mergeMotionClips(motionClips, patch || {});
}
function initScene() {
  renderer = new THREE.WebGLRenderer({ canvas, antialias: true, alpha: true });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
  renderer.setClearColor(0xf7faf9, 1);

  scene = new THREE.Scene();
  scene.fog = new THREE.Fog(0xf7faf9, 5, 12);

  camera = new THREE.PerspectiveCamera(42, 1, 0.1, 50);
  camera.position.set(0, 1.55, 3.15);
  camera.lookAt(0, 1.05, 0);

  const hemi = new THREE.HemisphereLight(0xffffff, 0xd7e4df, 2.3);
  scene.add(hemi);

  const key = new THREE.DirectionalLight(0xffffff, 2.1);
  key.position.set(3, 5, 4);
  scene.add(key);

  const fill = new THREE.DirectionalLight(0xbddbd2, 1.1);
  fill.position.set(-3, 2, -2);
  scene.add(fill);

  buildRoom();
  avatar = new THREE.Group();
  avatar.name = "SunguoAvatarRoot";
  fallbackAvatar = buildFallbackAvatar();
  avatar.add(fallbackAvatar);
  scene.add(avatar);
  resizeRenderer();
}

function buildRoom() {
  const floorMaterial = new THREE.MeshStandardMaterial({ color: 0xe8f0ed, roughness: 0.82, metalness: 0.03 });
  const floor = new THREE.Mesh(new THREE.PlaneGeometry(6.4, 5.2), floorMaterial);
  floor.rotation.x = -Math.PI / 2;
  floor.position.y = -0.01;
  scene.add(floor);

  const grid = new THREE.GridHelper(6.4, 8, 0x9db8b0, 0xd5e1de);
  grid.position.y = 0.005;
  scene.add(grid);

  const backWall = new THREE.Mesh(
    new THREE.BoxGeometry(6.4, 2.8, 0.08),
    new THREE.MeshStandardMaterial({ color: 0xf4f7f6, roughness: 0.9 })
  );
  backWall.position.set(0, 1.4, -2.05);
  scene.add(backWall);

  const desk = new THREE.Mesh(
    new THREE.BoxGeometry(1.4, 0.72, 0.52),
    new THREE.MeshStandardMaterial({ color: 0x6c8f86, roughness: 0.7 })
  );
  desk.position.set(1.35, 0.36, -0.85);
  scene.add(desk);

  const windowPane = new THREE.Mesh(
    new THREE.BoxGeometry(1.2, 1.0, 0.04),
    new THREE.MeshStandardMaterial({ color: 0xdcebf2, roughness: 0.4, transparent: true, opacity: 0.82 })
  );
  windowPane.position.set(-1.45, 1.55, -2.0);
  scene.add(windowPane);
}

function buildFallbackAvatar() {
  const group = new THREE.Group();
  group.name = "SunguoLowPolyFallback";

  const skin = new THREE.MeshStandardMaterial({ color: 0xf0c3a8, roughness: 0.55 });
  const hair = new THREE.MeshStandardMaterial({ color: 0x2f2525, roughness: 0.7 });
  const cloth = new THREE.MeshStandardMaterial({ color: 0x4f9a89, roughness: 0.76 });
  const blouse = new THREE.MeshStandardMaterial({ color: 0xf4f7f4, roughness: 0.65 });
  const dark = new THREE.MeshStandardMaterial({ color: 0x21323a, roughness: 0.7 });

  const body = new THREE.Mesh(new THREE.CapsuleGeometry(0.34, 0.78, 8, 16), cloth);
  body.position.y = 1.0;
  group.add(body);

  const collar = new THREE.Mesh(new THREE.ConeGeometry(0.28, 0.24, 4), blouse);
  collar.position.y = 1.43;
  collar.rotation.y = Math.PI / 4;
  group.add(collar);

  const neck = new THREE.Mesh(new THREE.CylinderGeometry(0.1, 0.12, 0.18, 16), skin);
  neck.position.y = 1.5;
  group.add(neck);

  const head = new THREE.Mesh(new THREE.SphereGeometry(0.28, 32, 24), skin);
  head.scale.set(0.9, 1.06, 0.86);
  head.position.y = 1.82;
  group.add(head);

  const hairBack = new THREE.Mesh(new THREE.SphereGeometry(0.32, 32, 18), hair);
  hairBack.scale.set(0.95, 1.2, 0.8);
  hairBack.position.set(0, 1.8, -0.06);
  group.add(hairBack);

  const bang = new THREE.Mesh(new THREE.SphereGeometry(0.22, 24, 12), hair);
  bang.scale.set(1.2, 0.45, 0.7);
  bang.position.set(0, 2.0, 0.17);
  group.add(bang);

  const leftArm = makeLimb(0.08, 0.46, skin);
  leftArm.position.set(-0.42, 1.16, 0);
  leftArm.rotation.z = -0.22;
  group.add(leftArm);

  const rightArm = makeLimb(0.08, 0.46, skin);
  rightArm.position.set(0.42, 1.16, 0);
  rightArm.rotation.z = 0.22;
  group.add(rightArm);

  const leftLeg = makeLimb(0.09, 0.56, dark);
  leftLeg.position.set(-0.14, 0.34, 0);
  group.add(leftLeg);

  const rightLeg = makeLimb(0.09, 0.56, dark);
  rightLeg.position.set(0.14, 0.34, 0);
  group.add(rightLeg);

  const base = new THREE.Mesh(
    new THREE.CylinderGeometry(0.48, 0.48, 0.035, 48),
    new THREE.MeshStandardMaterial({ color: 0xcfe1dc, roughness: 0.8 })
  );
  base.position.y = 0.02;
  group.add(base);

  return group;
}

function makeLimb(radius, length, material) {
  return new THREE.Mesh(new THREE.CapsuleGeometry(radius, length, 8, 12), material);
}

function loadAvatarPackage(payload) {
  clearMarkers();
  route = Array.isArray(payload.space_storyboard) ? payload.space_storyboard : [];
  const points = Array.isArray(payload.navigation_points) ? payload.navigation_points : [];
  points.forEach((point) => addMarker(point));
  tryLoadAvatarModel(payload.avatar_profile || {});
  if (route.length && avatar) {
    moveAvatarTo(route[0].coordinates || [0, 0, 0], true);
    previousAvatarPosition.copy(avatar.position);
    routeIndex = 0;
    routeTimer = 0;
  }
}

function tryLoadAvatarModel(profile) {
  const url = resolveModelUrl(profile.model_assets?.primary_vrm);
  if (!url) {
    setModelStatus("fallback");
    return;
  }
  if (activeModelUrl === url && currentVrm) return;
  activeModelUrl = url;
  setModelStatus("loading");
  warmModelCache(url).catch(() => {});
  loadVrmModel(url);
}

function warmModelCache(url) {
  if (!url) return Promise.resolve();
  if (modelWarmCache.has(url)) return modelWarmCache.get(url);
  const task = fetch(url, { cache: "force-cache" })
    .then((response) => {
      if (!response.ok) throw new Error(`model not found: ${url}`);
      return response.blob();
    })
    .catch((error) => {
      modelWarmCache.delete(url);
      throw error;
    });
  modelWarmCache.set(url, task);
  return task;
}

function resolveModelUrl(path) {
  if (!path) return "./assets/avatar/sunguo.vrm";
  if (/^https?:\/\//.test(path)) return path;
  return path.replace(/^frontend\//, "./");
}

function loadVrmModel(url) {
  const loader = new GLTFLoader();
  loader.register((parser) => new VRMLoaderPlugin(parser));
  loader.load(
    url,
    (gltf) => {
      const vrm = gltf.userData.vrm;
      if (!vrm) {
        setModelStatus("fallback");
        return;
      }
      VRMUtils.removeUnnecessaryVertices(vrm.scene);
      VRMUtils.combineSkeletons(vrm.scene);
      currentVrm = vrm;
      applyNaturalIdlePose(vrm);
      replaceAvatarVisual(vrm.scene, "vrm");
      setModelStatus("vrm");
    },
    (event) => {
      const total = Number(event.total) || 0;
      const loaded = Number(event.loaded) || 0;
      const percent = total > 0 ? Math.max(1, Math.min(100, Math.round((loaded / total) * 100))) : null;
      setModelStatus("loading", percent);
    },
    () => setModelStatus("fallback")
  );
}

function replaceAvatarVisual(model, mode) {
  if (!avatar) return;
  while (avatar.children.length) avatar.remove(avatar.children[0]);
  model.name = "SunguoVrmModel";
  model.position.set(0, 0, 0);
  model.rotation.y = 0;
  model.userData.baseScale = mode === "vrm" ? 1.45 : 1.0;
  model.scale.setScalar(model.userData.baseScale * 0.94);
  avatar.userData.entryMix = 0;
  avatar.add(model);
}

function applyNaturalIdlePose(vrm) {
  const humanoid = vrm?.humanoid;
  if (!humanoid?.getNormalizedBoneNode) return;
  const setRot = (name, x, y, z) => {
    const bone = humanoid.getNormalizedBoneNode(name);
    if (bone) bone.rotation.set(x, y, z);
  };
  setRot("leftUpperArm", 0.08, 0.02, -0.72);
  setRot("rightUpperArm", 0.08, -0.02, 0.72);
  setRot("leftLowerArm", 0.04, 0.0, -0.12);
  setRot("rightLowerArm", 0.04, 0.0, 0.12);
  setRot("leftHand", 0.0, 0.0, -0.04);
  setRot("rightHand", 0.0, 0.0, 0.04);
  setRot("leftUpperLeg", 0.02, 0.0, 0.03);
  setRot("rightUpperLeg", 0.02, 0.0, -0.03);
  setRot("leftLowerLeg", 0.02, 0.0, 0.0);
  setRot("rightLowerLeg", 0.02, 0.0, 0.0);
  setRot("leftFoot", -0.02, 0.0, 0.0);
  setRot("rightFoot", -0.02, 0.0, 0.0);
}

function setMotionState(detail) {
  motionState.expression = detail.expression || motionState.expression || "warm";
  motionState.gesture = detail.gesture || motionState.gesture || "small_nod";
  motionState.mouth = detail.mouth || motionState.mouth || "closed";
  motionState.lip_sync = detail.lip_sync || motionState.lip_sync || "rest";
  motionState.speaking = Boolean(detail.speaking || detail.mouth === "open" || detail.lip_sync === "enabled");
  motionState.section = detail.section || motionState.section || "idle";
  motionPulse = clock.elapsedTime;
  publishAvatarPresence(route[routeIndex] || {}, { mode: currentVrm ? "vrm" : "loading" });
}

function setAvatarVoiceState(detail) {
  voiceSpeaking = Boolean(detail.speaking);
  publishAvatarPresence(route[routeIndex] || {}, { mode: currentVrm ? "vrm" : "loading" });
}

function updateAvatarRuntime(elapsed) {
  if (!currentVrm) return;
  updateVrmExpressions(elapsed);
  updateVrmPose(elapsed);
}
function updateVrmExpressions(elapsed) {
  const blink = getBlinkValue(elapsed);
  const talking = voiceSpeaking || motionState.speaking;
  const mouth = talking ? 0.18 + Math.abs(Math.sin(elapsed * 13.5)) * 0.62 : 0;
  const smile = motionState.expression === "smile" || motionState.expression === "warm" ? 0.18 : 0.06;
  setExpressionValue(["blink", "Blink"], blink);
  setExpressionValue(["happy", "relaxed", "smile"], smile);
  setExpressionValue(["aa", "A", "a"], mouth);
  setExpressionValue(["ih", "I", "i"], talking ? mouth * 0.22 : 0);
  setExpressionValue(["ou", "O", "o"], talking ? mouth * 0.12 : 0);
  currentVrm.expressionManager?.update?.();
}

function getBlinkValue(elapsed) {
  const cycle = elapsed % 5.8;
  if (cycle < 0.11) return cycle / 0.11;
  if (cycle < 0.22) return 1 - (cycle - 0.11) / 0.11;
  const smallBlink = (elapsed + 2.7) % 8.9;
  if (smallBlink < 0.08) return smallBlink / 0.08;
  if (smallBlink < 0.16) return 1 - (smallBlink - 0.08) / 0.08;
  return 0;
}

function setExpressionValue(names, value) {
  const manager = currentVrm?.expressionManager;
  if (!manager?.setValue) return;
  names.forEach((name) => {
    try {
      manager.setValue(name, value);
    } catch (error) {
      // Some VRM files do not expose every preset expression.
    }
  });
}

function updateVrmPose(elapsed) {
  const breath = Math.sin(elapsed * (motionClips.defaults?.breathSpeed || 1.55)) * 0.035;
  const nod = Math.sin(elapsed * 0.9) * 0.035;
  const talking = voiceSpeaking || motionState.speaking;
  const walking = movementSpeed > (motionClips.defaults?.walkSpeedThreshold || 0.018);
  const gesture = normalizeGesture(motionState.gesture || "small_nod");
  const pose = buildGesturePose(gesture, elapsed, walking);

  setBoneRotationSmooth("spine", 0.02 + breath + (pose.spine?.[0] || 0), pose.spine?.[1] || 0, pose.spine?.[2] || 0, 0.08);
  setBoneRotationSmooth("chest", 0.025 + breath + (pose.chest?.[0] || 0), pose.chest?.[1] || 0, pose.chest?.[2] || 0, 0.08);
  setBoneRotationSmooth("neck", 0.02 + nod * 0.35, Math.sin(elapsed * 0.7) * 0.025, 0, 0.1);
  setBoneRotationSmooth("head", (talking ? Math.sin(elapsed * 5.4) * 0.018 : 0) + nod * 0.45 + (pose.head?.[0] || 0), Math.sin(elapsed * 0.55) * 0.035 + (pose.head?.[1] || 0), pose.head?.[2] || 0, 0.1);

  applyPoseBone("leftUpperArm", pose.leftUpperArm || [0.08, 0.02, -0.72], 0.13);
  applyPoseBone("rightUpperArm", pose.rightUpperArm || [0.08, -0.02, 0.72], 0.13);
  applyPoseBone("leftLowerArm", pose.leftLowerArm || [0.04, 0, -0.12], 0.13);
  applyPoseBone("rightLowerArm", pose.rightLowerArm || [0.04, 0, 0.12], 0.13);
  applyPoseBone("leftHand", pose.leftHand || [0, 0, -0.04], 0.16);
  applyPoseBone("rightHand", pose.rightHand || [0, 0, 0.04], 0.16);
  applyPoseBone("leftUpperLeg", pose.leftUpperLeg || [0.02, 0, 0.03], 0.18);
  applyPoseBone("rightUpperLeg", pose.rightUpperLeg || [0.02, 0, -0.03], 0.18);
  applyPoseBone("leftLowerLeg", pose.leftLowerLeg || [0.02, 0, 0], 0.18);
  applyPoseBone("rightLowerLeg", pose.rightLowerLeg || [0.02, 0, 0], 0.18);
  applyPoseBone("leftFoot", pose.leftFoot || [-0.02, 0, 0], 0.2);
  applyPoseBone("rightFoot", pose.rightFoot || [-0.02, 0, 0], 0.2);
}

function normalizeGesture(gesture) {
  if (gesture.includes("wave")) return "wave";
  if (gesture.includes("present_left") || gesture.includes("open_palm")) return "present_left";
  if (gesture.includes("point")) return "point_screen";
  if (gesture.includes("checklist")) return "checklist";
  if (gesture.includes("nod")) return "small_nod";
  return "idle";
}

function buildGesturePose(gesture, elapsed, walking = false) {
  const pulse = Math.max(0, 1 - (elapsed - motionPulse) / 1.1);
  const settle = 1 - pulse;
  const wave = Math.sin(elapsed * 7.4);
  const soft = Math.sin(elapsed * 1.8) * 0.035;
  const walk = buildWalkPose(elapsed, walking);
  const clips = motionClips.clips || {};
  const base = clips[gesture] || clips.idle || {};
  const dynamic = buildGestureDynamics(gesture, base, { elapsed, pulse, settle, wave, soft });
  return mergePose(mergePose(base, dynamic), walk);
}

function buildGestureDynamics(gesture, base, timing) {
  const { elapsed, pulse, settle, wave, soft } = timing;
  if (gesture === "small_nod") {
    return { head: [Math.sin(elapsed * 2.4) * (base.headNod || 0.035) * Math.max(pulse, 0.35), 0, 0] };
  }
  if (gesture === "wave") {
    return {
      rightUpperArm: addRotation(base.rightUpperArm, [0, 0, wave * 0.08]),
      rightLowerArm: addRotation(base.rightLowerArm, [0, 0, wave * (base.waveAmplitude || 0.28)]),
      rightHand: addRotation(base.rightHand, [0, 0, wave * 0.25])
    };
  }
  if (gesture === "present_left") {
    return { leftUpperArm: addRotation(base.leftUpperArm, [0, 0, soft]) };
  }
  if (gesture === "point_screen") {
    return { rightUpperArm: addRotation(base.rightUpperArm, [0, 0, soft]) };
  }
  if (gesture === "checklist") {
    return {
      head: [Math.sin(elapsed * 2.2) * (base.headNod || 0.025) * Math.max(settle, 0.45), 0.02, 0],
      rightUpperArm: addRotation(base.rightUpperArm, [0, 0, soft])
    };
  }
  return { chest: addRotation(base.chest, [soft, 0, 0]) };
}

function addRotation(base = [0, 0, 0], delta = [0, 0, 0]) {
  return [
    (base[0] || 0) + (delta[0] || 0),
    (base[1] || 0) + (delta[1] || 0),
    (base[2] || 0) + (delta[2] || 0)
  ];
}

function buildWalkPose(elapsed, walking) {
  if (!walking) {
    return {
      leftUpperLeg: [0.02, 0, 0.03],
      rightUpperLeg: [0.02, 0, -0.03],
      leftLowerLeg: [0.02, 0, 0],
      rightLowerLeg: [0.02, 0, 0],
      leftFoot: [-0.02, 0, 0],
      rightFoot: [-0.02, 0, 0]
    };
  }
  const walkConfig = motionClips.walk || {};
  const phase = elapsed * (motionClips.defaults?.walkCycleSpeed || 8.4);
  const stride = Math.sin(phase);
  const counter = Math.sin(phase + Math.PI);
  const liftLeft = Math.max(0, stride);
  const liftRight = Math.max(0, counter);
  return {
    spine: [(walkConfig.spineBase || 0.04) + Math.abs(stride) * 0.012, 0, 0],
    chest: [(walkConfig.chestBase || 0.03) + Math.abs(stride) * 0.012, 0, Math.sin(phase) * (walkConfig.bodySwing || 0.018)],
    leftUpperArm: [0.08 + counter * (walkConfig.armSwing || 0.12), 0.02, -0.68],
    rightUpperArm: [0.08 + stride * (walkConfig.armSwing || 0.12), -0.02, 0.68],
    leftLowerArm: [0.04, 0, -0.1 + stride * 0.05],
    rightLowerArm: [0.04, 0, 0.1 + counter * 0.05],
    leftUpperLeg: [0.08 + stride * (walkConfig.legSwing || 0.28), 0, 0.025],
    rightUpperLeg: [0.08 + counter * (walkConfig.legSwing || 0.28), 0, -0.025],
    leftLowerLeg: [0.06 + liftRight * (walkConfig.kneeLift || 0.34), 0, 0],
    rightLowerLeg: [0.06 + liftLeft * (walkConfig.kneeLift || 0.34), 0, 0],
    leftFoot: [-0.05 + liftLeft * (walkConfig.footLift || 0.18), 0, 0],
    rightFoot: [-0.05 + liftRight * (walkConfig.footLift || 0.18), 0, 0]
  };
}

function mergePose(base, overlay) {
  return { ...base, ...overlay };
}

function applyPoseBone(name, rotation, smoothing) {
  setBoneRotationSmooth(name, rotation[0] || 0, rotation[1] || 0, rotation[2] || 0, smoothing);
}

function setBoneRotationSmooth(name, x, y, z, smoothing = 0.12) {
  const bone = currentVrm?.humanoid?.getNormalizedBoneNode?.(name);
  if (!bone) return;
  bone.rotation.x = THREE.MathUtils.lerp(bone.rotation.x, x, smoothing);
  bone.rotation.y = THREE.MathUtils.lerp(bone.rotation.y, y, smoothing);
  bone.rotation.z = THREE.MathUtils.lerp(bone.rotation.z, z, smoothing);
}

function setModelStatus(mode, percent = null) {
  const status = document.querySelector("#avatar3dStatus");
  const overlay = document.querySelector("#avatar3dLoading");
  const title = document.querySelector("#avatar3dLoadingTitle");
  const meta = document.querySelector("#avatar3dLoadingMeta");

  if (mode === "loading") {
    if (status) status.textContent = percent ? `3D 模型加载中 ${percent}%` : "3D 模型加载中";
    if (title) title.textContent = "松果正在入场";
    if (meta) meta.textContent = percent ? `正在加载 3D 模型 ${percent}% ，首次打开会慢一点。` : "首次打开会加载 3D 模型，请稍等几秒。";
    overlay?.classList.remove("is-hidden");
    return;
  }

  if (mode === "vrm") {
    if (status) status.textContent = "3D 数字人已就位";
    if (title) title.textContent = "松果已到位";
    if (meta) meta.textContent = "3D 模型已加载完成。";
    overlay?.classList.add("is-hidden");
    return;
  }

  if (mode === "placeholder") {
    if (status) status.textContent = "正在等待 3D 模型";
    if (title) title.textContent = "松果还在准备";
    if (meta) meta.textContent = "模型文件正在同步，当前先显示加载状态。";
    overlay?.classList.remove("is-hidden");
    return;
  }

  if (mode === "fallback") {
    if (status) status.textContent = "占位形象展示中";
    if (title) title.textContent = "暂时使用占位形象";
    if (meta) meta.textContent = "3D 模型没有及时加载成功，当前先展示占位角色。";
    overlay?.classList.add("is-hidden");
  }
}

function publishAvatarPresence(step = {}, extra = {}) {
  window.dispatchEvent(new CustomEvent("sunguo:avatarPresence", {
    detail: {
      location: step.location || "briefing_spot",
      action: step.action || "idle_greeting",
      camera: step.camera || "medium",
      section: motionState.section || step.section || "idle",
      mood: motionState.expression || "warm",
      speaking: voiceSpeaking || motionState.speaking,
      mode: extra.mode || (currentVrm ? "vrm" : "loading")
    }
  }));
}
function addMarker(point) {
  const location = point.location || [0, 0, 0];
  const marker = new THREE.Group();
  marker.name = point.id || "point";

  const stem = new THREE.Mesh(
    new THREE.CylinderGeometry(0.015, 0.015, 0.18, 12),
    new THREE.MeshStandardMaterial({ color: 0x2e7d67, roughness: 0.6 })
  );
  stem.position.y = 0.1;
  marker.add(stem);

  const dot = new THREE.Mesh(
    new THREE.SphereGeometry(0.07, 20, 12),
    new THREE.MeshStandardMaterial({ color: 0xf0c45f, roughness: 0.45 })
  );
  dot.position.y = 0.22;
  marker.add(dot);

  marker.position.set(Number(location[0]) || 0, 0, Number(location[2]) || 0);
  scene.add(marker);
  markers.set(marker.name, marker);
}

function clearMarkers() {
  markers.forEach((marker) => scene.remove(marker));
  markers.clear();
}

function moveAvatarTo(coords, immediate = false) {
  if (!avatar) return;
  const target = new THREE.Vector3(Number(coords[0]) || 0, 0, Number(coords[2]) || 0);
  avatar.userData.target = target;
  if (immediate) avatar.position.copy(target);
}

function animate() {
  requestAnimationFrame(animate);
  if (!renderer || !scene || !camera) return;

  const delta = clock.getDelta();
  const elapsed = clock.elapsedTime;
  routeTimer += delta;

  if (route.length && routeTimer > 3.2) {
    routeTimer = 0;
    publishAvatarPresence(route[0], { mode: currentVrm ? "vrm" : "loading" });
    routeIndex = (routeIndex + 1) % route.length;
    moveAvatarTo(route[routeIndex].coordinates || [0, 0, 0]);
    publishAvatarPresence(route[routeIndex], { mode: currentVrm ? "vrm" : "loading" });
  }

  if (avatar) {
    const activeVisual = avatar.children[0];
    if (activeVisual) {
      const nextEntry = Math.min(1, Number(avatar.userData.entryMix ?? 1) + delta * 1.35);
      avatar.userData.entryMix = nextEntry;
      const eased = 1 - Math.pow(1 - nextEntry, 3);
      const baseScale = Number(activeVisual.userData.baseScale || 1);
      activeVisual.scale.setScalar(baseScale * (0.94 + eased * 0.06));
      activeVisual.position.y = (1 - eased) * 0.08;
    }

    const target = avatar.userData.target || avatar.position;
    const before = avatar.position.clone();
    avatar.position.lerp(target, Math.min(delta * 1.4, 1));
    movementSpeed = THREE.MathUtils.lerp(movementSpeed, avatar.position.distanceTo(before) / Math.max(delta, 0.001), 0.25);
    const travel = target.clone().sub(avatar.position);
    const facing = travel.lengthSq() > 0.0025 ? Math.atan2(travel.x, travel.z) : Math.sin(elapsed * 0.7) * 0.08;
    avatar.rotation.y = THREE.MathUtils.lerp(avatar.rotation.y, facing, 0.08);
    const walkBounce = movementSpeed > (motionClips.defaults?.walkSpeedThreshold || 0.018) ? Math.abs(Math.sin(elapsed * (motionClips.defaults?.walkCycleSpeed || 8.4))) * (motionClips.walk?.bounce || 0.035) : 0;
    avatar.position.y = Math.sin(elapsed * 2.2) * 0.012 + walkBounce;
    previousAvatarPosition.copy(avatar.position);
  }

  updateAvatarRuntime(elapsed);
  if (currentVrm) currentVrm.update(delta);

  markers.forEach((marker, index) => {
    marker.children[1].position.y = 0.22 + Math.sin(elapsed * 2 + index) * 0.018;
  });

  const focusX = avatar ? avatar.position.x : 0;
  const focusZ = avatar ? avatar.position.z : 0;
  camera.position.set(focusX * 0.72 + Math.sin(elapsed * 0.13) * 0.12, 1.55, focusZ + 3.15);
  camera.lookAt(focusX, 1.05, focusZ - 0.05);
  renderer.render(scene, camera);
}

function resizeRenderer() {
  if (!renderer || !camera || !canvas) return;
  const rect = canvas.parentElement.getBoundingClientRect();
  const width = Math.max(320, Math.floor(rect.width));
  const height = Math.max(320, Math.floor(rect.height));
  renderer.setSize(width, height, false);
  camera.aspect = width / height;
  camera.updateProjectionMatrix();
}













