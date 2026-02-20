# Chapter 10: 디버깅 기법

> **이 챕터의 목표**: 스코어보드가 MISMATCH를 보고했을 때, **체계적으로** 원인을 찾고, 수정하고, 검증하는 전체 디버깅 워크플로우를 습득합니다. UVM 메시지 시스템, 파형 분석, Factory Override를 활용한 디버깅, 흔한 에러 메시지 해석법을 다룹니다.

> **선수 지식**: Chapter 2 (시뮬레이터, VCD), Chapter 4 (Factory 패턴), Chapter 8 (스코어보드 MISMATCH), Chapter 9 (테스트 시나리오, regression)

---

## 10.1 왜 체계적 디버깅인가

> **이 절의 목표**: 체계적 디버깅의 필요성을 이해하고, UVM 디버깅 도구의 전체 맵과 워크플로우를 파악합니다.

### 10.1.1 "파형만 보면 되지?" — 실무의 현실

초보자가 가장 먼저 떠올리는 디버깅 방법은 파형(waveform)을 보는 것입니다. 물론 파형은 강력한 도구입니다. 하지만 실무에서는 이것만으로 부족합니다.

**파형만으로 디버깅하기 어려운 이유:**

1. **시뮬레이션 시간이 길다**: 수백만 클록 사이클 중 문제 시점을 찾아야 합니다
2. **신호가 많다**: SoC 수준에서는 수만 개의 신호가 동시에 변합니다
3. **트랜잭션 수준 정보가 없다**: 파형은 비트 레벨이지, "어떤 패킷이 전송됐는지"는 보이지 않습니다
4. **재현이 어렵다**: "언제" 문제가 발생했는지 모르면 파형에서 찾기 불가능합니다

UVM의 디버깅 도구를 활용하면 **문제 시점을 빠르게 좁히고**, 그 시점의 파형만 집중 분석할 수 있습니다. "파형을 보지 마라"가 아니라, **"파형을 볼 지점을 먼저 찾아라"**가 핵심입니다.

### 10.1.2 UVM 디버깅 도구 전체 맵

UVM은 다양한 디버깅 도구를 제공합니다. 각 도구의 역할을 먼저 파악하고, 상황에 맞게 선택하는 것이 중요합니다.

| 도구 | 용도 | 학습 섹션 |
|------|------|-----------|
| **메시지 시스템** | 로그 출력 제어, 심각도별 분류 | 10.2 |
| **Verbosity 제어** | 필요한 정보만 필터링 | 10.2 |
| **파형 분석** | 신호 레벨 타이밍 확인 | 10.3 |
| **Factory Override** | 디버그 컴포넌트 교체 | 10.4 |
| **에러 메시지 해석** | 빠른 원인 분류 | 10.5 |

### 10.1.3 디버깅 워크플로우

체계적 디버깅은 다음 순서를 따릅니다:

```
┌─────────────────────────────────────────────────────────┐
│              디버깅 워크플로우                            │
├─────────────────────────────────────────────────────────┤
│                                                         │
│   ① MISMATCH 발견    ──→   ② 로그 분석               │
│   스코어보드 보고           Verbosity 높여              │
│                             시점·위치 확인              │
│           │                       │                     │
│           ▼                       ▼                     │
│   ③ 파형 확인         ←──   문제 시점으로               │
│   RTL 신호 분석             타임스탬프 연결              │
│                                                         │
│           │                                             │
│           ▼                                             │
│   ④ 원인 분리         ──→   ⑤ 수정 & 검증             │
│   Factory Override          버그 수정 후                │
│   컴포넌트 교체              Regression 확인            │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

이 워크플로우의 핵심은 **범위 좁히기**입니다. 수백만 사이클 중 문제 시점을 찾고(①→②), 그 시점의 신호를 확인하고(③), 문제 원인을 특정 컴포넌트로 분리한(④) 다음 수정합니다(⑤).

> 💡 **실무 팁**: 팹리스 회사에서 검증 엔지니어의 일상은 이 워크플로우의 반복입니다. regression에서 FAIL이 나오면, 이 5단계를 따라 원인을 찾고 RTL 설계자에게 버그 리포트를 작성합니다.

---

## 10.2 UVM 메시지 시스템

> **이 절의 목표**: UVM 메시지 매크로의 4가지 심각도와 Verbosity 레벨을 이해하고, 명령줄과 코드에서 제어하는 방법을 습득합니다.

UVM 메시지 시스템은 디버깅의 **첫 번째 도구**입니다. `$display` 대신 UVM 메시지 매크로를 사용하면, 심각도와 상세도를 체계적으로 제어할 수 있습니다.

### 10.2.1 4가지 심각도 — UVM_INFO / WARNING / ERROR / FATAL

UVM은 메시지를 4가지 심각도(severity)로 분류합니다:

```systemverilog
// ──────────────────────────────────────────
// UVM 4가지 심각도 매크로
// ──────────────────────────────────────────

// INFO: 일반 정보 메시지 — 진행 상황, 디버그 정보
`uvm_info("DRIVER", "트랜잭션 전송 시작", UVM_MEDIUM)

// WARNING: 주의 필요 — 동작에 영향 없지만 확인 권장
`uvm_warning("MONITOR", "예상보다 긴 응답 시간 감지")

// ERROR: 오류 발생 — 시뮬레이션은 계속되지만 문제 있음
`uvm_error("SCOREBOARD",
  $sformatf("MISMATCH! expected=%0d, actual=%0d", expected, actual))

// FATAL: 치명적 오류 — 시뮬레이션 즉시 중단
`uvm_fatal("ENV", "필수 인터페이스가 config_db에 없습니다")
```

**심각도별 동작:**

| 심각도 | 동작 | 시뮬레이션 | 사용 예 |
|--------|------|------------|---------|
| `UVM_INFO` | 로그 출력 | 계속 | 진행 상황, 디버그 데이터 |
| `UVM_WARNING` | 경고 출력 | 계속 | 타이밍 위반, 비정상 상태 |
| `UVM_ERROR` | 에러 카운트 증가 | 계속 (기본) | MISMATCH, 프로토콜 위반 |
| `UVM_FATAL` | 에러 출력 | **즉시 중단** | 필수 설정 누락, 복구 불가 |

**매크로 형식:**

```systemverilog
// `uvm_info(ID, MESSAGE, VERBOSITY)
// - ID: 메시지 출처를 식별하는 문자열 (필터링에 사용)
// - MESSAGE: 출력할 메시지 문자열
// - VERBOSITY: 이 메시지의 상세도 레벨 (다음 섹션에서 설명)

// `uvm_warning(ID, MESSAGE)
// `uvm_error(ID, MESSAGE)
// `uvm_fatal(ID, MESSAGE)
// - WARNING/ERROR/FATAL은 VERBOSITY 인자가 없음 (항상 출력)
```

Ch.8에서 작성한 스코어보드를 기억하세요. MISMATCH를 `uvm_error`로 보고했습니다:

```systemverilog
// Ch.8에서 작성한 스코어보드의 MISMATCH 보고
if (expected !== item.count) begin
  `uvm_error(get_type_name(),
    $sformatf("MISMATCH! expected=%0d, actual=%0d (rst_n=%0b, enable=%0b)",
              expected, item.count, item.rst_n, item.enable))
  error_count++;
end
```

이 `UVM_ERROR`가 바로 디버깅의 **출발점**입니다.

> 💡 **실무 팁**: `$display`로 디버그 메시지를 출력하면 시뮬레이션이 끝난 후 제거하기 어렵습니다. `uvm_info`를 사용하면 verbosity 제어로 코드 수정 없이 끄고 켤 수 있습니다.

### 10.2.2 Verbosity 레벨 — LOW / MEDIUM / HIGH / DEBUG

`uvm_info`의 세 번째 인자인 verbosity는 메시지의 **상세도**를 지정합니다. verbosity 레벨이 높을수록 더 자세한 정보이며, 낮을수록 핵심 정보입니다.

```
┌───────────────────────────────────────────────┐
│          Verbosity 레벨 피라미드               │
├───────────────────────────────────────────────┤
│                                               │
│              ┌─────────┐                      │
│              │UVM_DEBUG│ 500                   │
│              │ 최상세  │                       │
│            ┌─┴─────────┴─┐                    │
│            │  UVM_FULL   │ 400                │
│            │  전체 상세  │                     │
│          ┌─┴─────────────┴─┐                  │
│          │   UVM_HIGH     │ 300               │
│          │   높은 상세    │                    │
│        ┌─┴─────────────────┴─┐                │
│        │    UVM_MEDIUM      │ 200             │
│        │    중간 상세       │                  │
│      ┌─┴─────────────────────┴─┐              │
│      │     UVM_LOW            │ 100           │
│      │     낮은 상세          │                │
│    ┌─┴─────────────────────────┴─┐            │
│    │      UVM_NONE              │ 0           │
│    │      메시지 없음           │              │
│    └─────────────────────────────┘            │
│                                               │
│   ▲ 위로 갈수록: 상세 정보 ↑, 메시지 양 ↑   │
│   ▼ 아래로 갈수록: 핵심 정보 ↓, 메시지 양 ↓  │
│                                               │
└───────────────────────────────────────────────┘
```

**각 레벨의 용도:**

```systemverilog
// UVM_NONE (0) — 절대 숨기지 않는 핵심 메시지
`uvm_info("TEST", "테스트 시작", UVM_NONE)

// UVM_LOW (100) — 주요 이벤트 (기본 출력)
`uvm_info("DRIVER", "리셋 완료", UVM_LOW)

// UVM_MEDIUM (200) — 트랜잭션 레벨 정보
`uvm_info("DRIVER",
  $sformatf("전송: rst_n=%0b, enable=%0b", item.rst_n, item.enable),
  UVM_MEDIUM)

// UVM_HIGH (300) — 상세 디버그 정보
`uvm_info("DRIVER",
  $sformatf("인터페이스 값: clk=%0b, rst_n=%0b, enable=%0b, count=%0d",
            vif.clk, vif.rst_n, vif.enable, vif.count),
  UVM_HIGH)

// UVM_FULL (400) — 매우 상세한 내부 상태
`uvm_info("SCOREBOARD",
  $sformatf("레퍼런스 모델 상태: prev_count=%0d, match=%0d, error=%0d",
            prev_count, match_count, error_count),
  UVM_FULL)

// UVM_DEBUG (500) — 최대 상세 (성능 영향 가능)
`uvm_info("MONITOR",
  $sformatf("샘플링 시점: $time=%0t, 모든 신호 덤프", $time),
  UVM_DEBUG)
```

**핵심 원리**: 시뮬레이터의 현재 verbosity 설정보다 **같거나 낮은** 레벨의 메시지만 출력됩니다. 기본 설정은 `UVM_MEDIUM(200)`이므로, `UVM_NONE(0)`, `UVM_LOW(100)`, `UVM_MEDIUM(200)` 메시지만 출력됩니다.

### 10.2.3 명령줄 Verbosity 제어 (+UVM_VERBOSITY)

코드를 수정하지 않고 시뮬레이션 실행 시 verbosity를 변경할 수 있습니다:

```bash
# 기본 실행 — UVM_MEDIUM (200) 이하 메시지 출력
vsim +UVM_TESTNAME=counter_coverage_closure_test

# 높은 상세도 — UVM_HIGH (300) 이하 메시지 출력
vsim +UVM_TESTNAME=counter_coverage_closure_test +UVM_VERBOSITY=UVM_HIGH

# 최대 상세도 — 모든 메시지 출력
vsim +UVM_TESTNAME=counter_coverage_closure_test +UVM_VERBOSITY=UVM_DEBUG

# 최소 출력 — UVM_NONE (0)만 출력
vsim +UVM_TESTNAME=counter_coverage_closure_test +UVM_VERBOSITY=UVM_NONE
```

**EDA Playground에서의 설정:**

EDA Playground를 사용하는 경우, **Compile & Run Options** 필드에 추가합니다:

```
# Run Options 필드에 입력
+UVM_VERBOSITY=UVM_HIGH
```

Ch.9에서 `+UVM_TESTNAME`을 Run Options에 추가했던 것과 같은 방식입니다.

### 10.2.4 컴포넌트별 Verbosity 제어

전체 시뮬레이션이 아닌 **특정 컴포넌트**만 상세 로그를 켤 수 있습니다. 이것이 `$display`로는 불가능한 UVM의 강점입니다.

```systemverilog
// ──────────────────────────────────────────
// 컴포넌트별 Verbosity 제어
// 파일: counter_debug_test.sv
// 역할: 특정 컴포넌트만 상세 로그를 켜는 디버그 테스트
// ──────────────────────────────────────────
class counter_debug_test extends counter_base_test;
  `uvm_component_utils(counter_debug_test)

  function new(string name, uvm_component parent);
    super.new(name, parent);
  endfunction

  // build_phase에서 특정 컴포넌트 verbosity 설정
  function void build_phase(uvm_phase phase);
    super.build_phase(phase);  // counter_env 생성

    // 스코어보드만 UVM_DEBUG로 설정
    // 다른 컴포넌트는 기본값(UVM_MEDIUM) 유지
    env.scoreboard.set_report_verbosity_level(UVM_DEBUG);
  endfunction

  // 또는 connect_phase에서 설정 (env.agent 등 접근 필요 시)
  function void connect_phase(uvm_phase phase);
    super.connect_phase(phase);

    // 드라이버도 HIGH로 올리기
    env.agent.driver.set_report_verbosity_level(UVM_HIGH);
  endfunction
endclass
```

**명령줄에서 컴포넌트별 설정도 가능합니다:**

```bash
# 특정 컴포넌트만 verbosity 변경
vsim +uvm_set_verbosity=uvm_test_top.env.scoreboard,_ALL_,UVM_DEBUG,run
```

> 💡 **실무 팁**: 디버깅 시 전체 verbosity를 DEBUG로 올리면 로그가 GB 단위로 커질 수 있습니다. **문제가 의심되는 컴포넌트만** 선택적으로 올리는 것이 효율적입니다.

### 10.2.5 메시지 필터링 실전 예제

실전에서 verbosity를 단계적으로 올려가며 문제를 좁히는 과정을 살펴봅니다.

**상황**: Ch.9의 `counter_coverage_closure_test` 실행 중 MISMATCH 발생

```
# ── 1단계: 기본 실행 (UVM_MEDIUM) ──

UVM_ERROR @ 850ns: uvm_test_top.env.scoreboard [counter_scoreboard]
  MISMATCH! expected=0, actual=5 (rst_n=0, enable=1)
```

MISMATCH가 발생했지만, 이것만으로는 원인을 알 수 없습니다. 정보가 더 필요합니다.

```
# ── 2단계: 스코어보드 HIGH로 올리기 ──
# 명령줄: +uvm_set_verbosity=*scoreboard*,_ALL_,UVM_HIGH,run

UVM_INFO @ 830ns: uvm_test_top.env.scoreboard [counter_scoreboard]
  트랜잭션 #41: predict(1, 1, 11) → expected=12, actual=12 ✓ MATCH
UVM_INFO @ 850ns: uvm_test_top.env.scoreboard [counter_scoreboard]
  트랜잭션 #42: predict(0, 1, 12) → expected=0
UVM_INFO @ 850ns: uvm_test_top.env.scoreboard [counter_scoreboard]
  DUT 실제값: count=5
UVM_ERROR @ 850ns: uvm_test_top.env.scoreboard [counter_scoreboard]
  MISMATCH! expected=0, actual=5 (rst_n=0, enable=1)
```

이제 더 많은 정보가 보입니다: 트랜잭션 #42에서, `rst_n=0`(리셋 활성)인데 DUT의 count가 0이 아닌 5입니다.

```
# ── 3단계: 드라이버도 HIGH로 올리기 ──
# 드라이버가 실제로 rst_n=0을 인터페이스에 전달했는지 확인

UVM_INFO @ 850ns: uvm_test_top.env.agent.driver [counter_driver]
  전송: rst_n=0, enable=1
UVM_INFO @ 850ns: uvm_test_top.env.agent.driver [counter_driver]
  인터페이스 확인: vif.rst_n=0, vif.enable=1
UVM_INFO @ 850ns: uvm_test_top.env.scoreboard [counter_scoreboard]
  트랜잭션 #42: predict(0, 1, 12) → expected=0
UVM_ERROR @ 850ns: uvm_test_top.env.scoreboard [counter_scoreboard]
  MISMATCH! expected=0, actual=5 (rst_n=0, enable=1)
```

드라이버는 정상적으로 `rst_n=0`을 전달했습니다. 그런데 DUT의 count가 0이 아닙니다. → **RTL 버그 가능성!**

이제 파형에서 **트랜잭션 #42 시점(850ns)**만 확인하면 됩니다. 이것이 "파형을 볼 지점을 먼저 찾아라"의 의미입니다.

---

## 10.3 파형 분석

> **이 절의 목표**: VCD 파형 파일을 생성하고, UVM 로그의 타임스탬프와 연결하여 MISMATCH 시점의 RTL 신호를 분석하는 기술을 습득합니다.

### 10.3.1 VCD/FSDB 파일 생성

파형을 보려면 시뮬레이션 중 신호 변화를 파일로 저장해야 합니다. 가장 일반적인 형식은 **VCD**(Value Change Dump)와 **FSDB**(Fast Signal Database)입니다.

```systemverilog
// ──────────────────────────────────────────
// VCD 파일 생성 — 테스트벤치 top 모듈
// 파일: tb_top.sv
// 역할: VCD 파형 덤프를 설정하고 UVM 테스트를 실행
// ──────────────────────────────────────────
module tb_top;
  // 클록 생성
  logic clk;
  initial clk = 0;
  always #5 clk = ~clk;  // 10ns 주기

  // 인터페이스 인스턴스
  counter_if counter_intf(clk);

  // DUT 인스턴스
  counter_4bit dut (
    .clk    (clk),
    .rst_n  (counter_intf.rst_n),
    .enable (counter_intf.enable),
    .count  (counter_intf.count)
  );

  initial begin
    // VCD 파형 덤프 설정
    $dumpfile("counter_debug.vcd");  // 출력 파일 이름
    $dumpvars(0, tb_top);           // 0: 모든 계층 신호 덤프
                                     // tb_top: 시작 모듈

    // config_db에 인터페이스 등록
    uvm_config_db#(virtual counter_if)::set(
      null, "uvm_test_top.*", "vif", counter_intf);

    // UVM 테스트 실행
    run_test();
  end
endmodule
```

**VCD vs FSDB 비교:**

| 특성 | VCD | FSDB |
|------|-----|------|
| **형식** | 텍스트 (ASCII) | 바이너리 |
| **파일 크기** | 큼 | 작음 (5~10배) |
| **표준** | IEEE 1364 표준 | Synopsys 독점 |
| **뷰어** | GTKWave, 모든 도구 | Verdi (Synopsys) |
| **EDA Playground** | ✅ 지원 | ❌ 미지원 |
| **실무 사용** | 작은 설계, 학습용 | 대규모 SoC |

> 💡 **실무 팁**: 팹리스 회사에서는 대부분 Synopsys Verdi + FSDB를 사용합니다. 하지만 학습과 작은 프로젝트에서는 VCD + GTKWave가 무료이고 충분합니다.

### 10.3.2 파형 뷰어 — DVE, Verdi, GTKWave

**GTKWave (무료, 오픈소스) — 추천:**

```bash
# VCD 파일을 GTKWave로 열기
gtkwave counter_debug.vcd &
```

GTKWave에서 확인할 신호:
- `tb_top.dut.clk` — 클록
- `tb_top.dut.rst_n` — 리셋
- `tb_top.dut.enable` — 인에이블
- `tb_top.dut.count[3:0]` — 카운터 출력

**GTKWave 기본 조작법:**

| 조작 | 방법 |
|------|------|
| **신호 추가** | 왼쪽 계층 트리에서 모듈 선택 → 신호 선택 → **Append** 클릭 |
| **줌인/줌아웃** | 마우스 휠 또는 도구 모음의 **+/-** 버튼 |
| **시간 이동** | **Time → Jump to Time** 메뉴에서 원하는 시간 입력 (예: `850ns`) |
| **커서 배치** | 파형 위 클릭으로 커서 배치, 두 커서 간 시간 차이 자동 표시 |
| **신호 값 확인** | 커서 위치의 신호 값이 왼쪽 패널에 표시됨 |

**EDA Playground에서 파형 보기:**

EDA Playground에서는 시뮬레이션 완료 후 **Open EPWave** 버튼을 클릭하면 웹 기반 파형 뷰어가 열립니다. `$dumpfile`과 `$dumpvars`가 코드에 포함되어 있어야 합니다.

**Verdi (Synopsys, 상용):**

```bash
# FSDB 파일을 Verdi로 열기 (실무 환경)
verdi -ssf counter_debug.fsdb &
```

**DVE (Synopsys, 상용):**

```bash
# VPD 파일을 DVE로 열기
dve -vpd counter_debug.vpd &
```

> 💡 **면접 팁**: "파형 뷰어 사용 경험이 있으신가요?"라는 질문을 받으면, GTKWave 경험을 말하고, Verdi의 존재와 FSDB 형식에 대해 알고 있다고 답하면 좋습니다.

### 10.3.3 RTL 신호와 UVM 로그 타임스탬프 연결

UVM 로그의 타임스탬프와 파형의 시간축을 연결하는 것이 핵심 기술입니다.

```
UVM 로그 출력 예시:
UVM_ERROR @ 850ns: uvm_test_top.env.scoreboard [counter_scoreboard]
  MISMATCH! expected=0, actual=5 (rst_n=0, enable=1)

→ 파형 뷰어에서 850ns로 이동 → 그 시점의 RTL 신호 확인
```

**타임스탬프를 활용한 스코어보드 메시지 패턴:**

```systemverilog
// ──────────────────────────────────────────
// 타임스탬프 포함 상세 스코어보드 메시지
// 파일: counter_scoreboard.sv (디버그 강화)
// 역할: MISMATCH 전후 맥락을 상세히 기록
// 참고: transaction_count, match_count, error_count, prev_count는
//       Ch.8에서 선언한 스코어보드 멤버 변수입니다
// ──────────────────────────────────────────
function void write(counter_seq_item item);
  transaction_count++;  // Ch.8 스코어보드의 int transaction_count 변수

  // 예측
  logic [3:0] expected = predict(item.rst_n, item.enable, prev_count);

  // 상세 트랜잭션 로그 (UVM_HIGH — 평소에는 숨겨짐)
  `uvm_info(get_type_name(),
    $sformatf("[%0t] 트랜잭션 #%0d: rst_n=%0b, enable=%0b, prev=%0d → expected=%0d, actual=%0d",
              $time, transaction_count,
              item.rst_n, item.enable, prev_count,
              expected, item.count),
    UVM_HIGH)

  // 비교
  if (expected !== item.count) begin
    `uvm_error(get_type_name(),
      $sformatf("[%0t] MISMATCH #%0d! expected=%0d, actual=%0d (rst_n=%0b, enable=%0b)",
                $time, transaction_count, expected, item.count,
                item.rst_n, item.enable))
    error_count++;
  end else begin
    match_count++;
  end

  prev_count = item.count;
endfunction
```

> 💡 **실무 팁**: MISMATCH 발생 시, 로그의 타임스탬프(`850ns`)를 파형 뷰어의 검색 기능에 입력하면 해당 시점으로 즉시 이동할 수 있습니다. GTKWave에서는 **Time → Jump to Time** 메뉴를 사용합니다.

### 10.3.4 실전: MISMATCH 시점 파형 확인

10.2.5에서 발견한 MISMATCH를 파형에서 확인하는 과정입니다.

**로그에서 얻은 정보:**
- 시점: 850ns (트랜잭션 #42)
- 입력: `rst_n=0`, `enable=1`
- 예측: `count=0` (리셋이면 0이어야 함)
- 실제: `count=5`

**파형에서 확인할 사항:**

```
시간   | clk | rst_n | enable | count | 분석
───────┼─────┼───────┼────────┼───────┼──────────────
830ns  |  ↑  |   1   |   1    |  12   | 정상 카운팅
840ns  |  ↑  |   1   |   1    |  13   |
845ns  |     |   0   |   1    |  13   | rst_n↓ (클록 에지 사이에 변경)
850ns  |  ↑  |   0   |   1    |   5   | ❌ 0이어야 하는데!
855ns  |  ↑  |   0   |   1    |   6   | ❌ 여전히 카운팅됨
860ns  |  ↑  |   0   |   0    |   0   | enable=0이 되어야 리셋됨
```

파형을 보면, `rst_n=0`이 845ns에 활성화되었는데 850ns에 count가 5입니다. `enable=0`이 되는 860ns에야 비로소 0이 됩니다. 이것은 **RTL에서 리셋과 enable의 우선순위 버그**입니다.

RTL 코드를 확인해봅시다:

```systemverilog
// ── 버그가 있는 RTL ──
always_ff @(posedge clk) begin
  if (enable)            // ❌ enable을 먼저 검사!
    count <= count + 1;
  else if (!rst_n)       // ❌ 리셋이 나중에 검사됨
    count <= 4'b0;
end
```

문제를 찾았습니다! `enable`이 `rst_n`보다 우선순위가 높아서, `rst_n=0`이면서 `enable=1`일 때 리셋이 무시됩니다.

**수정된 RTL:**

```systemverilog
// ── 올바른 RTL ──
always_ff @(posedge clk) begin
  if (!rst_n)            // ✅ 리셋이 최우선
    count <= 4'b0;
  else if (enable)       // ✅ 리셋이 아닐 때만 카운팅
    count <= count + 1;
end
```

> 💡 **실무 팁**: 리셋 우선순위 버그는 실무에서 매우 흔합니다. 특히 복잡한 FSM(상태 머신)에서 리셋 조건이 다른 조건 뒤에 위치하면 같은 문제가 발생합니다.

---

## 10.4 Factory Override 디버깅

> **이 절의 목표**: Ch.4에서 배운 Factory 패턴을 활용하여, 코드 수정 없이 디버그 컴포넌트를 교체하는 기법을 습득합니다.

### 10.4.1 디버그 드라이버 교체 — 상세 로깅 버전

기존 드라이버에 상세 로깅을 추가한 디버그 버전을 만들어봅시다. 기존 `counter_driver`를 **상속**하여 `run_phase`만 override합니다.

```systemverilog
// ──────────────────────────────────────────
// 디버그 드라이버 — 상세 로깅 버전
// 파일: counter_debug_driver.sv
// 역할: 기존 드라이버를 상속하여 모든 인터페이스 변화를 기록
// ──────────────────────────────────────────
class counter_debug_driver extends counter_driver;
  `uvm_component_utils(counter_debug_driver)

  function new(string name, uvm_component parent);
    super.new(name, parent);
  endfunction

  // 기존 run_phase를 override하여 상세 로깅 추가
  virtual task run_phase(uvm_phase phase);
    `uvm_info(get_type_name(),
      "=== 디버그 드라이버 활성화 ===", UVM_NONE)

    forever begin
      counter_seq_item item;
      seq_item_port.get_next_item(item);

      // ── 전송 전 상태 기록 ──
      `uvm_info(get_type_name(),
        $sformatf("[%0t] 전송 전: vif.rst_n=%0b, vif.enable=%0b, vif.count=%0d",
                  $time, vif.rst_n, vif.enable, vif.count),
        UVM_LOW)

      // ── 인터페이스에 값 적용 ──
      @(posedge vif.clk);
      vif.rst_n  <= item.rst_n;
      vif.enable <= item.enable;

      // ── 전송 후 상태 기록 ──
      `uvm_info(get_type_name(),
        $sformatf("[%0t] 전송 후: rst_n=%0b→%0b, enable=%0b→%0b",
                  $time, vif.rst_n, item.rst_n, vif.enable, item.enable),
        UVM_LOW)

      seq_item_port.item_done();
    end
  endtask
endclass
```

### 10.4.2 런타임 컴포넌트 교환 패턴

Ch.4의 `set_type_override_by_type`을 사용하여 **코드 변경 없이** 디버그 드라이버로 교체합니다:

```systemverilog
// ──────────────────────────────────────────
// Factory Override로 디버그 드라이버 교체
// 파일: counter_factory_debug_test.sv
// 역할: 기존 드라이버를 디버그 버전으로 교체하여 문제 분석
// ──────────────────────────────────────────
class counter_factory_debug_test extends counter_base_test;
  `uvm_component_utils(counter_factory_debug_test)

  function new(string name, uvm_component parent);
    super.new(name, parent);
  endfunction

  function void build_phase(uvm_phase phase);
    // ── Factory Override 설정 (build_phase 맨 처음!) ──
    // counter_driver → counter_debug_driver로 교체
    // Ch.4에서 배운 패턴: 원본 타입 → 교체 타입
    set_type_override_by_type(
      counter_driver::get_type(),        // 원본
      counter_debug_driver::get_type()   // 교체
    );

    `uvm_info(get_type_name(),
      "Factory Override: counter_driver → counter_debug_driver", UVM_NONE)

    // super.build_phase에서 env를 생성할 때,
    // counter_driver::type_id::create()가 자동으로
    // counter_debug_driver를 생성합니다!
    super.build_phase(phase);
  endfunction

  task run_phase(uvm_phase phase);
    // Ch.9의 coverage_closure_test와 동일한 시퀀스 실행
    counter_rst_with_en_seq rst_seq;

    phase.raise_objection(this);

    // 리셋
    reset_dut();

    // MISMATCH가 발생하는 시퀀스 실행
    rst_seq = counter_rst_with_en_seq::type_id::create("rst_seq");
    rst_seq.start(env.agent.sequencer);

    phase.drop_objection(this);
  endtask
endclass
```

**Factory Override 동작 원리 (Ch.4 복습):**

```
[build_phase 시작]
     │
     ▼
set_type_override_by_type(counter_driver, counter_debug_driver)
     │
     ▼
super.build_phase → counter_env::build_phase
     │
     ▼
counter_agent::build_phase
     │
     ▼
counter_driver::type_id::create("driver", this)
     │
     ▼  Factory가 override 테이블 확인
     │
     ▼
counter_debug_driver 인스턴스 생성! (counter_driver 대신)
```

**핵심 포인트:**
- `set_type_override_by_type`은 **반드시** `super.build_phase` 호출 **전에** 설정해야 합니다
- 기존 `counter_env`, `counter_agent` 코드는 **전혀 수정하지 않습니다**
- Ch.4에서 배운 것처럼, Factory에 등록된(`uvm_component_utils`) 모든 컴포넌트를 이 방식으로 교체 가능합니다

### 10.4.3 실전: 드라이버 vs 모니터 문제 분리

MISMATCH가 발생했을 때, 원인이 어디에 있는지 분리하는 것이 중요합니다:

- **드라이버 문제**: 시퀀스가 원하는 값을 인터페이스에 제대로 전달하지 못함
- **모니터 문제**: 인터페이스의 값을 잘못 샘플링하여 스코어보드에 틀린 정보 전달
- **RTL 버그**: 드라이버와 모니터 모두 정상이지만 DUT 자체에 버그

**문제 분리 체크리스트:**

```
[단계 1] 디버그 드라이버 교체 (Factory Override)
    └─ 드라이버가 인터페이스에 전달한 값 확인
    └─ 값이 시퀀스 아이템과 다르면 → 드라이버 버그

[단계 2] 디버그 모니터 교체 (Factory Override)
    └─ 모니터가 샘플링한 값 확인
    └─ 파형의 실제 값과 다르면 → 모니터 버그 (샘플 타이밍)

[단계 3] 드라이버, 모니터 모두 정상이면
    └─ 파형에서 DUT 내부 신호 확인
    └─ RTL 로직 검토 → RTL 버그
```

우리의 4비트 카운터 예제에서는:
1. 디버그 드라이버: `rst_n=0`, `enable=1` 정상 전달 ✅
2. 모니터: `count=5` 정확히 샘플링 ✅
3. → **RTL 버그** 확정: 리셋 우선순위 오류

> 💡 **실무 팁**: 팹리스 회사에서 검증 엔지니어는 RTL을 직접 수정하지 않습니다. 대신 **버그 리포트**를 작성하여 설계 엔지니어에게 전달합니다. 리포트에는 "언제, 어떤 입력에서, 예상값과 실제값이 어떻게 다른지"를 명확히 기록합니다.

---

## 10.5 흔한 UVM 에러 메시지 해석

> **이 절의 목표**: 실무에서 자주 만나는 UVM 에러 메시지를 즉시 해석하고 원인을 파악하는 능력을 기릅니다.

UVM을 사용하면서 자주 만나는 에러 메시지들입니다. 에러 메시지를 보고 즉시 원인을 파악할 수 있으면 디버깅 시간이 크게 줄어듭니다.

### 10.5.1 연결 에러 — "port is not connected"

```
UVM_FATAL @ 0ns: uvm_test_top.env.agent.driver.seq_item_port
  [CONNECTION] port is not connected
```

**원인**: `connect_phase`에서 포트 연결을 빠뜨렸습니다.

**해결:**

```systemverilog
// ❌ 연결 누락
function void connect_phase(uvm_phase phase);
  // driver.seq_item_port 연결을 잊음!
endfunction

// ✅ 올바른 연결
function void connect_phase(uvm_phase phase);
  driver.seq_item_port.connect(sequencer.seq_item_export);
endfunction
```

**확인 방법**: `connect_phase`에서 모든 포트가 연결되었는지 검토합니다. 특히 `analysis_port`, `seq_item_port`, `analysis_imp` 등을 확인하세요.

### 10.5.2 Factory 에러 — "create failed"

```
UVM_FATAL @ 0ns: reporter [FCTTYP] Factory create failed.
  No type registered with name 'counter_driver'
```

**원인**: `uvm_component_utils` 또는 `uvm_object_utils` 매크로를 빠뜨렸습니다.

**해결:**

```systemverilog
// ❌ Factory 등록 누락
class counter_driver extends uvm_driver #(counter_seq_item);
  // `uvm_component_utils(counter_driver)  ← 이 줄이 없음!
endclass

// ✅ Factory 등록 포함
class counter_driver extends uvm_driver #(counter_seq_item);
  `uvm_component_utils(counter_driver)   // ← 필수!
endclass
```

**확인 방법**: 에러 메시지의 클래스 이름을 찾아 `uvm_component_utils` (컴포넌트) 또는 `uvm_object_utils` (트랜잭션/시퀀스)가 있는지 확인합니다.

### 10.5.3 Phase 에러 — "objection raised but not dropped"

```
UVM_FATAL @ 100000ns: reporter [OBJTN]
  'uvm_test_top' raised 1 objection(s) but failed to drop them
```

**원인**: `raise_objection`은 했지만 `drop_objection`을 하지 않아 시뮬레이션이 끝나지 않습니다. (타임아웃 후 FATAL)

**해결:**

```systemverilog
// ❌ drop_objection 누락
task run_phase(uvm_phase phase);
  phase.raise_objection(this);
  // ... 시퀀스 실행 ...
  // phase.drop_objection(this);  ← 빠짐!
endtask

// ✅ 올바른 objection 관리
task run_phase(uvm_phase phase);
  phase.raise_objection(this);
  // ... 시퀀스 실행 ...
  phase.drop_objection(this);   // ← 반드시 짝 맞추기!
endtask
```

**확인 방법**: `raise_objection`과 `drop_objection`이 항상 짝을 이루는지, 특히 `if`문이나 `fork` 안에서 한쪽만 실행되는 경로가 없는지 확인합니다.

### 10.5.4 Randomization 에러 — "randomize() failed"

```
UVM_WARNING @ 50ns: reporter [RNDFLD]
  Randomization failed for counter_seq_item. Check constraints.
```

**원인**: `constraint`끼리 모순이 있어서 만족하는 값이 없습니다.

**해결:**

```systemverilog
// ❌ 모순되는 constraint
class counter_seq_item extends uvm_sequence_item;
  rand bit rst_n;
  rand bit enable;

  constraint c1 { rst_n == 1; }
  constraint c2 { rst_n == 0; }  // c1과 모순!
endclass

// ✅ constraint 검토 후 수정
class counter_seq_item extends uvm_sequence_item;
  rand bit rst_n;
  rand bit enable;

  constraint c_normal {
    rst_n dist {0 := 10, 1 := 90};  // 모순 없는 분포
  }
endclass
```

**확인 방법**: `randomize()` 호출 시 반환값을 체크합니다:

```systemverilog
// 안전한 randomization 패턴
if (!item.randomize())
  `uvm_error("SEQ", "randomize() 실패 — constraint 확인 필요")
```

### 10.5.5 Config DB 에러 — "config_db::get failed"

```
UVM_FATAL @ 0ns: uvm_test_top.env.agent.driver [CFGDB]
  config_db::get failed for 'vif'
```

**원인**: `uvm_config_db#(...)::set`과 `::get`의 경로나 키 이름이 불일치합니다.

**해결:**

```systemverilog
// ── tb_top.sv에서 set ──
initial begin
  uvm_config_db#(virtual counter_if)::set(
    null,              // context
    "uvm_test_top.*",  // scope (와일드카드)
    "vif",             // 키 이름
    counter_intf       // 값
  );
end

// ── driver에서 get ──
function void build_phase(uvm_phase phase);
  if (!uvm_config_db#(virtual counter_if)::get(
    this,    // context
    "",      // scope
    "vif",   // 키 이름 — set과 동일해야 함!
    vif      // 변수
  ))
    `uvm_fatal(get_type_name(), "config_db::get failed for 'vif'")
endfunction
```

**흔한 실수 3가지:**
1. `set`의 키가 `"vif"`인데 `get`에서 `"v_if"`로 **오타**
2. `set`의 scope가 `"uvm_test_top.env.*"`인데 컴포넌트 **경로가 맞지 않음**
3. `set`의 타입이 `virtual counter_if`인데 `get`에서 **다른 인터페이스 타입** 사용

### 10.5.6 에러 메시지 빠른 참조 표

| 에러 메시지 | 원인 | 확인 위치 | 해결 방법 |
|-------------|------|-----------|-----------|
| `port is not connected` | 포트 연결 누락 | `connect_phase` | 포트 연결 추가 |
| `create failed` | Factory 등록 누락 | 클래스 선언부 | `uvm_component_utils` 추가 |
| `objection raised but not dropped` | drop 누락 | `run_phase` | `drop_objection` 추가 |
| `randomize() failed` | constraint 모순 | constraint 블록 | constraint 검토/수정 |
| `config_db::get failed` | set/get 불일치 | `tb_top`, `build_phase` | 키 이름, 경로, 타입 확인 |
| `sequence not started` | start() 누락 | `run_phase` | `seq.start(sequencer)` 호출 |
| `null object access` | create() 누락 | `build_phase` | `type_id::create()` 확인 |
| `duplicate port name` | 같은 이름 포트 중복 | `build_phase` | 포트 이름 변경 |
| `type mismatch` | 타입 불일치 | `analysis_imp` 선언 | 파라미터 타입 확인 |
| `phase timeout` | 시뮬레이션 무한 루프 | `run_phase` | 종료 조건 확인 |

> 💡 **실무 팁**: 이 표를 프린트해서 책상에 두세요. 초보 시절에는 이 에러들을 반복적으로 만나게 됩니다. 시간이 지나면 에러 메시지를 보는 즉시 원인을 파악할 수 있게 됩니다.

**`uvm_report_catcher` — 고급 참고:**

UVM은 `uvm_report_catcher`라는 고급 기능도 제공합니다. 특정 에러 메시지를 프로그래밍적으로 필터링하거나 심각도를 변경할 수 있습니다. 예를 들어, 의도적으로 에러를 주입하는 테스트에서 예상된 `UVM_ERROR`를 `UVM_INFO`로 다운그레이드할 수 있습니다. 이 기능은 Part 3에서 자세히 다룹니다.

---

## 10.6 실전: MISMATCH 원인 찾기

> **이 절의 목표**: 지금까지 배운 모든 디버깅 기법을 종합하여, 의도적 버그가 주입된 DUT에서 MISMATCH 원인을 찾는 **전체 과정**을 단계별로 경험합니다.

### 10.6.1 시나리오 — 의도적 버그 주입

**DUT**: 4비트 카운터 (Ch.5~Ch.10 시리즈)
**버그**: 리셋 우선순위 오류 — `rst_n=0`이면서 `enable=1`일 때 리셋이 무시됨

```systemverilog
// ──────────────────────────────────────────
// 버그가 있는 4비트 카운터 RTL
// 파일: counter_bug.sv
// 버그: enable이 rst_n보다 우선순위가 높음
// ──────────────────────────────────────────
module counter_4bit (
  input  logic       clk,
  input  logic       rst_n,    // 액티브 로우 리셋
  input  logic       enable,   // 카운트 인에이블
  output logic [3:0] count     // 4비트 카운터 출력
);

  always_ff @(posedge clk) begin
    if (enable)          // ❌ 버그: enable을 먼저 검사
      count <= count + 1;
    else if (!rst_n)     // ❌ 버그: 리셋이 나중에 검사됨
      count <= 4'b0;
    else
      count <= count;    // hold
  end

endmodule
```

**테스트**: Ch.9의 `counter_coverage_closure_test` 실행

### 10.6.2 단계별 디버깅 프로세스

**[1단계] 시뮬레이션 실행 — MISMATCH 발견**

```bash
# Ch.9의 커버리지 클로저 테스트 실행
vsim +UVM_TESTNAME=counter_coverage_closure_test
```

실행 결과:

```
UVM_INFO @ 0ns: reporter [RNTST] Running test counter_coverage_closure_test...
UVM_INFO @ 10ns: uvm_test_top [counter_coverage_closure_test] === 테스트 시작 ===
UVM_INFO @ 10ns: uvm_test_top [counter_coverage_closure_test] 1단계: DUT 리셋
UVM_INFO @ 50ns: uvm_test_top [counter_coverage_closure_test] 2단계: 타겟 시퀀스 시작

UVM_ERROR @ 850ns: uvm_test_top.env.scoreboard [counter_scoreboard]
  MISMATCH! expected=0, actual=5 (rst_n=0, enable=1)
UVM_ERROR @ 870ns: uvm_test_top.env.scoreboard [counter_scoreboard]
  MISMATCH! expected=0, actual=6 (rst_n=0, enable=1)
UVM_ERROR @ 890ns: uvm_test_top.env.scoreboard [counter_scoreboard]
  MISMATCH! expected=0, actual=7 (rst_n=0, enable=1)

...

--- UVM Report Summary ---
** Report counts by severity
UVM_INFO :   45
UVM_WARNING :    0
UVM_ERROR :    5    ← MISMATCH 5건!
UVM_FATAL :    0
```

**발견**: `rst_n=0, enable=1` 조합에서 MISMATCH가 5건 발생했습니다. Ch.9에서 추가한 `counter_rst_with_en_seq` (타겟 시퀀스)가 이 조합을 테스트하는 시퀀스였습니다.

**[2단계] Verbosity 올리기 — 상세 로그 확인**

```bash
# 스코어보드의 verbosity를 HIGH로 올려 재실행
vsim +UVM_TESTNAME=counter_coverage_closure_test \
     +uvm_set_verbosity=*scoreboard*,_ALL_,UVM_HIGH,run
```

```
UVM_INFO @ 830ns: uvm_test_top.env.scoreboard [counter_scoreboard]
  트랜잭션 #41: predict(1, 1, 11) → expected=12, actual=12 ✓ MATCH

UVM_INFO @ 850ns: uvm_test_top.env.scoreboard [counter_scoreboard]
  트랜잭션 #42: predict(0, 1, 12) → expected=0
UVM_INFO @ 850ns: uvm_test_top.env.scoreboard [counter_scoreboard]
  DUT 실제값: count=5
UVM_ERROR @ 850ns: uvm_test_top.env.scoreboard [counter_scoreboard]
  MISMATCH! expected=0, actual=5 (rst_n=0, enable=1)
```

**분석**: 트랜잭션 #41까지는 정상(MATCH). 트랜잭션 #42에서 `rst_n`이 0으로 변경되었고, 레퍼런스 모델은 `count=0`을 예측했지만 DUT는 `count=5`를 출력했습니다.

**[3단계] Factory Override — 디버그 드라이버 교체**

```bash
# 디버그 테스트로 재실행
vsim +UVM_TESTNAME=counter_factory_debug_test
```

```
UVM_INFO @ 0ns: uvm_test_top [counter_factory_debug_test]
  Factory Override: counter_driver → counter_debug_driver

UVM_INFO @ 0ns: uvm_test_top.env.agent.driver [counter_debug_driver]
  === 디버그 드라이버 활성화 ===

UVM_INFO @ 840ns: uvm_test_top.env.agent.driver [counter_debug_driver]
  [840ns] 전송 전: vif.rst_n=1, vif.enable=1, vif.count=12
UVM_INFO @ 845ns: uvm_test_top.env.agent.driver [counter_debug_driver]
  [845ns] 전송 후: rst_n=1→0, enable=1→1

UVM_ERROR @ 850ns: uvm_test_top.env.scoreboard [counter_scoreboard]
  MISMATCH! expected=0, actual=5 (rst_n=0, enable=1)
```

**분석**: 디버그 드라이버가 확인한 바로는, `rst_n=0`이 845ns에 인터페이스에 정상 전달되었습니다. 드라이버는 정상입니다.

**[4단계] 파형 확인 — RTL 내부 분석**

GTKWave에서 `counter_debug.vcd`를 열고 850ns 시점으로 이동:

```
시간   | clk | rst_n | enable | count | 분석
───────┼─────┼───────┼────────┼───────┼──────────────
830ns  |  ↑  |   1   |   1    |  12   | 정상 카운팅
840ns  |  ↑  |   1   |   1    |  13   |
845ns  |     |   0   |   1    |  13   | rst_n↓ (클록 에지 사이)
850ns  |  ↑  |   0   |   1    |   5   | ❌ 0이어야 하는데!
855ns  |  ↑  |   0   |   1    |   6   | ❌ 여전히 카운팅
860ns  |  ↑  |   0   |   0    |   0   | enable=0이 되어야 리셋
```

**발견**: `rst_n=0`이면서 `enable=1`일 때, 카운터가 리셋되지 않고 계속 카운팅합니다. `enable=0`이 되어야 비로소 리셋이 적용됩니다.

### 10.6.3 원인 발견 및 수정

**버그 원인**: RTL의 `if-else` 우선순위

```systemverilog
// ── 버그 있는 코드 ──
always_ff @(posedge clk) begin
  if (enable)          // ← enable이 최우선 → 리셋 무시!
    count <= count + 1;
  else if (!rst_n)     // ← enable=0일 때만 리셋 검사
    count <= 4'b0;
end
```

**수정:**

```systemverilog
// ── 수정된 코드 ──
always_ff @(posedge clk) begin
  if (!rst_n)          // ✅ 리셋이 최우선
    count <= 4'b0;
  else if (enable)     // ✅ 리셋 아닐 때만 카운팅
    count <= count + 1;
end
```

**버그 리포트 예시:**

실무에서 검증 엔지니어가 설계 엔지니어에게 전달하는 버그 리포트입니다:

| 항목 | 내용 |
|------|------|
| **제목** | 4비트 카운터 리셋 우선순위 오류 |
| **심각도** | High |
| **발견 테스트** | `counter_coverage_closure_test` (`rst_with_en_seq` 실행 중) |
| **증상** | `rst_n=0`, `enable=1`일 때 count가 0으로 리셋되지 않고 계속 증가 |
| **원인** | `always_ff` 블록에서 enable 조건이 rst_n보다 먼저 평가됨 |
| **수정 제안** | `if(!rst_n)` 조건을 `if(enable)` 앞으로 이동 |
| **재현** | seed=12345, 트랜잭션 #42 시점 (850ns) |

### 10.6.4 수정 검증 — regression 확인

수정 후에는 **반드시** regression을 실행하여 다른 테스트에 영향이 없는지 확인합니다.

```bash
# ── 수정 검증 regression ──

# 1. 문제가 발생했던 테스트 재실행
vsim +UVM_TESTNAME=counter_coverage_closure_test +ntb_random_seed=12345
# → 결과: PASS (MISMATCH 0건)

# 2. 모든 테스트 regression
vsim +UVM_TESTNAME=counter_reset_test +ntb_random_seed=12345
# → 결과: PASS

vsim +UVM_TESTNAME=counter_random_test +ntb_random_seed=12345
# → 결과: PASS

vsim +UVM_TESTNAME=counter_random_test +ntb_random_seed=67890
# → 결과: PASS

vsim +UVM_TESTNAME=counter_coverage_closure_test +ntb_random_seed=67890
# → 결과: PASS
```

**Regression 결과 요약:**

```
┌──────────────────────────────────┬────────┬──────────┐
│ 테스트                            │ Seed   │ 결과     │
├──────────────────────────────────┼────────┼──────────┤
│ counter_reset_test               │ 12345  │ ✅ PASS  │
│ counter_random_test              │ 12345  │ ✅ PASS  │
│ counter_random_test              │ 67890  │ ✅ PASS  │
│ counter_coverage_closure_test    │ 12345  │ ✅ PASS  │
│ counter_coverage_closure_test    │ 67890  │ ✅ PASS  │
├──────────────────────────────────┼────────┼──────────┤
│ 전체                              │        │ 5/5 PASS │
└──────────────────────────────────┴────────┴──────────┘
```

모든 테스트가 PASS했습니다. 버그 수정이 확인되었고, 기존 기능에 영향을 주지 않았습니다.

> 💡 **실무 팁**: regression은 수정 후 반드시 실행해야 합니다. "한 줄만 고쳤으니 괜찮겠지"라는 생각은 금물입니다. 실무에서는 하루에도 수십 개의 수정이 발생하며, regression이 이를 지켜줍니다. Ch.9에서 배운 seed 관리와 regression 스크립트가 여기서 빛을 발합니다.

---

## 10.7 체크포인트

> **이 절의 목표**: 이 챕터의 핵심 개념을 확인하고, Part 2 전체를 마무리합니다.

### 10.7.1 셀프 체크

다음 질문에 답할 수 있으면 이 챕터의 핵심을 이해한 것입니다:

**1. `$display` 대신 `uvm_info`를 사용하는 가장 큰 장점은?** (10.2)

<details>
<summary>정답 확인</summary>
verbosity 제어로 코드 수정 없이 메시지를 끄고 켤 수 있습니다. 명령줄 `+UVM_VERBOSITY`나 `set_report_verbosity_level()`로 심각도와 상세도를 런타임에 조절할 수 있어, 디버그 메시지를 삭제하지 않고도 깨끗한 로그를 얻을 수 있습니다.
</details>

**2. `UVM_ERROR`와 `UVM_FATAL`의 차이는?** (10.2)

<details>
<summary>정답 확인</summary>
`UVM_ERROR`는 에러 카운트만 증가시키고 시뮬레이션은 계속됩니다. 여러 MISMATCH를 한 번에 수집할 수 있습니다. `UVM_FATAL`은 시뮬레이션을 즉시 중단합니다. 복구 불가능한 설정 오류(config_db 실패, 포트 미연결)에 사용합니다.
</details>

**3. Verbosity를 전체가 아닌 특정 컴포넌트만 올리는 방법 2가지는?** (10.2)

<details>
<summary>정답 확인</summary>
① 코드에서: `env.scoreboard.set_report_verbosity_level(UVM_DEBUG)` — build_phase나 connect_phase에서 특정 컴포넌트 인스턴스의 메서드를 호출합니다. ② 명령줄에서: `+uvm_set_verbosity=uvm_test_top.env.scoreboard,_ALL_,UVM_DEBUG,run` — 코드 수정 없이 실행 시 설정합니다.
</details>

**4. MISMATCH 로그의 타임스탬프를 파형에서 어떻게 활용하나요?** (10.3)

<details>
<summary>정답 확인</summary>
파형 뷰어의 "Jump to Time" 기능으로 해당 시점으로 이동하여 RTL 신호를 확인합니다. 예: 로그에서 `@ 850ns`를 확인하면, GTKWave에서 850ns로 점프하여 clk, rst_n, enable, count 신호의 실제 값을 확인합니다.
</details>

**5. Factory Override로 디버그 드라이버를 교체할 때, 기존 코드를 수정해야 하나요?** (10.4)

<details>
<summary>정답 확인</summary>
아닙니다. `set_type_override_by_type(counter_driver::get_type(), counter_debug_driver::get_type())`을 테스트의 `build_phase`에서 `super.build_phase` 호출 전에 설정하면, 기존 env/agent 코드 변경 없이 교체됩니다. Factory가 `type_id::create()` 호출 시 자동으로 override 테이블을 참조합니다.
</details>

**6. "config_db::get failed" 에러의 가장 흔한 원인 3가지는?** (10.5)

<details>
<summary>정답 확인</summary>
① 키 이름 오타 — `set`에서 `"vif"`, `get`에서 `"v_if"` 등 ② scope 경로 불일치 — `set`의 `"uvm_test_top.env.*"`와 실제 컴포넌트 계층이 맞지 않음 ③ 타입 불일치 — `set`과 `get`의 파라미터 타입이 다름 (예: `virtual counter_if` vs `virtual other_if`)
</details>

### 10.7.2 연습문제

**연습 10-1 (기본)**: 디버그 모니터 작성

`counter_monitor`를 상속한 `counter_debug_monitor`를 작성하세요. 매 샘플링마다 타임스탬프와 인터페이스 전체 상태를 `UVM_LOW`로 출력해야 합니다. Factory Override로 교체하여 테스트하세요.

<details>
<summary>힌트</summary>

```systemverilog
class counter_debug_monitor extends counter_monitor;
  `uvm_component_utils(counter_debug_monitor)
  // run_phase를 override하여 상세 로깅 추가
  // 샘플링 시 $sformatf("[%0t] ...", $time, ...) 형식 사용
  // Factory Override: set_type_override_by_type(
  //   counter_monitor::get_type(),
  //   counter_debug_monitor::get_type())
endclass
```
</details>

**연습 10-2 (중급)**: 다른 버그 찾기

다음 RTL에 숨겨진 버그를 UVM 디버깅 워크플로우 5단계를 따라 찾으세요:

```systemverilog
// 버그가 숨겨진 카운터
always_ff @(posedge clk) begin
  if (!rst_n)
    count <= 4'b0;
  else if (enable)
    count <= count + 2;    // ← 이 줄을 주의 깊게 보세요
end
```

<details>
<summary>힌트</summary>
증가값이 `+1`이 아닌 `+2`입니다. 레퍼런스 모델은 `count+1`을 예측하므로 enable=1인 모든 트랜잭션에서 MISMATCH가 발생합니다. 파형에서 count 값이 0, 2, 4, 6... 으로 증가하는 것을 확인할 수 있습니다.
</details>

**연습 10-3 (도전)**: Verbosity 전략 설계

다음 상황에서 어떤 verbosity 전략을 사용할지 설계하세요:
- 시뮬레이션에서 100만 트랜잭션 중 3건의 MISMATCH 발생
- 모든 MISMATCH가 트랜잭션 #500,000 이후에 집중
- 전체 verbosity를 DEBUG로 올리면 로그가 50GB

<details>
<summary>힌트</summary>
① 먼저 기본 verbosity로 실행하여 MISMATCH 시점(타임스탬프)을 확인합니다. ② 해당 시점 전후만 상세 로그가 필요하므로, 컴포넌트별 verbosity를 사용합니다. ③ 또는 코드에서 특정 트랜잭션 번호 이후에만 verbosity를 올리는 조건부 로직을 추가합니다: `if (transaction_count > 499990) set_report_verbosity_level(UVM_DEBUG);`
</details>

### 10.7.3 Part 2 마무리 & Part 3 미리보기

**Part 2 (Chapter 5~10)에서 배운 것:**

Chapter 5부터 10까지, 우리는 4비트 카운터 하나로 UVM 검증의 **핵심 사이클**을 완성했습니다:

| 챕터 | 주제 | 핵심 성과 |
|------|------|-----------|
| **Ch.5** | 첫 UVM 테스트벤치 | 하드코딩 시퀀스로 기본 구조 구축 |
| **Ch.6** | 시퀀스와 트랜잭션 | 랜덤 시퀀스로 자동화된 테스트 입력 |
| **Ch.7** | 에이전트 구조 | 드라이버-모니터-시퀀서 컴포넌트 분리 |
| **Ch.8** | 스코어보드와 커버리지 | 자동 비교(87.5%)와 측정 체계 |
| **Ch.9** | 테스트 시나리오 | CDV 워크플로우로 97.2% 달성 |
| **Ch.10** | 디버깅 기법 | MISMATCH → 원인 → 수정 → 검증 |

이 6개 챕터가 **검증 엔지니어의 일상 업무**입니다:
1. 테스트벤치를 만들고 (Ch.5~7)
2. 자동으로 검증하고 (Ch.8)
3. 커버리지를 채우고 (Ch.9)
4. 버그를 찾아 보고합니다 (Ch.10)

**Part 3 미리보기 (Chapter 11~15):**

Part 3에서는 4비트 카운터를 졸업하고, **실무 수준의 프로토콜**로 넘어갑니다:

| 챕터 | 주제 | 예고 |
|------|------|------|
| **Ch.11** | 인터페이스와 BFM | 실무 프로토콜 인터페이스 설계 |
| **Ch.12** | 레지스터 모델 | UVM RAL로 레지스터 자동 검증 |
| **Ch.13** | 가상 시퀀스 | 다중 에이전트 협업 시나리오 |
| **Ch.14** | 환경 통합 | SoC 레벨 검증 환경 구축 |
| **Ch.15** | 실전 프로젝트 | 취업 포트폴리오 프로젝트 완성 |

Part 2에서 배운 모든 기법 — 시퀀스, 스코어보드, 커버리지, 디버깅 — 이 Part 3에서 더 복잡한 프로토콜에 그대로 적용됩니다. **기초가 탄탄하면 확장은 자연스럽습니다.**

**Part 2에서 완성한 4비트 카운터 검증 환경:**

6개 챕터에 걸쳐 구축한 검증 환경의 최종 모습입니다:

- **DUT**: 4비트 카운터 (`counter_4bit`) — 3입력(clk, rst_n, enable), 1출력(count)
- **인터페이스**: `counter_if` — DUT와 테스트벤치를 연결하는 virtual interface
- **에이전트**: `counter_agent` — 드라이버, 모니터, 시퀀서를 하나로 묶은 재사용 단위
- **시퀀스**: 타겟(rst_with_en, max_hold), 랜덤(random), 에러 주입(rapid_reset, boundary) — 5가지
- **스코어보드**: `counter_scoreboard` — Reference Model 기반 자동 비교, MISMATCH 보고
- **커버리지**: `counter_coverage` — coverpoint 3개 + cross 2개, 97.2% 달성
- **테스트**: `counter_base_test` → reset/random/coverage_closure 3개 파생 테스트
- **디버깅**: verbosity 제어, Factory Override, 파형 분석, 버그 리포트 작성

이 환경은 규모만 다를 뿐, 실무의 SoC 검증 환경과 **동일한 구조**입니다. Part 3에서는 이 구조를 더 복잡한 프로토콜에 확장합니다.

### 다음 장 미리보기

Chapter 11에서는 4비트 카운터를 졸업하고, **실제 프로토콜 인터페이스**를 다룹니다. Virtual Interface의 실무 활용법과 Bus Functional Model(BFM) 패턴을 배웁니다. Part 2에서 다진 기초 위에 실무 역량을 쌓아가겠습니다.
