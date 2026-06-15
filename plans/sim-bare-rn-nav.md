# Plan: React Native Bare Workflow — react-navigation v7 Setup

| Field | Value |
|---|---|
| **Slug** | `sim-bare-rn-nav` |
| **Created** | 2026-06-27 |
| **Class** | M (multi-platform, multi-file, external deps) |
| **React Navigation** | v7 (stable) |
| **React Native target** | ≥ 0.76 (v7 minimum); ≥ 0.82 recommended (Fabric/New Arch) |
| **Intent** | Feature — navigation infrastructure setup |
| **Adversarial reviews** | 0 (plan-only, no code surface) |
| **Budget** | Estimated ~12K tokens |

## Context Anchor

| 필드 | 내용 |
|---|---|
| **WHY** | React Native bare-workflow 앱에서 화면 간 네비게이션, 딥링크, 타입 안전성을 제공하는 기반 인프라 구축 |
| **WHO** | 모바일 앱 개발자, 최종 사용자 (iOS/Android 네이티브 앱 사용자) |
| **WHAT** | `@react-navigation/native` v7 + `native-stack` + `bottom-tabs` 설치, iOS/Android 네이티브 링킹 설정, TypeScript 정적 타입 구성, 딥링크 설정, `src/navigation/` 구조 확립 |
| **RISK** | 네이티브 링킹 실패 시 앱 빌드 불가. react-native-screens 버전 불일치 시 런타임 크래시. 영향 범위: 앱 전체 (네비게이션은 모든 화면의 진입점) |
| **SUCCESS** | iOS/Android 양 플랫폼에서 `npx react-native run-ios` / `run-android` 빌드 성공, Stack + Tab 네비게이션 전환 정상 동작, TypeScript 컴파일 오류 0, 딥링크 `myapp://` 스킴 정상 처리 |
| **SCOPE** | 포함: `@react-navigation/native`, `native-stack`, `bottom-tabs` 설치, iOS Podfile/pod-install, Android MainActivity + AndroidManifest, TypeScript 정적 타입, 딥링크 설정, `src/navigation/` 디렉토리 구조. 제외: Expo workflow, drawer navigator, 인증 가드, 실제 화면 구현 |

## Summary

React Navigation v7 (안정 버전)을 React Native bare workflow에 설치하고 iOS/Android 네이티브 링킹을 구성한다. Static Configuration API를 사용하여 타입 안전한 네비게이터를 정의하고, 딥링크를 위한 URL 스킴을 등록한다. `react-native-screens`와 `react-native-safe-area-context` 피어 의존성을 포함하며, Android에서는 `RNScreensFragmentFactory` 설정이 필요하다. v7의 `createStaticNavigation` + `StaticScreenProps` 패턴으로 TypeScript 타입 안전성을 확보한다.

## Architecture Options

### Option A — Minimal (최소 변경, 동적 API)
- **접근법**: v7 dynamic API (`<NavigationContainer>` + JSX 기반 `<Stack.Navigator>`) 사용. 기존 v6 패턴 유지.
- **장점**: v6에서 마이그레이션 최소화, 익숙한 패턴
- **단점**: TypeScript 타입 추론 약함, 수동 `RootStackParamList` 유지 필요, v7 권장 패턴 아님
- **예상 파일 수**: 3-4개

### Option B — Clean (정적 API + 완전 타입 안전)
- **접근법**: v7 Static Configuration API (`createNativeStackNavigator({ screens: {...} })`), `StaticScreenProps`, `createStaticNavigation`, module augmentation
- **장점**: 완전한 TypeScript 타입 추론, v7 공식 권장, 미래 지향적
- **단점**: 학습 곡선, v6 코드와 호환 안 됨
- **예상 파일 수**: 5-7개

### Option C — Pragmatic (권장)
- **접근법**: Static API 기반으로 Root Stack + Bottom Tabs 구성, `src/navigation/`에 `RootNavigator.tsx`, `linking.ts`, `types.ts` 분리. 딥링크는 `enabled: 'auto'` 모드로 최소 설정.
- **장점**: Option B의 타입 안전성 + 실제 프로젝트에 바로 적용 가능한 구조
- **적합**: 신규 bare workflow 프로젝트
- **예상 파일 수**: 5-6개

### 권장: Option C (Pragmatic)
**사유**: v7 공식 권장 Static API를 채택하면서도 실제 프로젝트에서 바로 사용 가능한 실용적 구조. 딥링크, 타입 안전성, 네이티브 링킹을 모두 커버.

---

## Gap Matrix

| Cat | Item | File:Line | Conf | Risk | BKIT Gate |
|---|---|---|---|---|---|
| 🆕 Build | `@react-navigation/native` + navigators 설치 | `package.json` | — | — | M5 (clean-deps) |
| 🆕 Build | `react-native-screens` + `react-native-safe-area-context` 피어 의존성 | `package.json` | — | — | M5 |
| 🆕 Build | iOS CocoaPods 네이티브 링킹 | `ios/Podfile.lock` | — | HIGH | M2 (build-pass) |
| 🆕 Build | Android `RNScreensFragmentFactory` | `android/.../MainActivity.kt` | — | HIGH | M2 |
| 🆕 Build | Android `enableOnBackInvokedCallback=false` | `android/.../AndroidManifest.xml` | — | MED | M2 |
| 🆕 Build | `src/navigation/RootNavigator.tsx` (Static Config) | NEW | — | — | M1 (spec-match) |
| 🆕 Build | `src/navigation/types.ts` (module augmentation) | NEW | — | — | M1 |
| 🆕 Build | `src/navigation/linking.ts` (딥링크 설정) | NEW | — | — | M1 |
| 🆕 Build | `App.tsx` (createStaticNavigation 래퍼) | `App.tsx` | — | — | M1 |
| 🆕 Build | iOS `RCTLinkingManager` (딥링크) | `ios/.../AppDelegate.swift` | — | MED | M1 |
| 🆕 Build | Android intent-filter (딥링크) | `android/.../AndroidManifest.xml` | — | MED | M1 |

---

## Waves

### Wave 1 — Foundation: 패키지 설치 + 네이티브 링킹 (4 tasks, parallel after task-A)

- [ ] **task-A**: npm 의존성 설치 — 코어 + 피어
  - **Action**: `npm install @react-navigation/native @react-navigation/native-stack @react-navigation/bottom-tabs react-native-screens react-native-safe-area-context`
  - **Files**: `package.json`, `package-lock.json`
  - **Worker**: `mini`
  - **Token est:** ~0.5K
  - **Verify**: `npm ls @react-navigation/native react-native-screens --depth=0` — 버전 확인
  - **Gate**: M5 (clean-deps)
  - **Evidence**: `.omo/ulw-loop/evidence/sim-bare-rn-nav-w1-a-deps.txt`

- [ ] **task-B**: iOS CocoaPods 네이티브 링킹
  - **Action**: `npx pod-install ios` (또는 `cd ios && pod install`)
  - **Files**: `ios/Podfile.lock`, `ios/Pods/`
  - **Worker**: `heavy` (네트워크 다운로드, 빌드 시간)
  - **Depends on**: `[task-A]`
  - **Token est:** ~0.5K
  - **Verify**: `grep -c "react-native-screens" ios/Podfile.lock` → ≥ 1, `grep -c "react-native-safe-area-context" ios/Podfile.lock` → ≥ 1
  - **Gate**: M2 (build-pass)
  - **Evidence**: `.omo/ulw-loop/evidence/sim-bare-rn-nav-w1-b-podfile.txt`

- [ ] **task-C**: Android `MainActivity` — `RNScreensFragmentFactory` 추가
  - **Action**: `MainActivity.kt` (또는 `.java`)의 `onCreate()`에 `supportFragmentManager.fragmentFactory = RNScreensFragmentFactory()` 추가, `super.onCreate()` **이전**에 위치
  - **Files**: `android/app/src/main/java/<package>/MainActivity.kt`
  - **Worker**: `mini`
  - **Depends on**: `[task-A]` (네이티브 패키지 설치 후)
  - **Token est:** ~1K
  - **Verify**: `grep "RNScreensFragmentFactory" android/app/src/main/java/**/MainActivity.kt` → match
  - **Gate**: M2 (build-pass)
  - **Evidence**: `.omo/ulw-loop/evidence/sim-bare-rn-nav-w1-c-activity.txt`

  **Kotlin (RN ≥ 0.76 기본)**:
  ```kotlin
  import android.os.Bundle
  import com.swmansion.rnscreens.fragment.restoration.RNScreensFragmentFactory

  class MainActivity : ReactActivity() {
      override fun onCreate(savedInstanceState: Bundle?) {
          supportFragmentManager.fragmentFactory = RNScreensFragmentFactory()
          super.onCreate(savedInstanceState)
      }
  }
  ```

- [ ] **task-D**: Android predictive back gesture 비활성화
  - **Action**: `AndroidManifest.xml`의 `<application>` 태그에 `android:enableOnBackInvokedCallback="false"` 추가
  - **Files**: `android/app/src/main/AndroidManifest.xml`
  - **Worker**: `mini`
  - **Depends on**: `[]` (순수 설정, 의존성 없음)
  - **Token est:** ~0.5K
  - **Verify**: `grep "enableOnBackInvokedCallback" android/app/src/main/AndroidManifest.xml` → `"false"`
  - **Gate**: M2 (build-pass)
  - **Evidence**: `.omo/ulw-loop/evidence/sim-bare-rn-nav-w1-d-manifest.txt`

### Wave 2 — Core: 네비게이션 구조 + 타입 정의 (3 tasks, parallel after Wave 1)

- [ ] **task-E**: `src/navigation/types.ts` — 네비게이션 타입 정의
  - **Action**: `StaticParamList` 타입, `RootNavigator` module augmentation 정의
  - **Files**: `src/navigation/types.ts` (NEW)
  - **Worker**: `mini`
  - **Depends on**: `[task-A]`
  - **Token est:** ~1K
  - **Verify**: `npx tsc --noEmit` — types 파일 컴파일 오류 0
  - **Gate**: M1 (spec-match)
  - **Evidence**: `.omo/ulw-loop/evidence/sim-bare-rn-nav-w2-e-types.txt`

  ```typescript
  // src/navigation/types.ts
  import type { StaticParamList } from '@react-navigation/native';
  import type { RootNavigator } from './RootNavigator';

  // 추출된 파라미터 리스트 타입 — 모든 화면의 params를 자동 추론
  export type RootStackParamList = StaticParamList<typeof RootNavigator>;

  // useNavigation() 자동 타입 추론을 위한 module augmentation
  declare module '@react-navigation/core' {
    interface RootNavigator extends RootNavigator {}
  }
  ```

- [ ] **task-F**: `src/navigation/RootNavigator.tsx` — Static Configuration 네비게이터
  - **Action**: `createNativeStackNavigator` + `createBottomTabNavigator` 중첩, `createStaticScreen`으로 각 화면 등록. `HomeScreen`, `DetailsScreen`, `ProfileScreen` placeholder 포함.
  - **Files**: `src/navigation/RootNavigator.tsx` (NEW)
  - **Worker**: `medium`
  - **Depends on**: `[task-E]`
  - **Token est:** ~2K
  - **Verify**: `npx tsc --noEmit` — 네비게이터 정의 타입 오류 0
  - **Gate**: M1 (spec-match)
  - **Evidence**: `.omo/ulw-loop/evidence/sim-bare-rn-nav-w2-f-navigator.txt`

  ```typescript
  // src/navigation/RootNavigator.tsx
  import { createNativeStackNavigator } from '@react-navigation/native-stack';
  import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
  import type { StaticScreenProps } from '@react-navigation/native';

  // ── Screen Props ──────────────────────────────────
  type HomeProps = StaticScreenProps<{}>;
  type DetailsProps = StaticScreenProps<{ itemId: string }>;
  type ProfileProps = StaticScreenProps<{}>;
  type SettingsProps = StaticScreenProps<{}>;

  // ── Placeholder Screens ───────────────────────────
  function HomeScreen({}: HomeProps) { /* TODO */ return null; }
  function DetailsScreen({ route }: DetailsProps) { /* route.params.itemId */ return null; }
  function ProfileScreen({}: ProfileProps) { return null; }
  function SettingsScreen({}: SettingsProps) { return null; }

  // ── Tab Navigator ─────────────────────────────────
  const TabNavigator = createBottomTabNavigator({
    screens: {
      Home: { screen: HomeScreen },
      Profile: { screen: ProfileScreen },
    },
  });

  // ── Root Stack ────────────────────────────────────
  export const RootNavigator = createNativeStackNavigator({
    screenOptions: { headerShown: false },
    screens: {
      Tabs: { screen: TabNavigator },
      Details: { screen: DetailsScreen },
      Settings: { screen: SettingsScreen },
    },
  });
  ```

- [ ] **task-G**: `App.tsx` — `createStaticNavigation` 래퍼
  - **Action**: `createStaticNavigation(RootNavigator)`로 `Navigation` 컴포넌트 생성, `App`에서 렌더링
  - **Files**: `App.tsx` (MODIFY)
  - **Worker**: `mini`
  - **Depends on**: `[task-F]`
  - **Token est:** ~1K
  - **Verify**: `npx tsc --noEmit` — App.tsx 타입 오류 0
  - **Gate**: M1 (spec-match)
  - **Evidence**: `.omo/ulw-loop/evidence/sim-bare-rn-nav-w2-g-app.txt`

  ```typescript
  // App.tsx
  import { createStaticNavigation } from '@react-navigation/native';
  import { RootNavigator } from './src/navigation/RootNavigator';

  const Navigation = createStaticNavigation(RootNavigator);

  export default function App() {
    return <Navigation />;
  }
  ```

### Wave 3 — Integration: 딥링크 설정 (3 tasks, parallel after Wave 2)

- [ ] **task-H**: `src/navigation/linking.ts` — 딥링크 설정
  - **Action**: `linking` 객체 정의, `prefixes: ['myapp://']` + `enabled: 'auto'` (Static API 자동 경로 생성), `App.tsx`에 `linking` prop 전달
  - **Files**: `src/navigation/linking.ts` (NEW), `App.tsx` (MODIFY)
  - **Worker**: `mini`
  - **Depends on**: `[task-G]`
  - **Token est:** ~1K
  - **Verify**: `grep "linking" App.tsx` — linking prop 존재 확인
  - **Gate**: M1 (spec-match)
  - **Evidence**: `.omo/ulw-loop/evidence/sim-bare-rn-nav-w3-h-linking.txt`

  ```typescript
  // src/navigation/linking.ts
  import type { LinkingOptions } from '@react-navigation/native';
  import type { RootStackParamList } from './types';

  export const linking: LinkingOptions<RootStackParamList> = {
    enabled: 'auto', // Static API: 모든 screen 경로 자동 생성
    prefixes: ['myapp://', 'https://myapp.com'],
  };
  ```

- [ ] **task-I**: iOS 딥링크 네이티브 설정
  - **Action**: `AppDelegate.swift`에 `RCTLinkingManager.application(_:open:options:)` 추가, `Info.plist`에 `CFBundleURLTypes`로 `myapp` 스킴 등록
  - **Files**: `ios/<Project>/AppDelegate.swift`, `ios/<Project>/Info.plist`
  - **Worker**: `mini`
  - **Depends on**: `[]` (네이티브 설정, JS 의존성 없음)
  - **Token est:** ~1K
  - **Verify**: `grep "RCTLinkingManager" ios/**/AppDelegate.swift` → match
  - **Gate**: M1 (spec-match)
  - **Evidence**: `.omo/ulw-loop/evidence/sim-bare-rn-nav-w3-i-ios-deeplink.txt`

  **AppDelegate.swift 추가 코드**:
  ```swift
  import React

  // ... 기존 AppDelegate 클래스 내부에 추가:
  override func application(_ app: UIApplication, open url: URL,
      options: [UIApplication.OpenURLOptionsKey: Any] = [:]) -> Bool {
      return RCTLinkingManager.application(app, open: url, options: options)
  }
  ```

  **Info.plist 추가**:
  ```xml
  <key>CFBundleURLTypes</key>
  <array>
      <dict>
          <key>CFBundleURLSchemes</key>
          <array>
              <string>myapp</string>
          </array>
      </dict>
  </array>
  ```

- [ ] **task-J**: Android 딥링크 네이티브 설정
  - **Action**: `AndroidManifest.xml`의 MainActivity `<activity>` 내에 intent-filter 추가 (`myapp://` 스킴)
  - **Files**: `android/app/src/main/AndroidManifest.xml`
  - **Worker**: `mini`
  - **Depends on**: `[]`
  - **Token est:** ~0.5K
  - **Verify**: `grep "myapp" android/app/src/main/AndroidManifest.xml` → scheme 등록 확인
  - **Gate**: M1 (spec-match)
  - **Evidence**: `.omo/ulw-loop/evidence/sim-bare-rn-nav-w3-j-android-deeplink.txt`

  ```xml
  <!-- 기존 <activity android:name=".MainActivity" ...> 내부에 추가 -->
  <intent-filter>
      <action android:name="android.intent.action.VIEW" />
      <category android:name="android.intent.category.DEFAULT" />
      <category android:name="android.intent.category.BROWSABLE" />
      <data android:scheme="myapp" />
  </intent-filter>
  ```

---

## Risk Register (BKIT 11-Gate)

| Risk | BKIT Class | Sev | Threshold | Mitigation | Verification |
|---|---|---|---|---|---|
| react-native-screens ↔ RN 버전 불일치 | `M2_build_pass` | **HIGH** | iOS/Android 빌드 성공 | `react-native-screens` README 호환성 테이블 확인, RN ≥ 0.76 사용 | `npx react-native run-ios` + `run-android` 빌드 성공 |
| pod install 실패 (CocoaPods 누락, Ruby 버전) | `M2_build_pass` | **HIGH** | `pod install` exit 0 | `npx pod-install ios` 사용 (자동 CocoaPods 감지) | `echo $?` → 0 |
| RNScreensFragmentFactory 누락으로 Activity 재시작 시 크래시 | `M2_build_pass` | **HIGH** | `onCreate`에 factory 설정 | Kotlin/Java 코드 템플릿 제공, `super.onCreate()` 이전 위치 확인 | `grep "RNScreensFragmentFactory"` → match |
| Android predictive back gesture 충돌 | `M3_regression` | MED | 이중 back 방지 | `enableOnBackInvokedCallback="false"` | 실제 기기 테스트: back 제스처 1회 동작 |
| TypeScript 컴파일 오류 (타입 불일치) | `M1_spec_match` | MED | `tsc --noEmit` 0 오류 | `StaticScreenProps`, `StaticParamList`, module augmentation 사용 | `npx tsc --noEmit` |
| 딥링크 미작동 (스킴 충돌, 네이티브 설정 누락) | `M1_spec_match` | MED | `myapp://` 스킴 정상 처리 | iOS: `RCTLinkingManager` + `CFBundleURLTypes`, Android: intent-filter | `npx uri-scheme open myapp://home --ios` / `--android` |
| react-native-screens 4.25+ Paper 지원 중단 | `M5_dead_code` | MED | Fabric/New Arch 활성화 필요 | RN ≥ 0.82 사용 권장, 또는 react-native-screens ≤ 4.24 고정 | `npx react-native info` — New Architecture 활성화 확인 |
| 안전 영역 미처리 (노치/상단바 가림) | `M1_spec_match` | LOW | `react-native-safe-area-context` 정상 동작 | `SafeAreaProvider`가 `Navigation` 내부에서 자동 래핑됨 | iOS 시뮬레이터 iPhone 15 Pro: 콘텐츠가 노치에 가려지지 않음 |

---

## Verification Checklist

| # | Check | Command / Method | Expected |
|---|---|---|---|
| 1 | 모든 의존성 설치 완료 | `npm ls @react-navigation/native react-native-screens react-native-safe-area-context --depth=0` | 모든 패키지가 `--depth=0`에서 출력됨, `UNMET` 없음 |
| 2 | iOS pods 링크 완료 | `grep -c "react-native-screens" ios/Podfile.lock` | ≥ 1 |
| 3 | Android MainActivity 설정 | `grep "RNScreensFragmentFactory" android/app/src/main/java/**/MainActivity.*` | match |
| 4 | Android predictive back 비활성화 | `grep 'enableOnBackInvokedCallback="false"' android/app/src/main/AndroidManifest.xml` | match |
| 5 | TypeScript 컴파일 | `npx tsc --noEmit` | exit 0, 오류 0 |
| 6 | iOS 빌드 | `npx react-native run-ios --simulator="iPhone 15 Pro"` | 빌드 성공, 시뮬레이터 실행 |
| 7 | Android 빌드 | `npx react-native run-android` | 빌드 성공, 에뮬레이터 실행 |
| 8 | Tab 전환 | 앱 실행 후 Home → Profile 탭 탭 | 화면 전환 정상, 탭 아이콘 표시 |
| 9 | Stack push | Home에서 Details로 이동 (`navigation.navigate('Details', { itemId: '123' })`) | Details 화면 표시, back 버튼으로 복귀 |
| 10 | iOS 딥링크 | `npx uri-scheme open myapp://details --ios` | 앱이 Details 화면으로 열림 |
| 11 | Android 딥링크 | `npx uri-scheme open myapp://details --android` | 앱이 Details 화면으로 열림 |

---

## Execution

Run this plan with:
```
blackcow-loop "Execute plans/sim-bare-rn-nav.md" --completion-promise='iOS/Android both build successfully with Stack + Tab navigation functional and deep linking myapp:// scheme working' --trust-level=2
```

### Parallelism Guide
- Wave 1: task-A serial (npm install), then task-B || task-C || task-D parallel (3 workers)
- Wave 2: task-E || task-F parallel (no cross-dependency between types and navigator); task-G serial on task-F
- Wave 3: task-H || task-I || task-J parallel (3 workers)
- Total budget: ~10K / 128K target

### Dependencies Flow
```
task-A (npm install)
  ├─→ task-B (iOS pods) ─────────────────────┐
  ├─→ task-C (Android MainActivity) ──────────┤
  ├─→ task-D (Android Manifest: back) ────────┤
  ├─→ task-E (types.ts) ─→ task-F (navigator) ─→ task-G (App.tsx)
  │                                                │
  │                          ┌─────────────────────┘
  │                          ▼
  └──────────────────→ task-H (linking.ts)
                              task-I (iOS deeplink)   ← Wave 3 (all parallel)
                              task-J (Android deeplink)
```

### Critical Path
`task-A → task-E → task-F → task-G → task-H` (5 hops, estimated ~30 min including npm + pod install)
