# Chapter 8: 스코어보드 & 커버리지

> **이 챕터의 목표**: 스코어보드로 DUT 출력을 **자동 검증**하고, 기능 커버리지로 검증 **완전성**을 측정합니다. 눈으로 파형을 보는 시대는 끝났습니다.

> **선수 지식**: Chapter 7 (analysis port, TLM 포트, 모니터 브로드캐스트)

---

## 8.1 왜 자동 검증이 필요한가

> **이 절의 목표**: 수동 검증의 한계를 이해하고, 스코어보드와 커버리지가 해결하는 문제를 파악합니다.

### 8.1.1 수동 검증의 한계 — 눈으로 확인하는 검증

Chapter 7까지 우리는 모니터가 수집한 데이터를 `uvm_info`로 출력만 했습니다. 검증은 어떻게 했나요?

```
[시뮬레이션 실행]
    ↓
[파형 뷰어에서 눈으로 확인]
    ↓
[맞는 것 같으면... PASS?]
```

이 방법의 문제점:

| 문제 | 설명 |
|------|------|
| **확장 불가** | 신호 100개, 트랜잭션 10,000개를 눈으로? |
| **실수 가능** | 사람은 피곤하면 오류를 놓침 |
| **재현 불가** | "저번에 봤을 때 맞았는데..." |
| **정량화 불가** | "충분히 테스트했나?" → 감으로 판단 |

> **실무 이야기**: 팹리스에서 칩을 테이프아웃하기 전, "검증이 충분한가?"라는 질문에 "파형 봤는데 괜찮아 보여요"라고 답하면 바로 탈락입니다. **자동 검증** + **정량적 커버리지 목표**가 필수입니다.

### 8.1.2 스코어보드 — 자동 채점기

시험에 비유하면:

| 시험 | 검증 |
|------|------|
| 시험지 | 테스트 시나리오 (시퀀스) |
| 학생 답안 | DUT 출력 (모니터가 관찰) |
| **정답지** | **Reference Model (스코어보드 내부)** |
| **채점관** | **스코어보드** |

스코어보드는 **정답지(Reference Model)**를 갖고 있고, 모니터가 전달한 **학생 답안(DUT 출력)**을 자동으로 비교합니다. 틀리면 즉시 에러를 보고합니다.

### 8.1.3 커버리지 — 시험 범위 체크리스트

시험을 잘 봤다고 끝이 아닙니다. "이 시험이 모든 범위를 커버했는가?"도 중요합니다.

| 체크리스트 항목 | 검증 대응 |
|----------------|----------|
| 1장 출제했나? | reset 시나리오 테스트했나? |
| 2장 출제했나? | overflow 시나리오 테스트했나? |
| 1+2장 복합? | reset 후 overflow 테스트했나? |
| **커버율** | **기능 커버리지 퍼센트** |

### 8.1.4 검증 자동화 전체 구조

```
┌─────────────────────────────────────────────────────┐
│                   자동 검증 구조                      │
│                                                      │
│     ┌──────────┐     ┌──────────────────────┐       │
│     │ Sequence │     │     Environment      │       │
│     └────┬─────┘     │                      │       │
│          ↓           │  ┌──────────────┐    │       │
│     ┌──────────┐     │  │  Scoreboard  │    │       │
│     │Sequencer │     │  │  (자동 채점)  │    │       │
│     └────┬─────┘     │  └──────▲───────┘    │       │
│          ↓           │         │             │       │
│     ┌──────────┐     │  ┌──────┴───────┐    │       │
│     │  Driver  ├────►│  │   Monitor    │    │       │
│     └────┬─────┘     │  └──────┬───────┘    │       │
│          │           │         │             │       │
│          │           │  ┌──────▼───────┐    │       │
│          │           │  │  Coverage    │    │       │
│          │           │  │  (범위 측정)  │    │       │
│     ┌────▼─────┐     │  └──────────────┘    │       │
│     │   DUT    │     │                      │       │
│     └──────────┘     └──────────────────────┘       │
└─────────────────────────────────────────────────────┘
```

**핵심 포인트**: 모니터의 `analysis_port.write()`가 스코어보드와 커버리지 수집기 **둘 다**에게 동시에 트랜잭션을 전달합니다. Ch.7에서 배운 1:N 브로드캐스트의 실전 활용입니다!

---

## 8.2 스코어보드 기초

> **이 절의 목표**: `uvm_scoreboard`와 `uvm_analysis_imp`를 사용해 자동 검증 스코어보드를 구현합니다.

### 8.2.1 Reference Model — 정답지 만들기

스코어보드가 DUT 출력을 검증하려면 "정답"을 알아야 합니다. 이 정답을 만드는 것이 **Reference Model**입니다.

**우리의 4비트 카운터 DUT 동작 규칙:**
- `rst_n == 0` → count = 0 (리셋)
- `enable == 1` → count = count + 1 (증가)
- `enable == 0` → count 유지 (정지)
- count가 15(4'hF)를 넘으면 → 0으로 돌아감 (오버플로우)

이 규칙을 SystemVerilog 함수로 구현하면 Reference Model이 됩니다:

```systemverilog
// Reference Model — 소프트웨어로 DUT 동작을 예측
function logic [3:0] predict_count(
    logic       rst_n,
    logic       enable,
    logic [3:0] current_count
);
  if (!rst_n)
    return 4'h0;                    // 리셋
  else if (enable)
    return current_count + 1;       // 증가 (자동 오버플로우)
  else
    return current_count;           // 유지
endfunction
```

> **왜 Reference Model이 필요한가?** DUT는 하드웨어(RTL)로 구현됩니다. 같은 기능을 **소프트웨어**로 별도 구현해서 결과를 비교하면, 두 구현이 독립적이므로 동일한 버그를 만들 확률이 매우 낮습니다.

### 8.2.2 uvm_scoreboard 와 uvm_analysis_imp

Ch.7에서 스코어보드 코드를 프리뷰했습니다. 이제 본격적으로 구조를 이해합니다.

**스코어보드의 3가지 핵심 요소:**

| 요소 | 역할 | UVM 클래스 |
|------|------|-----------|
| 기본 클래스 | 스코어보드 뼈대 | `uvm_scoreboard` |
| 수신 포트 | 모니터에서 트랜잭션 받기 | `uvm_analysis_imp` |
| 검증 함수 | 받은 데이터 비교 | `write()` 메서드 |

**연결 흐름 복습** (Ch.7 → Ch.8):

```
Monitor                    Scoreboard
┌──────────┐              ┌──────────────────┐
│          │   write()    │                  │
│ analysis ├─────────────►│ uvm_analysis_imp │
│ _port    │  자동 호출    │                  │
│          │              │ write() {        │
└──────────┘              │   비교 & 판정    │
                          │ }                │
                          └──────────────────┘
```

### 8.2.3 write() 메서드 — 트랜잭션이 도착하면

`write()` 메서드는 모니터가 `ap.write(item)`을 호출할 때마다 **자동으로** 실행됩니다. 이 안에서 Reference Model로 예측한 값과 실제 DUT 출력을 비교합니다.

```systemverilog
virtual function void write(counter_seq_item item);
  logic [3:0] expected;

  // ⭐ Step 1: Reference Model로 예측
  expected = predict_count(item.rst_n, item.enable, prev_count);

  // ⭐ Step 2: 예측 vs 실제 비교
  if (expected !== item.count) begin
    `uvm_error(get_type_name(),
      $sformatf("MISMATCH! expected=%0d, actual=%0d (rst_n=%0b, enable=%0b)",
                expected, item.count, item.rst_n, item.enable))
    error_count++;
  end else begin
    `uvm_info(get_type_name(),
      $sformatf("MATCH: count=%0d (rst_n=%0b, enable=%0b)",
                item.count, item.rst_n, item.enable), UVM_HIGH)
    match_count++;
  end

  // ⭐ Step 3: 상태 업데이트
  prev_count = expected;
endfunction
```

**핵심 패턴:**
1. **예측(Predict)**: Reference Model로 예상 출력 계산
2. **비교(Compare)**: 예상 출력 ↔ 실제 DUT 출력 비교
3. **보고(Report)**: 일치하면 PASS, 불일치하면 ERROR

> **`uvm_error` vs `uvm_fatal`**: 스코어보드에서 불일치를 발견하면 `uvm_error`를 사용합니다. `uvm_fatal`은 시뮬레이션을 즉시 중단하므로, 여러 오류를 모아서 보고하려면 `uvm_error`가 적합합니다.

### 8.2.4 기본 스코어보드 구현 — 예제 8-1

```systemverilog
// ===== 예제 8-1: 4비트 카운터 스코어보드 =====
class counter_scoreboard extends uvm_scoreboard;
  `uvm_component_utils(counter_scoreboard)

  // ⭐ analysis implementation — 모니터에서 트랜잭션을 받는 포트
  uvm_analysis_imp #(counter_seq_item, counter_scoreboard) ap_imp;

  // 내부 상태
  logic [3:0] prev_count;          // 이전 예측 값
  int         match_count;          // 일치 횟수
  int         error_count;          // 불일치 횟수
  bit         first_transaction;    // 첫 트랜잭션 플래그

  function new(string name, uvm_component parent);
    super.new(name, parent);
  endfunction

  // ─── build_phase: 포트 생성 ───
  virtual function void build_phase(uvm_phase phase);
    super.build_phase(phase);
    ap_imp = new("ap_imp", this);
    prev_count = 4'h0;
    match_count = 0;
    error_count = 0;
    first_transaction = 1;
  endfunction

  // ─── Reference Model ───
  function logic [3:0] predict(
      logic rst_n, logic enable, logic [3:0] current
  );
    if (!rst_n)     return 4'h0;
    else if (enable) return current + 1;
    else             return current;
  endfunction

  // ─── write(): 모니터가 호출 → 자동 실행 ───
  virtual function void write(counter_seq_item item);
    logic [3:0] expected;

    // 첫 트랜잭션은 초기 상태이므로 비교 생략
    if (first_transaction) begin
      prev_count = item.count;
      first_transaction = 0;
      `uvm_info(get_type_name(),
        $sformatf("Initial state: count=%0d", item.count), UVM_MEDIUM)
      return;
    end

    // Step 1: 예측
    expected = predict(item.rst_n, item.enable, prev_count);

    // Step 2: 비교
    if (expected !== item.count) begin
      `uvm_error(get_type_name(),
        $sformatf("MISMATCH! expected=%0d, actual=%0d (rst_n=%0b, en=%0b)",
                  expected, item.count, item.rst_n, item.enable))
      error_count++;
    end else begin
      `uvm_info(get_type_name(),
        $sformatf("MATCH: count=%0d (rst_n=%0b, en=%0b)",
                  item.count, item.rst_n, item.enable), UVM_HIGH)
      match_count++;
    end

    // Step 3: 상태 업데이트
    prev_count = expected;
  endfunction

  // ─── check_phase: 시뮬레이션 종료 후 잔여 검증 ───
  virtual function void check_phase(uvm_phase phase);
    super.check_phase(phase);
    // ⭐ 트랜잭션을 하나도 받지 못했다면 연결 누락 가능성
    if (match_count + error_count == 0)
      `uvm_error(get_type_name(),
        "No transactions received! Check monitor→scoreboard connection.")
  endfunction

  // ─── report_phase: 최종 결과 요약 ───
  virtual function void report_phase(uvm_phase phase);
    super.report_phase(phase);
    `uvm_info(get_type_name(), "===== Scoreboard Summary =====", UVM_LOW)
    `uvm_info(get_type_name(),
      $sformatf("  Total transactions: %0d", match_count + error_count), UVM_LOW)
    `uvm_info(get_type_name(),
      $sformatf("  Matches : %0d", match_count), UVM_LOW)
    `uvm_info(get_type_name(),
      $sformatf("  Errors  : %0d", error_count), UVM_LOW)

    if (error_count > 0)
      `uvm_error(get_type_name(),
        $sformatf("TEST FAILED — %0d mismatches detected!", error_count))
    else
      `uvm_info(get_type_name(), "TEST PASSED — all transactions matched!", UVM_LOW)
  endfunction
endclass
```

**실행 결과 예시:**

```
UVM_INFO  counter_scoreboard: Initial state: count=0
UVM_INFO  counter_scoreboard: MATCH: count=0 (rst_n=0, en=0)
UVM_INFO  counter_scoreboard: MATCH: count=1 (rst_n=1, en=1)
UVM_INFO  counter_scoreboard: MATCH: count=2 (rst_n=1, en=1)
...
UVM_INFO  counter_scoreboard: ===== Scoreboard Summary =====
UVM_INFO  counter_scoreboard:   Total transactions: 30
UVM_INFO  counter_scoreboard:   Matches : 30
UVM_INFO  counter_scoreboard:   Errors  : 0
UVM_INFO  counter_scoreboard: TEST PASSED — all transactions matched!
```

> **면접 포인트**: "스코어보드에서 Reference Model은 어떻게 구현하나요?" — 간단한 DUT는 함수로 직접 구현합니다. 복잡한 프로토콜(PCIe, USB 등)은 C/C++ DPI 모델이나 별도 SystemVerilog 모듈을 사용합니다.

---

## 8.3 스코어보드 심화

> **이 절의 목표**: `uvm_subscriber`로 더 간단하게 스코어보드를 만들고, 실무에서 사용하는 패턴을 학습합니다.

### 8.3.1 uvm_subscriber — 더 간단한 대안

Ch.7에서 `uvm_subscriber`를 잠깐 소개했습니다. `uvm_analysis_imp`를 직접 선언하는 것보다 **훨씬 간단합니다**.

**uvm_analysis_imp (직접 선언) vs uvm_subscriber (내장):**

| 항목 | uvm_analysis_imp | uvm_subscriber |
|------|-----------------|----------------|
| 포트 선언 | 직접 `uvm_analysis_imp` 생성 | 자동 내장 (`analysis_export`) |
| 구현 메서드 | `write()` 직접 구현 | `write()` 직접 구현 (동일) |
| 연결 | `mon.ap.connect(sb.ap_imp)` | `mon.ap.connect(sb.analysis_export)` |
| 코드량 | 많음 | 적음 |
| 다중 포트 | 지원 (여러 imp 선언) | 불가 (포트 1개 고정) |

**uvm_subscriber 버전 스코어보드:**

```systemverilog
class counter_scoreboard_sub extends uvm_subscriber #(counter_seq_item);
  `uvm_component_utils(counter_scoreboard_sub)

  logic [3:0] prev_count;
  int match_count, error_count;
  bit first_transaction = 1;

  function new(string name, uvm_component parent);
    super.new(name, parent);
  endfunction

  // ⭐ uvm_subscriber는 write()만 구현하면 끝!
  //    포트 선언, build_phase에서 포트 생성 — 전부 자동
  virtual function void write(counter_seq_item t);
    logic [3:0] expected;

    if (first_transaction) begin
      prev_count = t.count;
      first_transaction = 0;
      return;
    end

    expected = (!t.rst_n) ? 4'h0 :
               (t.enable) ? prev_count + 1 : prev_count;

    if (expected !== t.count) begin
      `uvm_error(get_type_name(),
        $sformatf("MISMATCH! exp=%0d, act=%0d", expected, t.count))
      error_count++;
    end else
      match_count++;

    prev_count = expected;
  endfunction

  virtual function void report_phase(uvm_phase phase);
    `uvm_info(get_type_name(),
      $sformatf("Results: %0d matches, %0d errors",
                match_count, error_count), UVM_LOW)
  endfunction
endclass
```

> **어떤 것을 사용할까?** 포트가 1개면 `uvm_subscriber`가 간편합니다. 입력과 출력을 **따로** 받아야 하면 `uvm_analysis_imp`를 직접 선언해야 합니다 (8.3.3에서 다룸).

### 8.3.2 예측-비교 분리 패턴

실무에서 복잡한 DUT를 검증할 때는 스코어보드를 **Predictor(예측기)**와 **Comparator(비교기)**로 분리합니다.

```
┌───────────────────────────────────────────────┐
│          예측-비교 분리 패턴                    │
│                                               │
│     입력 Monitor        출력 Monitor           │
│      (자극 관찰)         (결과 관찰)            │
│          │                   │                │
│          ▼                   ▼                │
│    ┌───────────┐      ┌───────────┐           │
│    │ Predictor │      │Comparator │           │
│    │ (예측기)   │─────►│ (비교기)   │           │
│    │ Ref Model │ 예측값│ 예측 vs   │           │
│    └───────────┘      │ 실제 비교  │           │
│                       └───────────┘           │
└───────────────────────────────────────────────┘
```

이 패턴은 Part 3 (Chapter 11+)에서 복잡한 프로토콜 검증 시 다시 다룹니다. 지금은 **"스코어보드를 분리할 수 있다"**는 개념만 기억하세요.

> **왜 분리하나?** Predictor는 입력을 받아 예측만 합니다. Comparator는 예측값과 실제값을 비교만 합니다. 각자의 역할이 명확해 디버깅이 쉽고, Predictor를 다른 프로젝트에 재사용할 수 있습니다.

### 8.3.3 멀티포트 스코어보드

4비트 카운터처럼 간단한 DUT는 모니터 1개로 충분합니다. 하지만 실무에서는 **입력과 출력을 별도 모니터**로 관찰하는 경우가 많습니다.

```
┌─────────────────────────────────────────────────┐
│         멀티포트 스코어보드                        │
│                                                  │
│  입력 Monitor          출력 Monitor               │
│  (자극 관찰)            (결과 관찰)               │
│       │                     │                    │
│       ▼                     ▼                    │
│  ┌──────────────────────────────────────┐        │
│  │         Scoreboard                   │        │
│  │  ┌─────────────┐ ┌─────────────┐    │        │
│  │  │ ap_imp_in   │ │ ap_imp_out  │    │        │
│  │  │ (입력 포트)  │ │ (출력 포트)  │    │        │
│  │  └──────┬──────┘ └──────┬──────┘    │        │
│  │         │               │           │        │
│  │         ▼               ▼           │        │
│  │    ┌──────────────────────────┐     │        │
│  │    │   예측 큐 vs 실제 비교    │     │        │
│  │    └──────────────────────────┘     │        │
│  └──────────────────────────────────────┘        │
└─────────────────────────────────────────────────┘
```

**멀티포트 스코어보드의 핵심**: `uvm_analysis_imp`를 2개 사용하려면 매크로가 필요합니다.

```systemverilog
// ⭐ 매크로로 별명 포트 선언 — UVM 표준 방식
`uvm_analysis_imp_decl(_input)
`uvm_analysis_imp_decl(_output)

class counter_scoreboard_multi extends uvm_scoreboard;
  `uvm_component_utils(counter_scoreboard_multi)

  // ⭐ 2개의 analysis implementation port
  uvm_analysis_imp_input  #(counter_seq_item, counter_scoreboard_multi) ap_in;
  uvm_analysis_imp_output #(counter_seq_item, counter_scoreboard_multi) ap_out;

  // 예측 큐 — 입력 기반 예측값 저장
  logic [3:0] expected_queue[$];
  int match_count, error_count;

  function new(string name, uvm_component parent);
    super.new(name, parent);
  endfunction

  virtual function void build_phase(uvm_phase phase);
    super.build_phase(phase);
    ap_in  = new("ap_in",  this);
    ap_out = new("ap_out", this);
  endfunction

  // ⭐ 입력 포트: 입력 트랜잭션을 받아 예측값 저장
  //   실무에서는 입력 모니터가 자극(rst_n, enable)만 관찰하고,
  //   출력 모니터가 결과(count)를 관찰합니다.
  //   여기서는 단순화를 위해 item.count(현재 상태)를 참조합니다.
  virtual function void write_input(counter_seq_item item);
    logic [3:0] predicted;
    predicted = (!item.rst_n) ? 4'h0 :
                (item.enable) ? item.count + 1 : item.count;
    expected_queue.push_back(predicted);
    `uvm_info(get_type_name(),
      $sformatf("Predicted: %0d (queue size: %0d)",
                predicted, expected_queue.size()), UVM_HIGH)
  endfunction

  // ⭐ 출력 포트: 실제 출력과 예측값 비교
  virtual function void write_output(counter_seq_item item);
    logic [3:0] expected;

    if (expected_queue.size() == 0) begin
      `uvm_error(get_type_name(), "Unexpected output — no prediction in queue!")
      return;
    end

    expected = expected_queue.pop_front();

    if (expected !== item.count) begin
      `uvm_error(get_type_name(),
        $sformatf("MISMATCH! exp=%0d, act=%0d", expected, item.count))
      error_count++;
    end else
      match_count++;
  endfunction

  virtual function void report_phase(uvm_phase phase);
    `uvm_info(get_type_name(),
      $sformatf("Results: %0d matches, %0d errors", match_count, error_count),
      UVM_LOW)
    if (expected_queue.size() > 0)
      `uvm_warning(get_type_name(),
        $sformatf("%0d predictions left unchecked!", expected_queue.size()))
  endfunction
endclass
```

**핵심 포인트:**
- `uvm_analysis_imp_decl(_input)`: `write_input()` 메서드를 사용하는 포트 타입 생성
- `uvm_analysis_imp_decl(_output)`: `write_output()` 메서드를 사용하는 포트 타입 생성
- 예측 큐(`expected_queue`)로 입력 기반 예측과 출력 비교를 시간차로 처리

> **면접 포인트**: "멀티포트 스코어보드를 구현한 경험이 있나요?" — `uvm_analysis_imp_decl` 매크로로 접미사별 포트를 생성하고, `write_접미사()` 메서드로 각각 처리합니다. 실무에서 AXI, AHB 같은 버스 프로토콜 검증 시 입력/출력 포트 분리가 필수입니다.

### 8.3.4 report_phase()로 최종 결과 요약

예제 8-1에서 이미 `report_phase()`를 사용했습니다. 실무에서 자주 쓰는 패턴을 정리합니다:

```systemverilog
virtual function void report_phase(uvm_phase phase);
  uvm_report_server svr = uvm_report_server::get_server();

  `uvm_info(get_type_name(), "============ SCOREBOARD REPORT ============", UVM_LOW)
  `uvm_info(get_type_name(),
    $sformatf("  Transactions checked: %0d", match_count + error_count), UVM_LOW)
  `uvm_info(get_type_name(),
    $sformatf("  Pass: %0d / Fail: %0d", match_count, error_count), UVM_LOW)
  `uvm_info(get_type_name(), "============================================", UVM_LOW)

  // ⭐ 트랜잭션이 0개면 경고 — 연결 누락 가능성
  if (match_count + error_count == 0)
    `uvm_warning(get_type_name(),
      "No transactions received! Check monitor-scoreboard connection.")
endfunction
```

> **트러블슈팅**: `No transactions received!` 경고가 뜨면?
> 1. `env.connect_phase()`에서 `agent.mon.ap.connect(scoreboard.ap_imp)` 확인
> 2. 모니터가 `ap.write(item)`을 호출하는지 확인
> 3. Agent가 Active 모드인지 확인 (`is_active == UVM_ACTIVE`)

---

## 8.4 기능 커버리지 기초

> **이 절의 목표**: SystemVerilog `covergroup`을 사용해 기능 커버리지를 수집하고, 검증 완전성을 정량적으로 측정합니다.

### 8.4.1 코드 커버리지 vs 기능 커버리지

커버리지는 두 종류가 있습니다:

| 항목 | 코드 커버리지 | 기능 커버리지 |
|------|-------------|-------------|
| **무엇을** | RTL 코드 실행 여부 | **기능 시나리오** 검증 여부 |
| **누가** | 시뮬레이터 자동 수집 | **검증 엔지니어가 정의** |
| **예시** | "이 if문 실행됐나?" | "reset 후 enable 시나리오 테스트했나?" |
| **도구** | VCS: `-cm line+cond+...` | `covergroup` 문법 |
| **한계** | 코드가 실행됐다 ≠ 기능 검증됨 | 정의하지 않은 건 측정 불가 |

> **핵심**: 코드 커버리지 100%여도 버그가 있을 수 있습니다. 코드가 "실행"만 됐을 뿐 "올바른 결과"인지는 확인하지 않기 때문입니다. **기능 커버리지**는 "의미 있는 시나리오를 테스트했는가?"를 측정합니다.

### 8.4.2 covergroup, coverpoint, bins

`covergroup`은 **SystemVerilog 문법**입니다 (UVM 전용이 아님). UVM 테스트벤치에서 활용하는 방법을 배웁니다.

**기본 문법:**

```systemverilog
// covergroup 선언
covergroup counter_cg @(posedge clk);
  // ⭐ coverpoint: 관심 있는 변수
  cp_rst_n: coverpoint rst_n {
    bins active   = {0};    // 리셋 활성화
    bins inactive = {1};    // 리셋 비활성화
  }

  cp_enable: coverpoint enable {
    bins on  = {1};         // 카운터 활성화
    bins off = {0};         // 카운터 비활성화
  }

  cp_count: coverpoint count {
    bins zero     = {0};           // 0 값
    bins mid      = {[1:14]};      // 중간 값
    bins max      = {15};          // 최대 값 (오버플로우 직전)
  }
endgroup
```

**용어 정리:**

| 용어 | 뜻 | 비유 |
|------|-----|------|
| `covergroup` | 커버리지 그룹 | 시험 과목 |
| `coverpoint` | 관찰 대상 변수 | 시험 문제 |
| `bins` | 값 범위 구간 | 문제의 보기 (각각 맞춰야 100%) |

> **참고**: `bins`를 직접 정의하지 않으면 시뮬레이터가 **자동으로** bin을 생성합니다 (auto bins). 기본값은 `auto_bin_max = 64`개입니다. 자동 bin은 편리하지만, 의미 있는 구간을 직접 정의하는 것이 실무에서 권장됩니다.

### 8.4.3 cross coverage

`cross`는 두 coverpoint의 **조합**을 측정합니다.

```systemverilog
covergroup counter_cg @(posedge clk);
  cp_rst_n:  coverpoint rst_n;
  cp_enable: coverpoint enable;
  cp_count:  coverpoint count {
    bins zero = {0};
    bins mid  = {[1:14]};
    bins max  = {15};
  }

  // ⭐ cross: 조합 커버리지
  //    rst_n × enable = 4가지 조합 (00, 01, 10, 11)
  cx_rst_en: cross cp_rst_n, cp_enable;

  // ⭐ enable × count 조합
  //    enable이 1일 때 count가 0/mid/max 모두 나왔는가?
  cx_en_count: cross cp_enable, cp_count;
endgroup
```

**cross coverage가 중요한 이유:**
- `rst_n = 0` 테스트함 ✅
- `enable = 1` 테스트함 ✅
- 하지만 `rst_n = 0 && enable = 1` 조합은? → cross가 잡아냄

> **실무 이야기**: 팹리스에서 테이프아웃 전 기능 커버리지 목표는 보통 **95% 이상**입니다. cross coverage까지 95%를 달성해야 "검증 완료"로 판단합니다.

### 8.4.4 기본 커버리지 수집기 — 예제 8-2

커버리지 수집기도 `uvm_subscriber`로 구현합니다. 모니터의 analysis port에 연결되어 트랜잭션을 받을 때마다 covergroup을 샘플링합니다.

```systemverilog
// ===== 예제 8-2: 4비트 카운터 커버리지 수집기 =====
class counter_coverage extends uvm_subscriber #(counter_seq_item);
  `uvm_component_utils(counter_coverage)

  // ⭐ 커버리지 그룹 선언
  covergroup counter_cg;
    cp_rst_n: coverpoint item.rst_n {
      bins active   = {0};
      bins inactive = {1};
    }

    cp_enable: coverpoint item.enable {
      bins on  = {1};
      bins off = {0};
    }

    cp_count: coverpoint item.count {
      bins zero     = {0};
      bins low      = {[1:7]};
      bins high     = {[8:14]};
      bins max      = {15};
    }

    // cross coverage
    cx_rst_en:    cross cp_rst_n, cp_enable;
    cx_en_count:  cross cp_enable, cp_count;
  endgroup

  // 트랜잭션 저장용 — covergroup에서 참조
  counter_seq_item item;

  function new(string name, uvm_component parent);
    super.new(name, parent);
    counter_cg = new();    // ⭐ covergroup 인스턴스 생성
  endfunction

  // ⭐ write(): 트랜잭션 수신 시 커버리지 샘플링
  virtual function void write(counter_seq_item t);
    if (t == null) return;  // null 트랜잭션 방어
    item = t;
    counter_cg.sample();    // ⭐ 커버리지 수집!
    `uvm_info(get_type_name(),
      $sformatf("Sampled: rst_n=%0b, en=%0b, count=%0d",
                t.rst_n, t.enable, t.count), UVM_HIGH)
  endfunction

  // ⭐ report_phase: 커버리지 요약 출력
  virtual function void report_phase(uvm_phase phase);
    `uvm_info(get_type_name(), "===== Coverage Summary =====", UVM_LOW)
    `uvm_info(get_type_name(),
      $sformatf("  Overall: %.1f%%", counter_cg.get_coverage()), UVM_LOW)
    `uvm_info(get_type_name(),
      $sformatf("  rst_n : %.1f%%", counter_cg.cp_rst_n.get_coverage()), UVM_LOW)
    `uvm_info(get_type_name(),
      $sformatf("  enable: %.1f%%", counter_cg.cp_enable.get_coverage()), UVM_LOW)
    `uvm_info(get_type_name(),
      $sformatf("  count : %.1f%%", counter_cg.cp_count.get_coverage()), UVM_LOW)
    `uvm_info(get_type_name(),
      $sformatf("  cross(rst,en)   : %.1f%%",
                counter_cg.cx_rst_en.get_coverage()), UVM_LOW)
    `uvm_info(get_type_name(),
      $sformatf("  cross(en,count) : %.1f%%",
                counter_cg.cx_en_count.get_coverage()), UVM_LOW)
  endfunction
endclass
```

**실행 결과 예시:**

```
UVM_INFO  counter_coverage: ===== Coverage Summary =====
UVM_INFO  counter_coverage:   Overall: 78.5%
UVM_INFO  counter_coverage:   rst_n : 100.0%
UVM_INFO  counter_coverage:   enable: 100.0%
UVM_INFO  counter_coverage:   count : 75.0%      ← max(15) 미달!
UVM_INFO  counter_coverage:   cross(rst,en)   : 100.0%
UVM_INFO  counter_coverage:   cross(en,count) : 62.5%   ← 조합 부족!
```

> **분석**: count의 `max` bin(15)이 hit되지 않았습니다. 오버플로우까지 카운터를 돌리는 시퀀스가 필요합니다. → Ch.9에서 시나리오별 시퀀스 작성을 배웁니다.

---

## 8.5 커버리지 기반 검증 (CDV)

> **이 절의 목표**: Coverage-Driven Verification 워크플로우를 이해하고, 커버리지를 체계적으로 관리하는 방법을 배웁니다.

### 8.5.1 CDV 워크플로우

```
┌──────────────────────────────────────────────┐
│         CDV (Coverage-Driven Verification)    │
│                                              │
│   ┌────────────┐                             │
│   │ 1. 목표    │  기능 커버리지 항목 정의     │
│   │    설정    │  목표: 95% 이상              │
│   └─────┬──────┘                             │
│         ↓                                    │
│   ┌────────────┐                             │
│   │ 2. 테스트  │  시퀀스 작성 & 실행          │
│   │    실행    │                              │
│   └─────┬──────┘                             │
│         ↓                                    │
│   ┌────────────┐                             │
│   │ 3. 커버리지│  어떤 bin이 미달인지 분석     │
│   │    분석    │                              │
│   └─────┬──────┘                             │
│         ↓                                    │
│   ┌────────────┐     ┌───────────────┐       │
│   │ 4. 목표    │ No  │ 추가 시나리오 │       │
│   │   달성?    ├────►│ 작성 후 2로   │       │
│   └─────┬──────┘     └───────────────┘       │
│         │ Yes                                │
│         ↓                                    │
│   ┌────────────┐                             │
│   │ 5. 검증    │                             │
│   │    완료!   │                             │
│   └────────────┘                             │
└──────────────────────────────────────────────┘
```

**단계별 설명:**

| 단계 | 활동 | 산출물 |
|------|------|--------|
| 1. 목표 설정 | DUT 기능 명세에서 커버리지 항목 추출 | 커버리지 계획서 |
| 2. 테스트 실행 | 시퀀스로 다양한 시나리오 실행 | 시뮬레이션 로그 |
| 3. 커버리지 분석 | 미달 bin 확인, 원인 분석 | 커버리지 리포트 |
| 4. 목표 확인 | 95% 이상 달성했는지 확인 | 합격/추가 작업 |
| 5. 완료 | 사인오프, 테이프아웃 진행 | 검증 완료 보고서 |

### 8.5.2 커버리지 리포트 읽기

시뮬레이션 후 커버리지 리포트를 읽는 방법입니다:

```
=== Coverage Report ===
covergroup: counter_cg

  coverpoint: cp_rst_n          Coverage: 100.0%
    bins active   = {0}         hit: 5     ✅
    bins inactive = {1}         hit: 25    ✅

  coverpoint: cp_enable         Coverage: 100.0%
    bins on  = {1}              hit: 20    ✅
    bins off = {0}              hit: 10    ✅

  coverpoint: cp_count          Coverage: 75.0%
    bins zero = {0}             hit: 5     ✅
    bins low  = {[1:7]}         hit: 12    ✅
    bins high = {[8:14]}        hit: 8     ✅
    bins max  = {15}            hit: 0     ❌ ← 미달!

  cross: cx_en_count            Coverage: 62.5%
    <enable=1, count=max>       hit: 0     ❌ ← 미달!
    <enable=0, count=max>       hit: 0     ❌ ← 미달!
```

**읽는 법:**
1. 각 bin의 `hit` 수를 확인 — 0이면 해당 시나리오 미테스트
2. **cross coverage** 주목 — 개별 100%여도 조합이 부족할 수 있음
3. 미달 항목에 맞는 **타겟 시퀀스** 작성 (Ch.9에서 상세히)

### 8.5.3 커버리지 100%의 함정

> **중요**: 기능 커버리지 100% ≠ 버그 없음

| 함정 | 설명 |
|------|------|
| **정의 누락** | 정의하지 않은 시나리오는 측정 불가 |
| **스코어보드 없는 커버리지** | 실행만 하고 결과를 확인하지 않으면 무의미 |
| **과도한 bin 생략** | `illegal_bins`, `ignore_bins`로 너무 많이 제외 |

> **실무 규칙**: 커버리지는 **스코어보드와 함께** 사용해야 의미가 있습니다. "실행했다"와 "검증했다"는 다릅니다. 스코어보드가 PASS를 보고한 상태에서 커버리지 95%가 진짜 검증 완료입니다.

---

## 8.6 종합: 자동 검증 테스트벤치

> **이 절의 목표**: 스코어보드와 커버리지를 Environment에 통합하여 완전한 자동 검증 테스트벤치를 완성합니다.

### 8.6.1 전체 구조

```
┌───────────────────────────────────────────────────────┐
│                    counter_test                        │
│                                                       │
│  ┌─────────────────────────────────────────────────┐  │
│  │                counter_env                       │  │
│  │                                                  │  │
│  │  ┌────────────────────┐  ┌───────────────────┐  │  │
│  │  │   counter_agent    │  │ counter_scoreboard│  │  │
│  │  │                    │  │                   │  │  │
│  │  │ ┌──────────────┐  │  │  Reference Model  │  │  │
│  │  │ │  Sequencer   │  │  │  + write()        │  │  │
│  │  │ └──────┬───────┘  │  │  + report_phase() │  │  │
│  │  │        ↓          │  └────────▲──────────┘  │  │
│  │  │ ┌──────────────┐  │           │             │  │
│  │  │ │   Driver     │  │    ┌──────┴──────┐      │  │
│  │  │ └──────────────┘  │    │  analysis   │      │  │
│  │  │                    │    │  _port      │      │  │
│  │  │ ┌──────────────┐  │    └──────┬──────┘      │  │
│  │  │ │   Monitor  ──┼──┼───────────┘             │  │
│  │  │ └──────────────┘  │           │             │  │
│  │  └────────────────────┘  ┌───────▼───────────┐ │  │
│  │                          │ counter_coverage   │ │  │
│  │                          │                    │ │  │
│  │                          │  covergroup        │ │  │
│  │                          │  + sample()        │ │  │
│  │                          │  + report_phase()  │ │  │
│  │                          └────────────────────┘ │  │
│  └─────────────────────────────────────────────────┘  │
│                                                       │
│     ┌─────────┐                                       │
│     │   DUT   │  (4비트 카운터)                        │
│     └─────────┘                                       │
└───────────────────────────────────────────────────────┘
```

### 8.6.2 완성 코드 — 예제 8-3

이전 챕터에서 만든 코드에 스코어보드와 커버리지를 추가합니다. **변경 부분만** 표시합니다.

**① counter_seq_item (Ch.6에서 작성, 변경 없음)**

```systemverilog
class counter_seq_item extends uvm_sequence_item;
  `uvm_object_utils(counter_seq_item)

  rand bit       rst_n;
  rand bit       enable;
  logic [3:0]    count;     // DUT 출력 (관찰용)

  constraint c_default {
    rst_n dist {0 := 10, 1 := 90};
    enable dist {0 := 20, 1 := 80};
  }

  function new(string name = "counter_seq_item");
    super.new(name);
  endfunction

  function string convert2string();
    return $sformatf("rst_n=%0b, en=%0b, count=%0d", rst_n, enable, count);
  endfunction
endclass
```

**② counter_env — ⭐ 스코어보드 & 커버리지 추가**

```systemverilog
class counter_env extends uvm_env;
  `uvm_component_utils(counter_env)

  counter_agent      agent;
  counter_scoreboard scoreboard;    // ⭐ 새로 추가
  counter_coverage   coverage_col;  // ⭐ 새로 추가

  function new(string name, uvm_component parent);
    super.new(name, parent);
  endfunction

  virtual function void build_phase(uvm_phase phase);
    super.build_phase(phase);
    agent        = counter_agent::type_id::create("agent", this);
    scoreboard   = counter_scoreboard::type_id::create("scoreboard", this);
    coverage_col = counter_coverage::type_id::create("coverage_col", this);
  endfunction

  // ⭐ connect_phase: 모니터 → 스코어보드 & 커버리지 연결
  virtual function void connect_phase(uvm_phase phase);
    super.connect_phase(phase);
    // 모니터의 analysis port를 두 곳에 연결 (1:N 브로드캐스트!)
    agent.mon.ap.connect(scoreboard.ap_imp);            // → 스코어보드
    agent.mon.ap.connect(coverage_col.analysis_export);  // → 커버리지
  endfunction
endclass
```

> **핵심**: `connect_phase()`에서 모니터의 `ap`를 스코어보드와 커버리지 **둘 다**에 연결합니다. Ch.7에서 배운 analysis port의 1:N 브로드캐스트가 여기서 빛을 발합니다!

**③ counter_test — run_phase 시퀀스 실행**

```systemverilog
class counter_base_test extends uvm_test;
  `uvm_component_utils(counter_base_test)

  counter_env env;

  function new(string name, uvm_component parent);
    super.new(name, parent);
  endfunction

  virtual function void build_phase(uvm_phase phase);
    super.build_phase(phase);
    env = counter_env::type_id::create("env", this);
  endfunction

  virtual task run_phase(uvm_phase phase);
    counter_reset_seq  reset_seq;
    counter_count_seq  count_seq;

    phase.raise_objection(this);

    // 리셋 시퀀스
    reset_seq = counter_reset_seq::type_id::create("reset_seq");
    reset_seq.start(env.agent.sqr);

    // 카운트 시퀀스
    count_seq = counter_count_seq::type_id::create("count_seq");
    count_seq.num_transactions = 50;
    count_seq.start(env.agent.sqr);

    phase.drop_objection(this);
  endtask
endclass
```

**④ 시퀀스들 — 다양한 시나리오**

```systemverilog
// 리셋 시퀀스 — 초기화 확인
class counter_reset_seq extends uvm_sequence #(counter_seq_item);
  `uvm_object_utils(counter_reset_seq)

  function new(string name = "counter_reset_seq");
    super.new(name);
  endfunction

  virtual task body();
    counter_seq_item item;

    // 리셋 활성화 (3 클럭)
    repeat (3) begin
      item = counter_seq_item::type_id::create("item");
      start_item(item);
      item.rst_n  = 0;
      item.enable = 0;
      finish_item(item);
    end

    // 리셋 해제
    item = counter_seq_item::type_id::create("item");
    start_item(item);
    item.rst_n  = 1;
    item.enable = 0;
    finish_item(item);
  endtask
endclass

// 카운트 시퀀스 — 랜덤 자극
class counter_count_seq extends uvm_sequence #(counter_seq_item);
  `uvm_object_utils(counter_count_seq)

  int num_transactions = 20;

  function new(string name = "counter_count_seq");
    super.new(name);
  endfunction

  virtual task body();
    counter_seq_item item;

    repeat (num_transactions) begin
      item = counter_seq_item::type_id::create("item");
      start_item(item);
      if (!item.randomize())
        `uvm_fatal(get_type_name(), "Randomization failed!")
      item.rst_n = 1;    // 리셋 해제 유지
      finish_item(item);
    end
  endtask
endclass

// 오버플로우 시퀀스 — count=15 → 0 전이 확인
class counter_overflow_seq extends uvm_sequence #(counter_seq_item);
  `uvm_object_utils(counter_overflow_seq)

  function new(string name = "counter_overflow_seq");
    super.new(name);
  endfunction

  virtual task body();
    counter_seq_item item;

    // 연속 enable로 16+α 클럭 구동 → 오버플로우 발생
    repeat (20) begin
      item = counter_seq_item::type_id::create("item");
      start_item(item);
      item.rst_n  = 1;
      item.enable = 1;    // 계속 카운트
      finish_item(item);
    end
  endtask
endclass
```

**⑤ top 모듈 (간략)**

```systemverilog
module top;
  import uvm_pkg::*;
  `include "uvm_macros.svh"

  // 시그널 및 인터페이스
  logic clk;
  counter_if cif(clk);

  // DUT 인스턴스
  counter_4bit dut (
    .clk    (clk),
    .rst_n  (cif.rst_n),
    .enable (cif.enable),
    .count  (cif.count)
  );

  // 클럭 생성
  initial clk = 0;
  always #5 clk = ~clk;

  // UVM 설정 및 시작
  initial begin
    uvm_config_db#(virtual counter_if)::set(null, "*", "vif", cif);
    run_test("counter_base_test");
  end

  initial begin
    $dumpfile("counter_scoreboard.vcd");
    $dumpvars(0, top);
  end
endmodule
```

### 8.6.3 실행 결과

```
UVM_INFO  @ 0: reporter [RNTST] Running test counter_base_test...

--- Reset Phase ---
UVM_INFO  counter_scoreboard: Initial state: count=0
UVM_INFO  counter_scoreboard: MATCH: count=0 (rst_n=0, en=0)
UVM_INFO  counter_scoreboard: MATCH: count=0 (rst_n=0, en=0)
UVM_INFO  counter_scoreboard: MATCH: count=0 (rst_n=1, en=0)

--- Count Phase (50 transactions) ---
UVM_INFO  counter_scoreboard: MATCH: count=1 (rst_n=1, en=1)
UVM_INFO  counter_scoreboard: MATCH: count=2 (rst_n=1, en=1)
...
UVM_INFO  counter_scoreboard: MATCH: count=15 (rst_n=1, en=1)
UVM_INFO  counter_scoreboard: MATCH: count=0 (rst_n=1, en=1)  ← 오버플로우!
...

--- Report Phase ---
UVM_INFO  counter_scoreboard: ===== Scoreboard Summary =====
UVM_INFO  counter_scoreboard:   Total transactions: 53
UVM_INFO  counter_scoreboard:   Matches : 53
UVM_INFO  counter_scoreboard:   Errors  : 0
UVM_INFO  counter_scoreboard: TEST PASSED — all transactions matched!

UVM_INFO  counter_coverage: ===== Coverage Summary =====
UVM_INFO  counter_coverage:   Overall: 87.5%
UVM_INFO  counter_coverage:   rst_n : 100.0%
UVM_INFO  counter_coverage:   enable: 100.0%
UVM_INFO  counter_coverage:   count : 100.0%
UVM_INFO  counter_coverage:   cross(rst,en)   : 75.0%     ← rst_n=0,en=1 미달
UVM_INFO  counter_coverage:   cross(en,count)  : 75.0%    ← en=0,count=max 미달

--- UVM Report Summary ---
** Report counts by severity
UVM_INFO :  62
UVM_WARNING :   0
UVM_ERROR :   0
UVM_FATAL :   0
** Test PASSED **
```

**결과 분석:**
- **스코어보드**: 53개 트랜잭션 전부 PASS → DUT 동작 정확
- **커버리지**: 87.5% → 일부 조합 미달
  - `rst_n=0, enable=1` 조합 — 리셋 중 enable 시나리오 미테스트
  - `enable=0, count=15` 조합 — 최대값에서 정지 시나리오 미테스트
- **다음 단계**: Ch.9에서 타겟 시퀀스를 추가해 95% 이상 달성

### 8.6.4 Ch.5 → Ch.8 진화 정리

| 항목 | Ch.5 | Ch.6 | Ch.7 | **Ch.8** |
|------|------|------|------|----------|
| 시나리오 | 하드코딩 | 시퀀스 분리 | 시퀀스 (동일) | 시퀀스 (동일) |
| 타이밍 | `#1` 해킹 | `#1` 해킹 | clocking block | clocking block |
| 접근 제어 | 없음 | 없음 | modport | modport |
| 데이터 전달 | 직접 신호 | seq_item_port | seq_item_port | seq_item_port |
| 모니터 출력 | `uvm_info`만 | `uvm_info`만 | analysis port | analysis port |
| **검증** | **눈으로 파형** | **눈으로 파형** | **눈으로 파형** | **⭐ 스코어보드 자동** |
| **커버리지** | **없음** | **없음** | **없음** | **⭐ 기능 커버리지** |

> **성취감 포인트**: 이제 만든 테스트벤치는 팹리스에서 실제 사용하는 것과 **동일한 수준**입니다! 시나리오 자동화(시퀀스) + 타이밍 안정(clocking block) + 자동 검증(스코어보드) + 완전성 측정(커버리지)를 모두 갖췄습니다.

---

## 8.7 체크포인트

### 셀프 체크

**1. 스코어보드의 역할은?** (8.1-8.2)
<details>
<summary>정답 확인</summary>
Reference Model로 예상 출력을 계산하고, 모니터가 관찰한 실제 DUT 출력과 자동으로 비교합니다. 불일치 시 `uvm_error`로 보고하고, `report_phase()`에서 최종 결과를 요약합니다.
</details>

**2. uvm_analysis_imp와 uvm_subscriber의 차이는?** (8.2-8.3)
<details>
<summary>정답 확인</summary>
`uvm_analysis_imp`는 analysis port 수신 포트를 직접 선언합니다. 다중 포트가 필요할 때 사용합니다. `uvm_subscriber`는 analysis port가 내장되어 있어 `write()`만 구현하면 됩니다. 포트 1개로 충분한 경우 `uvm_subscriber`가 간편합니다.
</details>

**3. 코드 커버리지와 기능 커버리지의 차이는?** (8.4)
<details>
<summary>정답 확인</summary>
코드 커버리지는 시뮬레이터가 자동으로 RTL 코드 실행 여부를 측정합니다 (line, branch, condition 등). 기능 커버리지는 검증 엔지니어가 `covergroup`으로 정의한 기능 시나리오의 검증 여부를 측정합니다. 코드 커버리지 100%여도 기능 검증이 부족할 수 있습니다.
</details>

**4. cross coverage가 필요한 이유는?** (8.4)
<details>
<summary>정답 확인</summary>
개별 coverpoint가 100%여도 변수 간 조합이 테스트되지 않을 수 있습니다. 예: `rst_n=0` 테스트 완료, `enable=1` 테스트 완료이지만 `rst_n=0 && enable=1` 조합은 미테스트. cross coverage가 이런 빈틈을 잡아냅니다.
</details>

**5. connect_phase()에서 모니터를 스코어보드와 커버리지에 동시 연결하는 방법은?** (8.6)
<details>
<summary>정답 확인</summary>
analysis port의 1:N 브로드캐스트를 활용합니다. `agent.mon.ap.connect(scoreboard.ap_imp)` 와 `agent.mon.ap.connect(coverage_col.analysis_export)`를 둘 다 호출하면, 모니터가 `write()`할 때 스코어보드와 커버리지 수집기 **모두**의 `write()`가 자동 호출됩니다.
</details>

**6. 스코어보드의 report_phase()에서 트랜잭션 수가 0이면?** (8.3)
<details>
<summary>정답 확인</summary>
모니터-스코어보드 연결이 누락되었거나, 모니터가 `ap.write()`를 호출하지 않거나, Agent가 Passive 모드(모니터만 존재)인데 입력이 없는 경우입니다. `connect_phase()` 연결과 모니터 구현을 확인해야 합니다.
</details>

### 연습문제

**연습 8-1 (기본)**: 예제 8-1의 스코어보드에 **타임스탬프 로깅**을 추가하세요. 각 비교 결과에 `$time` 값을 포함하여 언제 에러가 발생했는지 추적할 수 있도록 합니다.

<details>
<summary>힌트</summary>
`$sformatf`의 포맷 문자열에 `$time`을 추가합니다: `$sformatf("[%0t] MISMATCH! ...", $time, ...)`
</details>

**연습 8-2 (중급)**: 예제 8-2의 커버리지 수집기에 **transition coverage**를 추가하세요. `count` 값이 `15 → 0`으로 전이되는 오버플로우 이벤트를 추적합니다.

<details>
<summary>힌트</summary>
coverpoint에 `bins overflow = (15 => 0);` transition bin을 추가합니다. 이것은 순차적 값 전이를 추적합니다.
</details>

**연습 8-3 (도전)**: 멀티포트 스코어보드(8.3.3)를 실제로 구현하세요. 입력 모니터와 출력 모니터를 분리하고, 예측 큐를 사용하여 비동기적으로 비교합니다. `check_phase()`에서 큐에 남은 미비교 항목을 에러로 보고합니다.

<details>
<summary>힌트</summary>
`uvm_analysis_imp_decl(_input)`, `uvm_analysis_imp_decl(_output)` 매크로를 사용합니다. `check_phase()`에서 `expected_queue.size() > 0`이면 `uvm_error`를 보고합니다.
</details>

### 다음 장 미리보기

Chapter 9에서는 **테스트 시나리오**를 체계적으로 작성합니다. 이번 챕터에서 커버리지가 87.5%에 머물렀던 이유는 시나리오가 부족했기 때문입니다. 타겟 시퀀스, 랜덤 시퀀스, 에러 주입 시퀀스를 조합하여 커버리지 95% 이상을 달성하는 방법을 배웁니다.
